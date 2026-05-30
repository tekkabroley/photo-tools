"""Extract photo metadata via ExifTool and write JSON files."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import exiftool
from exiftool.exceptions import ExifToolException

from photo_tools.exceptions import DependencyError, UserError
from photo_tools.paths import (
    DuplicateStemTracker,
    ensure_output_dir,
    is_photo_file,
    iter_photo_files,
)

logger = logging.getLogger(__name__)


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    return str(value)


def _normalize_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    return {str(key): _json_safe(value) for key, value in raw.items()}


def read_photo_metadata(photo_path: Path) -> dict[str, Any]:
    try:
        with exiftool.ExifToolHelper() as helper:
            results = helper.get_metadata(str(photo_path))
    except FileNotFoundError as exc:
        raise DependencyError(
            "exiftool binary not found. Install ExifTool and ensure it is on PATH."
        ) from exc
    except ExifToolException as exc:
        raise DependencyError(
            "ExifTool failed. Ensure exiftool is installed and on PATH."
        ) from exc

    if not results:
        return {}
    return _normalize_metadata(results[0])


def write_metadata_json(metadata: dict[str, Any], output_file: Path) -> None:
    output_file.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def extract_photo_metadata(input_path: Path, output_path: Path) -> int:
    """Extract metadata for one or more photos. Returns count of files written."""
    if not input_path.exists():
        raise UserError(f"Input path does not exist: {input_path}")

    if input_path.is_file() and not is_photo_file(input_path):
        raise UserError(f"Input is not a supported photo file: {input_path}")

    output_dir = ensure_output_dir(output_path)
    tracker = DuplicateStemTracker()
    written = 0

    for photo in iter_photo_files(input_path):
        stem = photo.stem
        if not tracker.accept(photo, stem):
            continue

        metadata = read_photo_metadata(photo)
        out_file = output_dir / f"{stem}.json"
        write_metadata_json(metadata, out_file)
        logger.info("Wrote metadata: %s", out_file)
        written += 1

    return written
