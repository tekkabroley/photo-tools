"""Path helpers for walking inputs and naming outputs."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

from photo_tools.constants import PHOTO_EXTENSIONS

logger = logging.getLogger(__name__)


def is_photo_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in PHOTO_EXTENSIONS


def is_json_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == ".json"


def ensure_output_dir(output_path: Path) -> Path:
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def iter_photo_files(input_path: Path) -> Iterator[Path]:
    """Yield photo files from a single file or recursive directory walk."""
    if input_path.is_file():
        if not is_photo_file(input_path):
            return
        yield input_path
        return

    if not input_path.is_dir():
        return

    for path in sorted(input_path.rglob("*")):
        if is_photo_file(path):
            yield path


def iter_json_files(input_path: Path) -> Iterator[Path]:
    """Yield JSON files from a single file or recursive directory walk."""
    if input_path.is_file():
        if not is_json_file(input_path):
            return
        yield input_path
        return

    if not input_path.is_dir():
        return

    for path in sorted(input_path.rglob("*")):
        if is_json_file(path):
            yield path


class DuplicateStemTracker:
    """Track output stems; warn and skip duplicates (first wins)."""

    def __init__(self) -> None:
        self._seen: dict[str, Path] = {}

    def accept(self, source: Path, stem: str) -> bool:
        if stem in self._seen:
            logger.warning(
                "Skipping duplicate stem %r: %s (already from %s)",
                stem,
                source,
                self._seen[stem],
            )
            return False
        self._seen[stem] = source
        return True
