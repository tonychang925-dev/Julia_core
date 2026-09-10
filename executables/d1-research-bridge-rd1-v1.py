#!/opt/miniconda3/bin/python
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


D1_SOURCE_SHA = "c173f92d34de212f84646d2467e382ea6d8f53ebec24b01ac65404f38d774dd4"
CONTROLLED_ROOT = Path("/Users/admin/julia_rd1_controlled")
D1_RELEASE = CONTROLLED_ROOT / "releases" / f"d1-{D1_SOURCE_SHA}"
D1_MANIFEST = CONTROLLED_ROOT / "manifests" / f"d1-{D1_SOURCE_SHA}.file-manifest.sha256"
BUN_PATH = Path("/Users/admin/.bun/bin/bun")
BUN_SHA256 = "4aa2fe331eb3110723e35dc8170d2d30fb7540805f179aab07a04b6c3daa5a69"
ZOD_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "deploy/d1/zod-v4.4.3"
ZOD_TREE_SHA256 = "18281fa9e1d6eff276fcb954885b98bdc32c8998fa6fc882f7e680b1621088bd"
ZOD_TARBALL_SHA512_BASE64 = (
    "ytENFjIJFl2UwYglde2jchW2Hwm4GJFLDiSXWdTrJQBIN9Fcyp7n4DhxJEiWNAJMV1/"
    "BqWfW/kkg71UDcHJyTQ=="
)
ACQUISITION_ROOT = Path("/private/tmp/julia-d1-rd1-v1-acquisitions")


class LauncherBindingError(RuntimeError):
    pass


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    paths = sorted(path for path in root.rglob("*") if path.is_file())
    for path in paths:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def manifest_entries() -> dict[Path, str]:
    if file_sha256(D1_MANIFEST) != D1_SOURCE_SHA:
        raise LauncherBindingError("D1 release manifest digest mismatch")
    entries: dict[Path, str] = {}
    for line in D1_MANIFEST.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(maxsplit=1)
        path = Path(relative.removeprefix("./"))
        if path.is_absolute() or ".." in path.parts:
            raise LauncherBindingError("D1 manifest contains an unsafe path")
        entries[path] = digest
    observed = {
        path.relative_to(D1_RELEASE)
        for path in D1_RELEASE.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if observed != set(entries):
        raise LauncherBindingError("D1 release file set differs from manifest")
    return entries


def stage_release(entries: dict[Path, str], run_root: Path) -> Path:
    entrypoint = run_root / "research_bridge_entrypoint.ts"
    for relative, expected in entries.items():
        source = D1_RELEASE / relative
        if source.is_symlink() or not source.is_file():
            raise LauncherBindingError(f"D1 manifest file is unavailable: {relative}")
        content = source.read_bytes()
        if hashlib.sha256(content).hexdigest() != expected:
            raise LauncherBindingError(f"D1 source digest mismatch: {relative}")
        target = run_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        target.chmod(0o600 if relative.suffix in {".json", ".md"} else 0o700)
    if not entrypoint.is_file():
        raise LauncherBindingError("D1 entrypoint is absent from manifest")
    return entrypoint


def stage_zod(run_root: Path) -> None:
    package_root = run_root / "node_modules" / "zod"
    package_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ZOD_SOURCE_ROOT, package_root, symlinks=False)
    package = json.loads((package_root / "package.json").read_text(encoding="utf-8"))
    if package.get("name") != "zod" or package.get("version") != "4.4.3":
        raise LauncherBindingError("zod runtime package identity mismatch")
    if tree_sha256(package_root) != ZOD_TREE_SHA256:
        raise LauncherBindingError("zod runtime tree digest mismatch")


def runtime_environment(source_authority: str) -> dict[str, str]:
    acquisition = {
        "allowed_content_types": [
            "text/html",
            "text/plain",
            "application/xhtml+xml",
        ],
        "artifact_root": str(ACQUISITION_ROOT),
        "contract_version": "research.controlled-http-acquisition.v1",
        "max_redirects": 3,
        "max_response_bytes": 4194304,
        "proxy_mode": "DIRECT",
        "timeout_ms": 20000,
    }
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": "/nonexistent",
        "LANG": "C",
        "LC_ALL": "C",
        "BUN_CONFIG_AUTO_INSTALL": "0",
        "JULIA_D1_SOURCE_SHA": D1_SOURCE_SHA,
        "JULIA_D1_RESEARCH_SOURCE_AUTHORITY_JSON": source_authority,
        "JULIA_D1_CONTROLLED_ACQUISITION_CONFIG_JSON": json.dumps(
            acquisition, sort_keys=True, separators=(",", ":")
        ),
        "JULIA_D1_ZOD_VERSION": "4.4.3",
        "JULIA_D1_ZOD_TREE_SHA256": ZOD_TREE_SHA256,
        "JULIA_D1_ZOD_TARBALL_SHA512_BASE64": ZOD_TARBALL_SHA512_BASE64,
    }


def main() -> int:
    if not BUN_PATH.is_file() or file_sha256(BUN_PATH) != BUN_SHA256:
        raise LauncherBindingError("Bun runtime digest mismatch")
    if not ZOD_SOURCE_ROOT.is_dir() or tree_sha256(ZOD_SOURCE_ROOT) != ZOD_TREE_SHA256:
        raise LauncherBindingError("retained zod source artifact digest mismatch")
    entries = manifest_entries()
    run_root = Path(tempfile.mkdtemp(prefix="julia-d1-rd1-v1-", dir="/private/tmp"))
    run_root.chmod(0o700)
    entrypoint = stage_release(entries, run_root)
    stage_zod(run_root)
    source_authority = (run_root / "production_webfetch_authority.json").read_text(
        encoding="utf-8"
    )
    ACQUISITION_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.execve(
        str(BUN_PATH),
        [str(BUN_PATH), "--no-install", str(entrypoint)],
        runtime_environment(source_authority),
    )
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LauncherBindingError as exc:
        print(f"d1-research-bridge-rd1-v1: {exc}", file=sys.stderr)
        raise SystemExit(2)
