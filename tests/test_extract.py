"""Tests for metadata extraction."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from photo_tools.cli import app
from photo_tools.exceptions import UserError
from photo_tools.metadata.extract import extract_photo_metadata, read_photo_metadata
from markers import requires_exiftool

runner = CliRunner()


@requires_exiftool
def test_extract_single_jpg(sample_jpg: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    count = extract_photo_metadata(sample_jpg, out)
    assert count == 1
    json_path = out / "sample.json"
    assert json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert len(data) > 0


@requires_exiftool
def test_extract_single_png(sample_png: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    count = extract_photo_metadata(sample_png, out)
    assert count == 1
    assert (out / "sample.json").exists()


@requires_exiftool
def test_extract_directory_recursive(nested_photo_tree: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    count = extract_photo_metadata(nested_photo_tree, out)
    assert count == 3
    assert (out / "photo_a.json").exists()
    assert (out / "photo_b.json").exists()
    assert (out / "PHOTO_C.json").exists()


@requires_exiftool
def test_extract_skips_non_photos(nested_photo_tree: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    extract_photo_metadata(nested_photo_tree, out)
    assert not (out / "notes.json").exists()
    assert not (out / "readme.json").exists()


@requires_exiftool
def test_extract_case_insensitive_ext(nested_photo_tree: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    count = extract_photo_metadata(nested_photo_tree, out)
    assert count == 3


def test_extract_missing_input(tmp_path: Path) -> None:
    with pytest.raises(UserError, match="does not exist"):
        extract_photo_metadata(tmp_path / "missing.jpg", tmp_path / "out")


def test_extract_non_photo_file(tmp_path: Path) -> None:
    bad = tmp_path / "notes.txt"
    bad.write_text("x", encoding="utf-8")
    with pytest.raises(UserError, match="not a supported photo"):
        extract_photo_metadata(bad, tmp_path / "out")


@requires_exiftool
def test_extract_creates_output_dir(sample_jpg: Path, tmp_path: Path) -> None:
    out = tmp_path / "new" / "nested" / "out"
    extract_photo_metadata(sample_jpg, out)
    assert out.is_dir()
    assert (out / "sample.json").exists()


@requires_exiftool
def test_extract_empty_directory(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    count = extract_photo_metadata(empty, tmp_path / "out")
    assert count == 0


@requires_exiftool
def test_extract_duplicate_stem_skipped(
    duplicate_stem_photo_tree: Path,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    caplog.set_level(logging.WARNING)
    out = tmp_path / "out"
    count = extract_photo_metadata(duplicate_stem_photo_tree, out)
    assert count == 1
    assert (out / "duplicate.json").exists()
    assert any("Skipping duplicate stem" in record.message for record in caplog.records)


@requires_exiftool
def test_extract_cli_missing_input(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["get-photo-metadata", str(tmp_path / "nope.jpg"), str(tmp_path / "out")],
    )
    assert result.exit_code == 1


@requires_exiftool
def test_overwrite_existing_output(sample_jpg: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    extract_photo_metadata(sample_jpg, out)
    first = (out / "sample.json").read_text(encoding="utf-8")
    extract_photo_metadata(sample_jpg, out)
    second = (out / "sample.json").read_text(encoding="utf-8")
    assert json.loads(first) == json.loads(second)


@requires_exiftool
def test_unicode_filename(unicode_stem_jpg: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    count = extract_photo_metadata(unicode_stem_jpg, out)
    assert count == 1
    assert (out / "café.json").exists()


@requires_exiftool
def test_read_photo_metadata_returns_dict(sample_jpg: Path) -> None:
    data = read_photo_metadata(sample_jpg)
    assert isinstance(data, dict)
