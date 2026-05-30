"""Tests for markdown frontmatter generation."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from typer.testing import CliRunner

from photo_tools.cli import app
from photo_tools.constants import S3_GALLERY_BASE_URL
from photo_tools.exceptions import UserError
from photo_tools.metadata.markdown import (
    build_image_url,
    create_metadata_markdown,
    map_frontmatter_fields,
    render_frontmatter,
)
from markers import requires_exiftool

runner = CliRunner()


def test_markdown_all_fields_present(fixtures_dir: Path) -> None:
    metadata = json.loads((fixtures_dir / "sample_metadata.json").read_text(encoding="utf-8"))
    fields = map_frontmatter_fields(metadata, "DSC00037")
    assert fields["date"] == "2025:08:27 21:37:45-07:00"
    assert fields["location"] == "Portland, OR"
    assert fields["collection"] == "Bridges"
    assert fields["width"] == "9214"
    assert fields["height"] == "6143"


def test_markdown_image_url_constructed() -> None:
    url = build_image_url("DSC00037")
    assert url == f"{S3_GALLERY_BASE_URL}/DSC00037.jpg"


def test_markdown_missing_fields_blank(sparse_metadata_json: Path) -> None:
    metadata = json.loads(sparse_metadata_json.read_text(encoding="utf-8"))
    fields = map_frontmatter_fields(metadata, "sparse")
    assert fields["date"] == ""
    assert fields["location"] == ""
    assert fields["collection"] == ""
    assert fields["width"] == ""
    assert fields["height"] == ""
    assert fields["image"] == f"{S3_GALLERY_BASE_URL}/sparse.jpg"


def test_markdown_location_composite() -> None:
    metadata = {"City": "Portland", "State": "OR"}
    fields = map_frontmatter_fields(metadata, "x")
    assert fields["location"] == "Portland, OR"


def test_markdown_single_file(fixtures_dir: Path, tmp_path: Path) -> None:
    json_path = fixtures_dir / "sample_metadata.json"
    out = tmp_path / "out"
    count = create_metadata_markdown(json_path, out)
    assert count == 1
    md = (out / "sample_metadata.md").read_text(encoding="utf-8")
    assert "collection: Bridges" in md


def test_markdown_directory_walk(nested_json_tree: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    count = create_metadata_markdown(nested_json_tree, out)
    assert count == 2
    assert (out / "sample_metadata.md").exists()
    assert (out / "nested_meta.md").exists()


def test_markdown_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(UserError, match="Invalid JSON"):
        create_metadata_markdown(bad, tmp_path / "out")


def test_markdown_missing_input(tmp_path: Path) -> None:
    with pytest.raises(UserError, match="does not exist"):
        create_metadata_markdown(tmp_path / "missing.json", tmp_path / "out")


def test_markdown_output_format() -> None:
    fields = {
        "date": "2025:08:27 21:37:45-07:00",
        "image": f"{S3_GALLERY_BASE_URL}/DSC00037.jpg",
        "location": "Portland, OR",
        "collection": "Bridges",
        "width": "9214",
        "height": "6143",
    }
    rendered = render_frontmatter(fields)
    assert rendered.startswith("---\n")
    assert rendered.endswith("---\n\n")
    assert rendered.index("date:") < rendered.index("image:")
    assert rendered.index("image:") < rendered.index("location:")
    assert rendered.index("location:") < rendered.index("collection:")
    assert rendered.index("collection:") < rendered.index("width:")
    assert rendered.index("width:") < rendered.index("height:")


def test_markdown_duplicate_stem_skipped(
    duplicate_stem_json_tree: Path,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)
    out = tmp_path / "out"
    count = create_metadata_markdown(duplicate_stem_json_tree, out)
    assert count == 1
    assert (out / "same.md").exists()
    assert any("Skipping duplicate stem" in record.message for record in caplog.records)


def test_markdown_non_json_file(tmp_path: Path) -> None:
    bad = tmp_path / "photo.jpg"
    bad.write_bytes(b"\xff\xd8\xff")
    with pytest.raises(UserError, match="not a JSON"):
        create_metadata_markdown(bad, tmp_path / "out")


def test_markdown_cli_missing_input(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["create-metadata-markdown", str(tmp_path / "nope.json"), str(tmp_path / "out")],
    )
    assert result.exit_code == 1


def test_overwrite_existing_markdown(fixtures_dir: Path, tmp_path: Path) -> None:
    json_path = fixtures_dir / "sample_metadata.json"
    out = tmp_path / "out"
    create_metadata_markdown(json_path, out)
    first = (out / "sample_metadata.md").read_text(encoding="utf-8")
    create_metadata_markdown(json_path, out)
    second = (out / "sample_metadata.md").read_text(encoding="utf-8")
    assert first == second


def test_unicode_stem_markdown(tmp_path: Path) -> None:
    json_path = tmp_path / "café.json"
    json_path.write_text('{"City": "Paris"}', encoding="utf-8")
    out = tmp_path / "out"
    count = create_metadata_markdown(json_path, out)
    assert count == 1
    assert (out / "café.md").exists()
    content = (out / "café.md").read_text(encoding="utf-8")
    assert f"{S3_GALLERY_BASE_URL}/café.jpg" in content


@requires_exiftool
def test_cli_integration(sample_jpg: Path, tmp_path: Path) -> None:
    meta_out = tmp_path / "meta"
    md_out = tmp_path / "md"
    result = runner.invoke(
        app,
        ["get-photo-metadata", str(sample_jpg), str(meta_out)],
    )
    assert result.exit_code == 0
    result = runner.invoke(
        app,
        ["create-metadata-markdown", str(meta_out / "sample.json"), str(md_out)],
    )
    assert result.exit_code == 0
    assert (md_out / "sample.md").exists()


@requires_exiftool
def test_large_nested_tree(nested_photo_tree: Path, tmp_path: Path) -> None:
    from photo_tools.metadata.extract import extract_photo_metadata

    out = tmp_path / "out"
    count = extract_photo_metadata(nested_photo_tree, out)
    assert count == 3
    json_files = list(out.glob("*.json"))
    assert len(json_files) == 3
    stems = {p.stem for p in json_files}
    assert len(stems) == 3
