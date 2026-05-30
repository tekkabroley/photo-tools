"""Tests for path helpers."""

from pathlib import Path

from photo_tools.paths import (
    DuplicateStemTracker,
    is_json_file,
    is_photo_file,
    iter_all_files,
    iter_json_files,
    iter_photo_files,
)


def test_is_photo_file_accepts_supported_extensions(tmp_path: Path) -> None:
    for name in ("a.arw", "b.jpg", "c.jpeg", "d.png", "e.JPG", "f.ArW"):
        path = tmp_path / name
        path.write_bytes(b"x")
        assert is_photo_file(path)


def test_is_photo_file_rejects_other_extensions(tmp_path: Path) -> None:
    path = tmp_path / "file.txt"
    path.write_text("x", encoding="utf-8")
    assert not is_photo_file(path)


def test_is_json_file(tmp_path: Path) -> None:
    json_path = tmp_path / "meta.json"
    json_path.write_text("{}", encoding="utf-8")
    assert is_json_file(json_path)
    assert not is_json_file(tmp_path / "photo.jpg")


def test_iter_photo_files_single_file(sample_jpg: Path) -> None:
    assert list(iter_photo_files(sample_jpg)) == [sample_jpg]


def test_iter_photo_files_directory(nested_photo_tree: Path) -> None:
    files = list(iter_photo_files(nested_photo_tree))
    assert len(files) == 3


def test_iter_all_files_directory_includes_non_photos(nested_photo_tree: Path) -> None:
    files = list(iter_all_files(nested_photo_tree))
    assert len(files) == 5
    assert any(p.name == "notes.txt" for p in files)


def test_iter_json_files_directory(nested_json_tree: Path) -> None:
    files = list(iter_json_files(nested_json_tree))
    assert len(files) == 2


def test_duplicate_stem_tracker_skips_second() -> None:
    tracker = DuplicateStemTracker()
    first = Path("/photos/a/IMG.jpg")
    second = Path("/photos/b/IMG.jpg")
    assert tracker.accept(first, "IMG") is True
    assert tracker.accept(second, "IMG") is False


def test_iter_photo_files_non_photo_file(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("x", encoding="utf-8")
    assert list(iter_photo_files(path)) == []


def test_iter_photo_files_missing_path(tmp_path: Path) -> None:
    assert list(iter_photo_files(tmp_path / "missing")) == []


def test_iter_json_files_non_json_file(tmp_path: Path) -> None:
    path = tmp_path / "photo.jpg"
    path.write_bytes(b"\xff\xd8\xff")
    assert list(iter_json_files(path)) == []


def test_iter_json_files_missing_path(tmp_path: Path) -> None:
    assert list(iter_json_files(tmp_path / "missing")) == []
