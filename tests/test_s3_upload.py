"""Tests for S3 sync (mocked boto3)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from photo_tools.exceptions import DependencyError, UserError
from photo_tools.s3_upload import (
    list_s3_relative_names,
    load_env_files,
    object_key_for_file,
    parse_s3_path,
    relative_name_for_file,
    sync_to_s3,
)


@patch("photo_tools.s3_upload.load_dotenv")
def test_load_env_files(mock_dotenv: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("AWS_ACCESS_KEY_ID=from-env\n", encoding="utf-8")
    (tmp_path / ".env.local").write_text("AWS_ACCESS_KEY_ID=from-local\n", encoding="utf-8")
    load_env_files()
    assert mock_dotenv.call_count == 2


def test_parse_s3_path_bucket_and_prefix() -> None:
    bucket, prefix = parse_s3_path("s3://my-bucket/gallery/2025/")
    assert bucket == "my-bucket"
    assert prefix == "gallery/2025/"


def test_parse_s3_path_bucket_only() -> None:
    bucket, prefix = parse_s3_path("s3://my-bucket")
    assert bucket == "my-bucket"
    assert prefix == ""


def test_parse_s3_path_adds_trailing_slash() -> None:
    _, prefix = parse_s3_path("s3://bkt/prefix")
    assert prefix == "prefix/"


def test_parse_s3_path_invalid() -> None:
    with pytest.raises(UserError, match="Invalid S3 path"):
        parse_s3_path("https://example.com/bucket")


def test_relative_name_single_file(tmp_path: Path) -> None:
    file_path = tmp_path / "DSC0001.jpg"
    file_path.write_bytes(b"x")
    name = relative_name_for_file(file_path, file_path, single_file_input=True)
    assert name == "DSC0001.jpg"


def test_relative_name_directory(tmp_path: Path) -> None:
    root = tmp_path / "photos"
    (root / "sub").mkdir(parents=True)
    file_path = root / "sub" / "DSC0001.jpg"
    file_path.write_bytes(b"x")
    name = relative_name_for_file(file_path, root, single_file_input=False)
    assert name == "sub/DSC0001.jpg"


def test_object_key_single_file(tmp_path: Path) -> None:
    file_path = tmp_path / "DSC0001.jpg"
    file_path.write_bytes(b"x")
    key = object_key_for_file(
        file_path, file_path, "gallery/", single_file_input=True
    )
    assert key == "gallery/DSC0001.jpg"


def test_object_key_directory(tmp_path: Path) -> None:
    root = tmp_path / "photos"
    (root / "sub").mkdir(parents=True)
    file_path = root / "sub" / "DSC0001.jpg"
    file_path.write_bytes(b"x")
    key = object_key_for_file(
        file_path, root, "out/", single_file_input=False
    )
    assert key == "out/sub/DSC0001.jpg"


def test_list_s3_relative_names() -> None:
    client = MagicMock()
    paginator = MagicMock()
    client.get_paginator.return_value = paginator
    paginator.paginate.return_value = [
        {
            "Contents": [
                {"Key": "tree/a.jpg"},
                {"Key": "tree/sub/b.txt"},
                {"Key": "tree/sub/"},
            ]
        }
    ]

    names = list_s3_relative_names(client, "test-bucket", "tree/")

    assert names == {"a.jpg", "sub/b.txt"}
    paginator.paginate.assert_called_once_with(Bucket="test-bucket", Prefix="tree/")


def _mock_s3_list(client: MagicMock, keys: list[str]) -> None:
    paginator = MagicMock()
    client.get_paginator.return_value = paginator
    contents = [{"Key": key} for key in keys]
    paginator.paginate.return_value = [{"Contents": contents}] if contents else [{}]


@patch("photo_tools.s3_upload.boto3.client")
@patch("photo_tools.s3_upload.load_env_files")
def test_sync_single_file(
    mock_load_env: MagicMock,
    mock_client: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    source = tmp_path / "photo.jpg"
    source.write_bytes(b"data")
    client = mock_client.return_value
    _mock_s3_list(client, [])

    count = sync_to_s3(source, "s3://test-bucket/uploads/")

    assert count == 1
    client.upload_file.assert_called_once_with(
        str(source), "test-bucket", "uploads/photo.jpg"
    )


@patch("photo_tools.s3_upload.boto3.client")
@patch("photo_tools.s3_upload.load_env_files")
def test_sync_directory(
    mock_load_env: MagicMock,
    mock_client: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    root = tmp_path / "in"
    (root / "sub").mkdir(parents=True)
    (root / "a.jpg").write_bytes(b"a")
    (root / "sub" / "b.txt").write_text("b", encoding="utf-8")
    client = mock_client.return_value
    _mock_s3_list(client, [])

    count = sync_to_s3(root, "s3://test-bucket/tree/")

    assert count == 2
    assert client.upload_file.call_count == 2
    client.upload_file.assert_any_call(
        str(root / "a.jpg"), "test-bucket", "tree/a.jpg"
    )
    client.upload_file.assert_any_call(
        str(root / "sub" / "b.txt"), "test-bucket", "tree/sub/b.txt"
    )


@patch("photo_tools.s3_upload.boto3.client")
@patch("photo_tools.s3_upload.load_env_files")
def test_sync_skips_existing_files(
    mock_load_env: MagicMock,
    mock_client: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    root = tmp_path / "in"
    (root / "sub").mkdir(parents=True)
    (root / "a.jpg").write_bytes(b"a")
    (root / "sub" / "b.txt").write_text("b", encoding="utf-8")
    (root / "sub" / "c.txt").write_text("c", encoding="utf-8")
    client = mock_client.return_value
    _mock_s3_list(client, ["tree/a.jpg", "tree/sub/b.txt", "tree/extra-only.txt"])

    count = sync_to_s3(root, "s3://test-bucket/tree/")

    assert count == 1
    client.upload_file.assert_called_once_with(
        str(root / "sub" / "c.txt"), "test-bucket", "tree/sub/c.txt"
    )


@patch("photo_tools.s3_upload.boto3.client")
@patch("photo_tools.s3_upload.load_env_files")
def test_sync_skips_when_single_file_exists(
    mock_load_env: MagicMock,
    mock_client: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    source = tmp_path / "photo.jpg"
    source.write_bytes(b"data")
    client = mock_client.return_value
    _mock_s3_list(client, ["uploads/photo.jpg"])

    count = sync_to_s3(source, "s3://test-bucket/uploads/")

    assert count == 0
    client.upload_file.assert_not_called()


def test_sync_missing_input(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    missing = tmp_path / "nope"
    with pytest.raises(UserError, match="does not exist"):
        sync_to_s3(missing, "s3://bkt/")


@patch("photo_tools.s3_upload.boto3.client")
@patch("photo_tools.s3_upload.load_env_files")
def test_sync_empty_directory(
    mock_load_env: MagicMock,
    mock_client: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    empty = tmp_path / "empty"
    empty.mkdir()
    client = mock_client.return_value
    _mock_s3_list(client, [])
    count = sync_to_s3(empty, "s3://test-bucket/")
    assert count == 0
    mock_client.return_value.upload_file.assert_not_called()


@patch("photo_tools.s3_upload.boto3.client")
@patch("photo_tools.s3_upload.load_env_files")
def test_sync_boto_client_failure(
    mock_load_env: MagicMock,
    mock_client: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from botocore.exceptions import BotoCoreError

    mock_client.side_effect = BotoCoreError()
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    source = tmp_path / "photo.jpg"
    source.write_bytes(b"data")
    with pytest.raises(DependencyError, match="Failed to create S3 client"):
        sync_to_s3(source, "s3://test-bucket/")


@patch("photo_tools.s3_upload.load_env_files")
def test_sync_missing_credentials(
    mock_load_env: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    source = tmp_path / "file.bin"
    source.write_bytes(b"x")
    with pytest.raises(UserError, match="Missing S3 credentials"):
        sync_to_s3(source, "s3://bkt/")


@patch("photo_tools.s3_upload.boto3.client")
@patch("photo_tools.s3_upload.load_env_files")
def test_sync_list_failure(
    mock_load_env: MagicMock,
    mock_client: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from botocore.exceptions import ClientError

    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    source = tmp_path / "photo.jpg"
    source.write_bytes(b"data")
    client = mock_client.return_value
    paginator = MagicMock()
    client.get_paginator.return_value = paginator
    paginator.paginate.side_effect = ClientError(
        {"Error": {"Code": "403", "Message": "Forbidden"}},
        "list_objects_v2",
    )

    with pytest.raises(DependencyError, match="Failed to list objects"):
        sync_to_s3(source, "s3://test-bucket/")


@patch("photo_tools.s3_upload.boto3.client")
@patch("photo_tools.s3_upload.load_env_files")
def test_sync_client_error(
    mock_load_env: MagicMock,
    mock_client: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from botocore.exceptions import ClientError

    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    source = tmp_path / "photo.jpg"
    source.write_bytes(b"data")
    client = mock_client.return_value
    _mock_s3_list(client, [])
    client.upload_file.side_effect = ClientError(
        {"Error": {"Code": "403", "Message": "Forbidden"}},
        "upload_file",
    )

    with pytest.raises(DependencyError, match="Failed to upload"):
        sync_to_s3(source, "s3://test-bucket/")
