"""
Storage primitives for the JSON file persistence layer.

Two responsibilities:

1. Data directory resolution (single source of truth, resolved lazily).

   The data directory must NEVER be captured as a default argument or module-level
   constant that callers close over, because that freezes it at import time and makes
   test overrides silently ineffective. Always call get_data_dir() at use time.

2. Atomic JSON writes.

   json.dumps + Path.write_text truncates the target before writing. A crash or a
   concurrent write mid-flight leaves a truncated or interleaved file. We write to a
   temporary file in the same directory and then os.replace(), which is atomic on both
   POSIX and Windows, so a reader either sees the old file or the new one.

Concurrency scope (honest limitation):
   The lock here is a per-path threading.Lock, so it serialises writes within a single
   process (including FastAPI's threadpool for sync endpoints). It does NOT coordinate
   across multiple OS processes (e.g. several uvicorn workers). For the Demo, the app is
   run single-process. Multi-process safety would require OS-level file locking or a
   real database — see ADR-0006.
"""

import json
import os
import threading
from pathlib import Path
from typing import Any, Optional

# Canonical production data directory (backend/data).
# Exposed so tests can assert they are NOT using it.
PRODUCTION_DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Runtime override, set by tests or alternative deployments.
_data_dir_override: Optional[Path] = None

# One lock per resolved file path.
_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def get_data_dir() -> Path:
    """
    Return the active data directory.

    Resolved at call time so overrides always take effect.
    """
    return _data_dir_override if _data_dir_override is not None else PRODUCTION_DATA_DIR


def set_data_dir(path: Optional[Path]) -> None:
    """
    Override the active data directory. Pass None to restore production.

    Intended for tests and for pointing a deployment at a different data volume.
    """
    global _data_dir_override
    _data_dir_override = Path(path) if path is not None else None


def _lock_for(path: Path) -> threading.Lock:
    """Get (or create) the lock guarding a specific file path."""
    key = str(path.resolve())
    with _locks_guard:
        if key not in _locks:
            _locks[key] = threading.Lock()
        return _locks[key]


def read_json(path: Path) -> list[dict]:
    """
    Read a JSON array from disk. Returns [] when missing or empty.

    Raises ValueError with the offending path if the file is not valid JSON, so a
    corrupted data file is reported explicitly instead of silently becoming empty.
    """
    if not path.exists():
        return []

    content = path.read_text(encoding="utf-8")
    if not content.strip():
        return []

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Corrupted JSON data file: {path} ({exc})") from exc

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}, got {type(data).__name__}")

    return data


def write_json_atomic(path: Path, records: list[Any]) -> None:
    """
    Write a JSON array to disk atomically.

    Strategy: serialise first (so a serialisation error never touches the target),
    write to a sibling temp file, flush + fsync, then os.replace() onto the target.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Serialise before opening the target so failures leave the original intact.
    payload = json.dumps(records, ensure_ascii=False, indent=2)

    lock = _lock_for(path)
    with lock:
        tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, path)  # atomic on POSIX and Windows
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass


def mutate_json_atomic(path: Path, mutator) -> Any:
    """
    Read-modify-write a JSON file while holding the write lock for the whole cycle.

    This closes the read-modify-write race that exists when read and write are
    separate lock acquisitions: two callers could both read the old list and the
    second write would drop the first caller's record.

    Args:
        path: Target JSON file.
        mutator: Callable receiving the current list and returning
                 (new_list, result). Only new_list is persisted.

    Returns:
        The `result` value produced by the mutator.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = _lock_for(path)

    with lock:
        current = read_json(path)
        new_records, result = mutator(current)

        payload = json.dumps(new_records, ensure_ascii=False, indent=2)
        tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, path)
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    return result
