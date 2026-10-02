"""#237 P1: the live-system guard. Nothing here touches the live system: every
forbidden action is refused by the audit hook *before* it happens."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from julia_core.testing import live_guard
from julia_core.testing.live_guard import Guard, LiveSystemAccessError

HOME = Path.home()


# ── the hook is really installed for this session (sentinel) ─────────────

def test_guard_is_installed_in_this_session():
    assert live_guard.is_installed(), "tests/conftest.py must install the live guard"


# ── real operations are refused by the installed hook ────────────────────

def test_connecting_to_the_production_port_is_refused():
    with pytest.raises(LiveSystemAccessError):
        socket.create_connection(("127.0.0.1", 18089), timeout=1)
    with pytest.raises(LiveSystemAccessError):
        socket.create_connection(("localhost", 18089), timeout=1)


def test_binding_the_production_port_is_refused_but_a_free_port_is_not():
    sock = socket.socket()
    try:
        with pytest.raises(LiveSystemAccessError):
            sock.bind(("127.0.0.1", 18089))
    finally:
        sock.close()
    with socket.socket() as free:
        free.bind(("127.0.0.1", 0))           # port 0 is the sanctioned way


@pytest.mark.parametrize("argv", [
    ["launchctl", "list"],
    ["/bin/launchctl", "kickstart", "-k", "gui/501/com.julia.brain.18089"],
    ["lsof", "-ti", ":18089"],
    ["pkill", "-f", "voice_api"],
    ["killall", "python3"],
    ["kill", "-9", "123"],
    ["bash", "-c", "echo hi > /dev/null; curl http://127.0.0.1:18089/health"],
])
def test_dangerous_subprocess_arguments_are_refused(argv):
    with pytest.raises(LiveSystemAccessError):
        subprocess.run(argv, capture_output=True)


def test_os_system_with_a_dangerous_command_is_refused():
    with pytest.raises(LiveSystemAccessError):
        os.system("launchctl list")


def test_killing_a_process_we_did_not_start_is_refused_but_liveness_probes_pass():
    with pytest.raises(LiveSystemAccessError):
        os.kill(1, 15)
    with pytest.raises(LiveSystemAccessError):
        os.killpg(1, 15)
    Guard().evaluate("os.kill", (1, 0))        # signal 0 is only a liveness probe (pure check)
    os.kill(os.getpid(), 0)


def test_a_child_started_in_this_session_may_be_killed():
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
    try:
        assert proc.pid in live_guard.registered_pids()
    finally:
        os.killpg(proc.pid, 15)                # its own process group
        proc.wait(timeout=10)


def test_a_grandchild_group_of_ours_may_be_cleaned_up_but_a_foreign_group_may_not():
    """Children of children (not registered by Popen tracking) are still ours."""
    code = (
        "import subprocess, sys, time\n"
        "g = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)\n"
        "print(g.pid, flush=True)\n"
        "time.sleep(60)\n"
    )
    parent = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
    try:
        grandchild = int(parent.stdout.readline())
        assert grandchild not in live_guard.registered_pids()      # not registered by this process
        Guard().evaluate("os.killpg", (grandchild, 15))            # but it descends from us -> allowed
        os.killpg(grandchild, 15)
        with pytest.raises(LiveSystemAccessError):
            Guard().evaluate("os.killpg", (1, 15))                 # a foreign group is refused
        with pytest.raises(LiveSystemAccessError):
            Guard().evaluate("os.kill", (os.getppid(), 15))        # our own parent is not our descendant
    finally:
        parent.kill()
        parent.wait(timeout=10)


@pytest.mark.parametrize("target", [
    "~/.julia_ops/should_never_exist_probe",
    "~/julia_ai_assistant/memory/conversations/should_never_exist_probe",
    "~/julia_ai_assistant/data/should_never_exist_probe",
    "~/julia_release/should_never_exist_probe",
])
def test_writing_into_formal_paths_is_refused_and_nothing_is_created(target):
    path = Path(target).expanduser()
    with pytest.raises(LiveSystemAccessError):
        open(path, "w")
    with pytest.raises(LiveSystemAccessError):
        path.write_text("x")
    with pytest.raises(LiveSystemAccessError):
        os.mkdir(str(path) + "_dir")
    assert not path.exists() and not Path(str(path) + "_dir").exists()


def test_reading_formal_paths_and_writing_tmp_are_allowed(tmp_path):
    (tmp_path / "ok.txt").write_text("fine")
    assert (tmp_path / "ok.txt").read_text() == "fine"
    start_brain = HOME / ".julia_ops" / "bin" / "start-brain-18089"
    if start_brain.exists():
        start_brain.read_bytes()               # reads are not blocked


# ── pure policy checks (no real side effects) ───────────────────────────

def test_policy_evaluate_covers_rename_remove_rmtree_and_copy():
    guard = Guard()
    forbidden = str(HOME / ".julia_ops" / "x")
    for event, args in (
        ("os.rename", (forbidden, "/tmp/y", -1, -1)),
        ("os.rename", ("/tmp/y", forbidden, -1, -1)),
        ("os.remove", (forbidden, -1)),
        ("os.rmdir", (forbidden, -1)),
        ("shutil.rmtree", (forbidden, None, -1)),
        ("shutil.copyfile", ("/tmp/a", forbidden)),
    ):
        with pytest.raises(LiveSystemAccessError):
            guard.evaluate(event, args)
    guard.evaluate("os.remove", ("/tmp/some_test_file", -1))


def test_symlink_or_dotdot_cannot_smuggle_a_write_into_a_formal_path(tmp_path):
    guard = Guard()
    link = tmp_path / "link"
    link.symlink_to(HOME / ".julia_ops")
    with pytest.raises(LiveSystemAccessError):
        guard.evaluate("open", (str(link / "x"), "w", os.O_WRONLY | os.O_CREAT))
    with pytest.raises(LiveSystemAccessError):
        dotdot = str(tmp_path) + "/" + "../" * 40 + str(HOME).lstrip("/") + "/.julia_ops/x"
        guard.evaluate("open", (dotdot, "w", os.O_WRONLY))


def test_ipv6_and_hostname_forms_of_the_production_port_are_refused():
    guard = Guard()
    guard.evaluate("socket.connect", (object(), ("127.0.0.1", 18090)))
    for addr in (("127.0.0.1", 18089), ("::1", 18089, 0, 0), ("localhost", 18089), ("0.0.0.0", 18089)):
        with pytest.raises(LiveSystemAccessError):
            guard.evaluate("socket.connect", (object(), addr))
        with pytest.raises(LiveSystemAccessError):
            guard.evaluate("socket.bind", (object(), addr))


def test_extra_forbidden_config_can_only_append(tmp_path):
    base = Guard()
    cfg = tmp_path / "live_guard.json"
    cfg.write_text(json.dumps({"forbidden_write_roots": ["/opt/prod_data"], "forbidden_ports": [19999],
                               "allow_write_roots": [str(HOME / ".julia_ops")], "forbidden_ports_remove": [18089]}))
    guard = Guard.from_config(cfg)
    assert set(base.forbidden_ports) <= set(guard.forbidden_ports) and 19999 in guard.forbidden_ports
    with pytest.raises(LiveSystemAccessError):      # built-in roots stay forbidden despite "allow"
        guard.evaluate("open", (str(HOME / ".julia_ops" / "x"), "w", os.O_WRONLY))
    with pytest.raises(LiveSystemAccessError):      # appended root is enforced
        guard.evaluate("open", ("/opt/prod_data/x", "w", os.O_WRONLY))
    with pytest.raises(LiveSystemAccessError):      # 18089 cannot be removed
        guard.evaluate("socket.connect", (object(), ("127.0.0.1", 18089)))


def test_unreadable_or_malformed_config_fails_closed(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(live_guard.GuardConfigError):
        Guard.from_config(bad)
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"forbidden_write_roots": "not-a-list"}))
    with pytest.raises(live_guard.GuardConfigError):
        Guard.from_config(wrong)
    assert Guard.from_config(tmp_path / "absent.json").forbidden_ports        # absent = built-ins only


# ── static scan: no stray production literals in tests ─────────────────

def test_no_test_file_mentions_the_production_port_or_launchd_outside_the_allowlist():
    root = Path(__file__).resolve().parents[1]
    allow = {"guard/test_live_guard.py"}
    offenders = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root).as_posix()
        if rel in allow or "__pycache__" in rel:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "18089" in text or "launchctl" in text or "lsof -ti" in text:
            offenders.append(rel)
    assert offenders == [], f"live-system literals in tests: {offenders}"
