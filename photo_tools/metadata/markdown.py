"""Build markdown frontmatter files from metadata JSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from photo_tools.constants import (
    COLLECTION_FIELD_CANDIDATES,
    DATE_FIELD_CANDIDATES,
    FRONTMATTER_FIELD_ORDER,
    HEIGHT_FIELD_CANDIDATES,
    LOCATION_FIELD_CANDIDATES,
    S3_GALLERY_BASE_URL,
    WIDTH_FIELD_CANDIDATES,
)
from photo_tools.exceptions import UserError
from photo_tools.paths import (
    DuplicateStemTracker,
    ensure_output_dir,
    is_json_file,
    iter_json_files,
)

logger = logging.getLogger(__name__)


def _tag_suffix(key: str) -> str:
    if ":" in key:
        return key.rsplit(":", 1)[-1]
    return key


def get_tag(metadata: dict[str, Any], *candidates: str) -> str | None:
    """Return first matching tag value from metadata (exact or suffix match)."""
    normalized = {_tag_suffix(k): v for k, v in metadata.items() if v not in (None, "")}
    for candidate in candidates:
        if candidate in metadata and metadata[candidate] not in (None, ""):
            return str(metadata[candidate])
        if candidate in normalized and normalized[candidate] not in (None, ""):
            return str(normalized[candidate])
    return None


def _format_location(metadata: dict[str, Any]) -> str:
    direct = get_tag(metadata, *LOCATION_FIELD_CANDIDATES)
    if direct:
        return direct

    city = get_tag(metadata, "City")
    state = get_tag(metadata, "State", "Province")
    if city and state:
        return f"{city}, {state}"
    if city:
        return city
    if state:
        return state

    gps = get_tag(metadata, "GPSPosition", "GPSCoordinates")
    if gps:
        return gps

    sub_location = get_tag(metadata, "Sub-location", "SubLocation", "LocationShown")
    if sub_location:
        return sub_location

    return ""


def build_image_url(json_stem: str) -> str:
    return f"{S3_GALLERY_BASE_URL}/{json_stem}.jpg"


def map_frontmatter_fields(metadata: dict[str, Any], json_stem: str) -> dict[str, str]:
    date = get_tag(metadata, *DATE_FIELD_CANDIDATES) or ""
    location = _format_location(metadata)
    collection = get_tag(metadata, *COLLECTION_FIELD_CANDIDATES) or ""
    width = get_tag(metadata, *WIDTH_FIELD_CANDIDATES) or ""
    height = get_tag(metadata, *HEIGHT_FIELD_CANDIDATES) or ""

    return {
        "date": date,
        "image": build_image_url(json_stem),
        "location": location,
        "collection": collection,
        "width": width,
        "height": height,
    }


def render_frontmatter(fields: dict[str, str]) -> str:
    lines = ["---"]
    for key in FRONTMATTER_FIELD_ORDER:
        lines.append(f"{key}: {fields[key]}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def load_metadata_json(json_path: Path) -> dict[str, Any]:
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise UserError(f"Invalid JSON in {json_path}: {exc.msg}") from exc

    if not isinstance(data, dict):
        raise UserError(f"Expected JSON object in {json_path}")
    return data


def create_metadata_markdown(input_path: Path, output_path: Path) -> int:
    """Create markdown frontmatter files from metadata JSON. Returns count written."""
    if not input_path.exists():
        raise UserError(f"Input path does not exist: {input_path}")

    if input_path.is_file() and not is_json_file(input_path):
        raise UserError(f"Input is not a JSON file: {input_path}")

    output_dir = ensure_output_dir(output_path)
    tracker = DuplicateStemTracker()
    written = 0

    for json_file in iter_json_files(input_path):
        stem = json_file.stem
        if not tracker.accept(json_file, stem):
            continue

        metadata = load_metadata_json(json_file)
        fields = map_frontmatter_fields(metadata, stem)
        md_content = render_frontmatter(fields)
        out_file = output_dir / f"{stem}.md"
        out_file.write_text(md_content, encoding="utf-8")
        logger.info("Wrote markdown: %s", out_file)
        written += 1

    return written
