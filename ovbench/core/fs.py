"""File system utilities."""

import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import Union


def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if needed."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def atomic_write(path: Union[str, Path], content: str, mode: str = "w"):
    """Write file atomically using temporary file and rename."""
    path = Path(path)
    ensure_dir(path.parent)

    with tempfile.NamedTemporaryFile(
        mode=mode,
        dir=path.parent,
        delete=False,
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as tmp:
        tmp.write(content)
        tmp.flush()
        temp_path = Path(tmp.name)

    temp_path.replace(path)


def get_digest(path: Union[str, Path], algorithm: str = "sha256") -> str:
    """Calculate file digest."""
    path = Path(path)
    hasher = hashlib.new(algorithm)

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def copy_tree(src: Union[str, Path], dst: Union[str, Path], symlinks: bool = False):
    """Copy directory tree."""
    src = Path(src)
    dst = Path(dst)

    if not src.exists():
        raise FileNotFoundError(f"Source not found: {src}")

    if src.is_file():
        ensure_dir(dst.parent)
        shutil.copy2(src, dst)
    else:
        shutil.copytree(src, dst, symlinks=symlinks, dirs_exist_ok=True)


def clean_dir(path: Union[str, Path], keep_root: bool = True):
    """Clean directory contents."""
    path = Path(path)

    if not path.exists():
        return

    if keep_root:
        for item in path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    else:
        shutil.rmtree(path)


def get_size(path: Union[str, Path]) -> int:
    """Get file or directory size in bytes."""
    path = Path(path)

    if path.is_file():
        return path.stat().st_size

    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def format_size(size_bytes: int) -> str:
    """Format size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"
