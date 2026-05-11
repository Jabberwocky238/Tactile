from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path


ARTIFACT_SUBDIR = "macos-app-workflow"
SESSION_ARTIFACT_DIR_ENV_VARS = (
    "TACTILE_SESSION_ARTIFACT_DIR",
)
SESSION_DIR_ENV_VARS = (
    "TACTILE_SESSION_DIR",
    "OPENCODE_SESSION_DIR",
    "CODEX_SESSION_DIR",
)
SESSION_ID_ENV_VARS = (
    "TACTILE_SESSION_ID",
    "OPENCODE_SESSION_ID",
    "CODEX_SESSION_ID",
)
WORKSPACE_ROOT_ENV_VARS = (
    "TACTILE_WORKSPACE_ROOT",
    "OPENCODE_WORKSPACE_ROOT",
    "WORKSPACE_ROOT",
)


def safe_path_component(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "-" for ch in value.strip())
    return cleaned.strip(".-") or "session"


def find_workspace_root(start: Path) -> Path | None:
    current = start.expanduser().resolve()
    candidates = [current] if current.is_dir() else [current.parent]
    candidates.extend(candidates[0].parents)
    for candidate in candidates:
        if (candidate / ".claw" / "sessions").is_dir() or (candidate / ".opencode").exists():
            return candidate
    return None


def latest_session_dir(workspace_root: Path, session_ids: list[str]) -> Path | None:
    sessions_root = workspace_root / ".claw" / "sessions"
    if not sessions_root.is_dir():
        return None

    for session_id in session_ids:
        safe_id = safe_path_component(session_id)
        matches = sorted(
            sessions_root.glob(f"*/{safe_id}.jsonl"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if matches:
            return matches[0].parent
        direct = sessions_root / safe_id
        if direct.is_dir():
            return direct

    session_files = sorted(
        sessions_root.glob("*/*.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if session_files:
        return session_files[0].parent

    session_dirs = sorted(
        (path for path in sessions_root.iterdir() if path.is_dir()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return session_dirs[0] if session_dirs else None


def session_artifact_dir(
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    create: bool = True,
) -> Path:
    current_env = os.environ if env is None else env

    for key in SESSION_ARTIFACT_DIR_ENV_VARS:
        if explicit_artifact_dir := current_env.get(key):
            artifact_dir = Path(explicit_artifact_dir).expanduser()
            if create:
                artifact_dir.mkdir(parents=True, exist_ok=True)
            return artifact_dir

    for key in SESSION_DIR_ENV_VARS:
        value = current_env.get(key)
        if value:
            artifact_dir = Path(value).expanduser() / ARTIFACT_SUBDIR
            if create:
                artifact_dir.mkdir(parents=True, exist_ok=True)
            return artifact_dir

    session_ids = [value for key in SESSION_ID_ENV_VARS if (value := current_env.get(key))]
    workspace_candidates = [
        Path(value).expanduser()
        for key in WORKSPACE_ROOT_ENV_VARS
        if (value := current_env.get(key))
    ]
    if cwd is not None:
        workspace = find_workspace_root(cwd)
        if workspace is not None:
            workspace_candidates.append(workspace)

    seen_workspaces: set[Path] = set()
    for workspace in workspace_candidates:
        workspace = workspace.resolve()
        if workspace in seen_workspaces:
            continue
        seen_workspaces.add(workspace)
        session_dir = latest_session_dir(workspace, session_ids)
        if session_dir is not None:
            artifact_dir = session_dir / ARTIFACT_SUBDIR
            if create:
                artifact_dir.mkdir(parents=True, exist_ok=True)
            return artifact_dir

    if session_ids:
        artifact_dir = (
            Path.home()
            / ".local"
            / "share"
            / "opencode"
            / "storage"
            / "session_artifacts"
            / safe_path_component(session_ids[0])
            / ARTIFACT_SUBDIR
        )
        if create:
            artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir

    fallback_root = find_workspace_root(cwd or Path.cwd()) or (cwd or Path.cwd())
    fallback_dir = fallback_root / f".{ARTIFACT_SUBDIR}"
    if session_ids:
        fallback_dir = fallback_dir / safe_path_component(session_ids[0])
    if create:
        fallback_dir.mkdir(parents=True, exist_ok=True)
    return fallback_dir


def default_artifact_path(
    prefix: str,
    suffix: str,
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> Path:
    stamp = int(time.time() * 1000)
    return session_artifact_dir(cwd=cwd, env=env) / f"{safe_path_component(prefix)}-{stamp}{suffix}"


def is_temporary_path(path: Path) -> bool:
    resolved = path.expanduser().resolve()
    temporary_roots = [
        Path("/tmp").resolve(),
        Path("/private/tmp").resolve(),
        Path(tempfile.gettempdir()).resolve(),
    ]
    return any(resolved == root or root in resolved.parents for root in temporary_roots)


def session_scoped_output_path(output: Path | None) -> Path | None:
    if output is None:
        return None
    expanded = output.expanduser()
    if is_temporary_path(expanded):
        return session_artifact_dir(cwd=Path.cwd()) / expanded.name
    if any(parent.name == f".{ARTIFACT_SUBDIR}" for parent in [expanded.parent, *expanded.parents]):
        artifact_dir = session_artifact_dir(cwd=Path.cwd())
        if artifact_dir.resolve() != expanded.parent.resolve():
            return artifact_dir / expanded.name
    return expanded
