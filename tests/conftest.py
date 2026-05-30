"""Shared pytest fixtures."""

from __future__ import annotations

import shutil
from pathlib import Path

import piexif
import pytest
from PIL import Image

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def exiftool_available() -> bool:
    return shutil.which("exiftool") is not None


requires_exiftool = pytest.mark.skipif(
    not exiftool_available(),
    reason="exiftool binary not installed",
)


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def sample_jpg(tmp_path: Path) -> Path:
    """Minimal JPEG with injectable EXIF."""
    path = tmp_path / "sample.jpg"
    image = Image.new("RGB", (100, 50), color="red")
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: b"TestMake",
            piexif.ImageIFD.Model: b"TestModel",
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: b"2025:01:15 12:00:00",
            piexif.ExifIFD.PixelXDimension: 100,
            piexif.ExifIFD.PixelYDimension: 50,
        },
    }
    exif_bytes = piexif.dump(exif_dict)
    image.save(path, "JPEG", exif=exif_bytes)
    return path


@pytest.fixture
def sample_png(tmp_path: Path) -> Path:
    path = tmp_path / "sample.png"
    image = Image.new("RGBA", (80, 40), color=(0, 128, 255, 255))
    image.save(path, "PNG")
    return path


@pytest.fixture
def nested_photo_tree(tmp_path: Path, sample_jpg: Path, sample_png: Path) -> Path:
    """Directory tree with photos and non-photos."""
    root = tmp_path / "photos"
    (root / "subdir").mkdir(parents=True)
    (root / "other").mkdir(parents=True)

    shutil.copy(sample_jpg, root / "photo_a.jpg")
    shutil.copy(sample_png, root / "subdir" / "photo_b.png")
    shutil.copy(sample_jpg, root / "subdir" / "PHOTO_C.JPG")
    (root / "notes.txt").write_text("ignore me", encoding="utf-8")
    (root / "other" / "readme.txt").write_text("ignore", encoding="utf-8")
    return root


@pytest.fixture
def duplicate_stem_photo_tree(tmp_path: Path, sample_jpg: Path) -> Path:
    root = tmp_path / "dup_photos"
    (root / "alpha").mkdir(parents=True)
    (root / "beta").mkdir(parents=True)
    shutil.copy(sample_jpg, root / "alpha" / "duplicate.jpg")
    shutil.copy(sample_jpg, root / "beta" / "duplicate.jpg")
    return root


@pytest.fixture
def nested_json_tree(tmp_path: Path, fixtures_dir: Path) -> Path:
    root = tmp_path / "json_in"
    (root / "nested").mkdir(parents=True)
    shutil.copy(fixtures_dir / "sample_metadata.json", root / "sample_metadata.json")
    shutil.copy(
        fixtures_dir / "sample_metadata.json",
        root / "nested" / "nested_meta.json",
    )
    (root / "ignore.txt").write_text("nope", encoding="utf-8")
    return root


@pytest.fixture
def duplicate_stem_json_tree(tmp_path: Path, fixtures_dir: Path) -> Path:
    root = tmp_path / "dup_json"
    (root / "a").mkdir(parents=True)
    (root / "b").mkdir(parents=True)
    shutil.copy(fixtures_dir / "sample_metadata.json", root / "a" / "same.json")
    shutil.copy(fixtures_dir / "sample_metadata.json", root / "b" / "same.json")
    return root


@pytest.fixture
def sparse_metadata_json(tmp_path: Path) -> Path:
    path = tmp_path / "sparse.json"
    path.write_text("{}", encoding="utf-8")
    return path


@pytest.fixture
def unicode_stem_jpg(tmp_path: Path) -> Path:
    path = tmp_path / "café.jpg"
    image = Image.new("RGB", (10, 10), color="green")
    image.save(path, "JPEG")
    return path
