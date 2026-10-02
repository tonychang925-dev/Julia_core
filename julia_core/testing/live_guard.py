"""#237 P1: refuse test access to the live (production) system.

An audit hook (``sys.addaudithook``) checks, *before* the action happens:

* ``socket.connect`` / ``socket.bind`` to a forbidden port (18089 = production brain);
* ``subprocess.Popen`` / ``os.system`` / ``os.exec*`` whose arguments mention
  ``launchctl``, ``lsof``, ``kill``/``pkill``/``killall`` or a forbidden port;
* ``os.kill`` / ``os.killpg`` of a process that was not started by this session
  (signal 0, a liveness probe, is allowed);
* writes, renames, removals and directory changes under the formal paths.

Reads are never blocked. The hook cannot be uninstalled and raises
``LiveSystemAccessError`` (a ``RuntimeError``), so the action does not happen.

Fail closed: ``install()`` raises if the guard cannot be set up; the test
conftest turns that into ``pytest.exit``. Extra forbidden paths/ports may be
*appended* through ``~/.julia_ops/live_guard.json``; a built-in entry can never be
removed, and a malformed config is an error, not a silent default.

Known limit (documented, covered elsewhere): grandchild processes started by a
child are not seen by this hook. They are covered by the static scan in
``tests/guard`` and by the regression canary script.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

PRODUCTION_PORTS: tuple[int, ...] = (18089,)

_HOME = Path.home()
BUILTIN_FORBIDDEN_WRITE_ROOTS: tuple[Path, ...] = (
    _HOME / ".julia_ops",
    _HOME / "julia_ai_assistant",
    _HOME / "julia_release",
    _HOME / "Library" / "LaunchAgents",
)

DEFAULT_CONFIG_PATH = Path("~/.julia_ops/live_guard.json")
_DANGEROUS_PROGRAMS = {"launchctl", "lsof", "kill", "pkill", "killall"}
_DANGEROUS_SHELL = re.compile(r"(?<![\w-])(?:launchctl|lsof|kill|pkill|killall)(?![\w-])")
_LOOPBACK_NAMES = {"", "localhost", "127.0.0.1", "::1", "0.0.0.0", "::"}

_WRITE_FLAGS = (
    os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
)

# audit event -> indexes of path arguments that are modified
_PATH_WRITE_EVENTS: dict[str, tuple[int, ...]] = {
    "os.rename": (0, 1),
    "os.remove": (0,),
    "os.rmdir": (0,),
    "os.mkdir": (0,),
    "os.truncate": (0,),
    "os.symlink": (1,),
    "os.link": (0, 1),
    "os.chmod": (0,),
    "os.chown": (0,),
    "os.utime": (0,),
    "shutil.rmtree": (0,),
    "shutil.copyfile": (1,),
    "shutil.copymode": (1,),
    "shutil.copystat": (1,),
    "shutil.move": (0, 1),
    "shutil.chown": (0,),
}


class LiveSystemAccessError(RuntimeError):
    """A test tried to touch the live system."""


class GuardConfigError(RuntimeError):
    """The guard configuration is unreadable or malformed (fail closed)."""


def _as_path_str(value: Any) -> str | None:
    if isinstance(value, bytes):
        try:
            value = os.fsdecode(value)
        except Exception:
            return None
    if isinstance(value, os.PathLike):
        value = os.fspath(value)
        if isinstance(value, bytes):
            value = os.fsdecode(value)
    return value if isinstance(value, str) else None


def _resolve(path: str) -> str:
    # realpath follows symlinks (a link into a formal path must not smuggle writes)
    return os.path.realpath(os.path.abspath(os.path.expanduser(path)))


class Guard:
    def __init__(
        self,
        extra_ports: Iterable[int] = (),
        extra_write_roots: Iterable[Path | str] = (),
    ) -> None:
        self.forbidden_ports: frozenset[int] = frozenset(PRODUCTION_PORTS) | frozenset(int(p) for p in extra_ports)
        roots = list(BUILTIN_FORBIDDEN_WRITE_ROOTS) + [Path(r) for r in extra_write_roots]
        # compare both the literal and the resolved form of every root
        resolved = {_resolve(str(r)) for r in roots} | {os.path.abspath(str(r)) for r in roots}
        self.forbidden_write_roots: tuple[str, ...] = tuple(sorted(resolved))
        self._pids: set[int] = set()

    # ── configuration (append-only) ──────────────────────────────────────
    @classmethod
    def from_config(cls, path: str | os.PathLike | None = None) -> "Guard":
        config_path = Path(path if path is not None else DEFAULT_CONFIG_PATH).expanduser()
        if not config_path.exists():
            return cls()
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise GuardConfigError(f"unreadable guard config {config_path}: {exc}") from exc
        if not isinstance(data, dict):
            raise GuardConfigError("guard config must be a JSON object")
        ports = data.get("forbidden_ports", [])
        roots = data.get("forbidden_write_roots", [])
        if not isinstance(ports, list) or not all(isinstance(p, int) and not isinstance(p, bool) for p in ports):
            raise GuardConfigError("forbidden_ports must be a list of integers")
        if not isinstance(roots, list) or not all(isinstance(r, str) and r.strip() for r in roots):
            raise GuardConfigError("forbidden_write_roots must be a list of non-empty strings")
        # any other key (allow_*, *_remove, ...) is ignored: configuration can only append
        return cls(extra_ports=ports, extra_write_roots=roots)

    # ── child tracking ───────────────────────────────────────────────────
    def register_pid(self, pid: int) -> None:
        self._pids.add(int(pid))

    def registered_pids(self) -> frozenset[int]:
        return frozenset(self._pids)

    # ── policy ───────────────────────────────────────────────────────────
    def evaluate(self, event: str, args: tuple) -> None:
        """Raise ``LiveSystemAccessError`` if the audit event is forbidden."""
        if event in ("socket.connect", "socket.bind"):
            self._check_address(event, args[1] if len(args) > 1 else None)
        elif event == "subprocess.Popen":
            self._check_command(event, args[0], args[1] if len(args) > 1 else None)
        elif event in ("os.system", "os.exec", "os.posix_spawn", "os.spawn"):
            self._check_command(event, args[0] if args else None, args[1] if len(args) > 1 else None)
        elif event in ("os.kill", "os.killpg"):
            self._check_kill(event, args)
        elif event == "open":
            self._check_open(args)
        elif event in _PATH_WRITE_EVENTS:
            for index in _PATH_WRITE_EVENTS[event]:
                if len(args) > index:
                    self._check_write_path(event, args[index])

    def _check_address(self, event: str, address: Any) -> None:
        if not isinstance(address, tuple) or len(address) < 2:
            return
        host, port = address[0], address[1]
        if isinstance(port, int) and port in self.forbidden_ports:
            if isinstance(host, bytes):
                host = host.decode(errors="ignore")
            if not isinstance(host, str) or host in _LOOPBACK_NAMES or host.startswith("127."):
                raise LiveSystemAccessError(f"{event} to production port {port} is forbidden in tests")

    def _check_command(self, event: str, executable: Any, argv: Any) -> None:
        tokens: list[str] = []
        for value in (executable, argv):
            if isinstance(value, (list, tuple)):
                tokens.extend(str(item) for item in value)
            elif value is not None:
                tokens.append(str(value))
        joined = " ".join(tokens)
        for token in tokens:
            if os.path.basename(token) in _DANGEROUS_PROGRAMS:
                raise LiveSystemAccessError(f"{event}: program {os.path.basename(token)!r} is forbidden in tests")
        if _DANGEROUS_SHELL.search(joined):
            raise LiveSystemAccessError(f"{event}: dangerous command in {joined[:60]!r}")
        for port in self.forbidden_ports:
            if str(port) in joined:
                raise LiveSystemAccessError(f"{event}: mentions production port {port}")

    def _check_kill(self, event: str, args: tuple) -> None:
        if len(args) < 2:
            return
        target, sig = args[0], args[1]
        if sig == 0:
            return                                    # liveness probe
        if not isinstance(target, int):
            raise LiveSystemAccessError(f"{event}: unexpected target {target!r}")
        if target in (os.getpid(), os.getpgrp()) or target in self._pids:
            return
        if self._is_session_descendant(target):
            return
        raise LiveSystemAccessError(f"{event}: pid/pgid {target} was not started by this test session")

    def _is_session_descendant(self, target: int) -> bool:
        """True if ``target`` is a process of ours or a process group made of our descendants.

        Second line of defence next to the registered-pid set (children and grandchildren
        that tests legitimately clean up). A foreign process (launchd, the production
        brain, a shell of the user) is never a descendant of this pytest process.
        """
        try:
            table = subprocess.run(
                ["/bin/ps", "-axo", "pid=,ppid=,pgid="], capture_output=True, text=True, timeout=10, check=True
            ).stdout
        except (OSError, subprocess.SubprocessError):
            return False                                   # cannot prove it: refuse (fail closed)
        parent: dict[int, int] = {}
        group: dict[int, int] = {}
        for line in table.splitlines():
            parts = line.split()
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                pid, ppid, pgid = (int(p) for p in parts)
                parent[pid], group[pid] = ppid, pgid
        me = os.getpid()

        def descends(pid: int) -> bool:
            for _ in range(64):                            # bounded walk up the process tree
                if pid == me:
                    return True
                pid = parent.get(pid, 0)
                if pid <= 1:
                    return False
            return False

        members = [pid for pid, pgid in group.items() if pgid == target]
        candidates = members if members else ([target] if target in parent else [])
        if not candidates:
            return True                                    # nothing exists there: the signal harms no one
        return all(descends(pid) and pid != me for pid in candidates)

    def _check_open(self, args: tuple) -> None:
        if len(args) < 3:
            return
        path, mode, flags = args[0], args[1], args[2]
        write = False
        if isinstance(flags, int) and flags & _WRITE_FLAGS:
            write = True
        if isinstance(mode, str) and any(ch in mode for ch in "wax+"):
            write = True
        if write:
            self._check_write_path("open", path)

    def _check_write_path(self, event: str, raw: Any) -> None:
        path = _as_path_str(raw)
        if path is None:
            return
        for candidate in {os.path.abspath(os.path.expanduser(path)), _resolve(path)}:
            for root in self.forbidden_write_roots:
                if candidate == root or candidate.startswith(root + os.sep):
                    raise LiveSystemAccessError(f"{event}: write to formal path {root} is forbidden in tests")


# ── installation ─────────────────────────────────────────────────────────

_installed: Guard | None = None
_original_popen_init = None


def install(guard: Guard | None = None) -> Guard:
    """Install the audit hook (idempotent). Raises on any failure (fail closed)."""
    global _installed, _original_popen_init
    if _installed is not None:
        return _installed
    active = guard if guard is not None else Guard.from_config()

    def hook(event: str, args: tuple) -> None:
        active.evaluate(event, args)

    sys.addaudithook(hook)

    original_init = subprocess.Popen.__init__

    def tracked_init(self, *a, **kw):                  # register children for os.kill checks
        original_init(self, *a, **kw)
        active.register_pid(self.pid)

    subprocess.Popen.__init__ = tracked_init           # type: ignore[method-assign]
    _original_popen_init = original_init
    _installed = active
    return active


def is_installed() -> bool:
    return _installed is not None


def registered_pids() -> frozenset[int]:
    return _installed.registered_pids() if _installed is not None else frozenset()


def register_pid(pid: int) -> None:
    if _installed is None:
        raise LiveSystemAccessError("live guard is not installed")
    _installed.register_pid(pid)
