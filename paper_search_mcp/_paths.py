from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union


PathLike = Union[str, Path]
_FILENAME_HASH_LENGTH = 8
_FILENAME_HASH_SEPARATOR = "__"
_MAX_FILENAME_LENGTH = 200


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _find_repo_root(start: Optional[Path] = None) -> Path:
    """
    Best-effort repo root discovery.

    Priority is to behave well when running from the repo (e.g. `uv run ...`).
    If no `pyproject.toml` is found, fall back to the current working directory.
    """
    candidates = []
    if start is not None:
        candidates.append(start)
    candidates.append(Path.cwd())

    for candidate in candidates:
        current = candidate.resolve()
        for parent in (current, *current.parents):
            if (parent / "pyproject.toml").is_file():
                return parent
    return Path.cwd().resolve()


def safe_download_root(base_dir: Optional[PathLike] = None) -> Path:
    """
    Return the canonical download root (and ensure it exists).

    Download root is always `docs/downloads/` under the repo root when the repo
    can be discovered. If the repo root cannot be discovered, it is relative to
    the current working directory.
    """
    base = Path(base_dir).resolve() if base_dir is not None else _find_repo_root()
    base_resolved = base.resolve()
    download_root = (base_resolved / "docs" / "downloads").resolve()

    if not _is_relative_to(download_root, base_resolved):
        raise ValueError(
            f"Refusing to use download root outside base dir: {download_root}"
        )

    download_root.mkdir(parents=True, exist_ok=True)
    return download_root


def sanitize_filename(filename: str, *, default: str = "paper.pdf") -> str:
    """
    Sanitize a user-controlled filename so it is safe to use as a path segment.
    """
    if not filename:
        filename = default

    name = str(filename).strip()
    if name in {"", ".", ".."}:
        name = default

    normalized_name = name.replace("\\", "/")
    parts = []
    for raw_part in normalized_name.split("/"):
        part = raw_part.strip()
        if part in {"", ".", ".."}:
            continue
        part = part.replace(":", "_")
        part = "".join(ch for ch in part if ch >= " " and ch != "\x7f").strip()
        if part and part not in {".", ".."}:
            parts.append(part)

    if not parts:
        fallback_name = str(default).strip() or "paper.pdf"
        normalized_name = fallback_name.replace("\\", "/")
        parts = [part for part in normalized_name.split("/") if part not in {"", ".", ".."}]

    name = "_".join(parts).strip()

    if not name:
        name = default

    suffix = Path(name).suffix
    stem = Path(name).stem or Path(default).stem or "paper"
    digest = hashlib.sha256(normalized_name.encode("utf-8")).hexdigest()[
        :_FILENAME_HASH_LENGTH
    ]
    max_stem_length = max(
        1,
        _MAX_FILENAME_LENGTH
        - len(suffix)
        - len(_FILENAME_HASH_SEPARATOR)
        - len(digest),
    )
    stem = stem[:max_stem_length]
    name = f"{stem}{_FILENAME_HASH_SEPARATOR}{digest}{suffix}"

    if name in {".", ".."}:
        name = default

    return name


def _normalize_subdir(save_path: Optional[str]) -> Optional[Path]:
    if save_path is None:
        return None

    raw = str(save_path).strip()
    if not raw:
        return None

    raw = raw.replace("\\", "/")
    if raw.startswith("/"):
        raise ValueError("save_path must be relative (absolute paths are not allowed)")
    if len(raw) >= 2 and raw[1] == ":":
        raise ValueError("save_path must not include a drive prefix")
    while raw.startswith("./"):
        raw = raw[2:]
    raw = raw.strip("/")

    if not raw:
        return None

    parts = [part for part in raw.split("/") if part not in {"", "."}]
    if ".." in parts:
        raise ValueError("save_path must not contain '..'")

    if parts[:2] == ["docs", "downloads"]:
        parts = parts[2:]
    elif parts[:1] == ["downloads"]:
        parts = parts[1:]

    if not parts:
        return None

    return Path(*parts)


@dataclass(frozen=True)
class SafeDownloadTarget:
    """
    Result of resolving a safe download path under `docs/downloads/`.
    """

    root: Path
    path: Path


def resolve_download_target(
    *,
    filename: str,
    save_path: Optional[str] = None,
    base_dir: Optional[PathLike] = None,
) -> SafeDownloadTarget:
    """
    Resolve a filesystem path for a downloaded artifact under `docs/downloads/`.

    - Always writes under the canonical download root.
    - Refuses path traversal and absolute paths.
    - Creates parent directories as needed.
    """
    root = safe_download_root(base_dir)
    subdir = _normalize_subdir(save_path)

    target_dir = (root / subdir).resolve() if subdir is not None else root
    if not _is_relative_to(target_dir, root):
        raise ValueError("Refusing to use a download directory outside download root")

    safe_name = sanitize_filename(filename)
    target = (target_dir / safe_name).resolve()
    if not _is_relative_to(target, root):
        raise ValueError("Refusing to write outside download root")

    target.parent.mkdir(parents=True, exist_ok=True)
    return SafeDownloadTarget(root=root, path=target)
