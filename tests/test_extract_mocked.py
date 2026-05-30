"""Mocked extraction tests (no exiftool required)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from photo_tools.exceptions import DependencyError
from photo_tools.metadata.extract import extract_photo_metadata, read_photo_metadata


@patch("photo_tools.metadata.extract.exiftool.ExifToolHelper")
def test_extract_with_mocked_exiftool(mock_helper: MagicMock, sample_jpg: Path, tmp_path: Path) -> None:
    instance = mock_helper.return_value.__enter__.return_value
    instance.get_metadata.return_value = [{"EXIF:DateTimeOriginal": "2025:01:15 12:00:00"}]

    out = tmp_path / "out"
    count = extract_photo_metadata(sample_jpg, out)
    assert count == 1
    assert (out / "sample.json").exists()


@patch("photo_tools.metadata.extract.exiftool.ExifToolHelper")
def test_read_photo_metadata_dependency_error(mock_helper: MagicMock, sample_jpg: Path) -> None:
    from exiftool.exceptions import ExifToolException

    mock_helper.return_value.__enter__.side_effect = ExifToolException("fail")
    with pytest.raises(DependencyError, match="ExifTool failed"):
        read_photo_metadata(sample_jpg)


@patch("photo_tools.metadata.extract.exiftool.ExifToolHelper")
def test_read_photo_metadata_not_found(mock_helper: MagicMock, sample_jpg: Path) -> None:
    mock_helper.return_value.__enter__.side_effect = FileNotFoundError
    with pytest.raises(DependencyError, match="not found"):
        read_photo_metadata(sample_jpg)


@patch("photo_tools.metadata.extract.exiftool.ExifToolHelper")
def test_read_photo_metadata_normalizes_complex_values(
    mock_helper: MagicMock, sample_jpg: Path
) -> None:
    instance = mock_helper.return_value.__enter__.return_value
    instance.get_metadata.return_value = [
        {
            "Binary": b"bytes",
            "List": [1, 2],
            "Nested": {"inner": True},
            "Other": object(),
            "Empty": None,
        }
    ]
    data = read_photo_metadata(sample_jpg)
    assert data["Binary"] == "bytes"
    assert data["List"] == [1, 2]
    assert data["Nested"] == {"inner": True}
    assert isinstance(data["Other"], str)
    assert data["Empty"] is None


@patch("photo_tools.metadata.extract.exiftool.ExifToolHelper")
def test_read_photo_metadata_empty_result(mock_helper: MagicMock, sample_jpg: Path) -> None:
    mock_helper.return_value.__enter__.return_value.get_metadata.return_value = []
    assert read_photo_metadata(sample_jpg) == {}
