"""CLI smoke tests."""

from typer.testing import CliRunner

from photo_tools.cli import app

runner = CliRunner()


def _invoke(*args: str):
    return runner.invoke(app, list(args), color=False)


def test_cli_help() -> None:
    result = _invoke("--help")
    assert result.exit_code == 0
    assert "get-photo-metadata" in result.output
    assert "create-metadata-markdown" in result.output
    assert "sync-to-s3" in result.output


def test_get_photo_metadata_help() -> None:
    result = _invoke("get-photo-metadata", "--help")
    assert result.exit_code == 0
    assert "Extract all metadata" in result.output


def test_create_metadata_markdown_help() -> None:
    result = _invoke("create-metadata-markdown", "--help")
    assert result.exit_code == 0
    assert "YAML-frontmatter" in result.output


def test_sync_to_s3_help() -> None:
    result = _invoke("sync-to-s3", "--help")
    assert result.exit_code == 0
    assert "Sync a file or directory tree to S3" in result.output
