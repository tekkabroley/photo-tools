"""CLI smoke tests."""

from typer.testing import CliRunner

from photo_tools.cli import app

runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "get-photo-metadata" in result.output
    assert "create-metadata-markdown" in result.output


def test_get_photo_metadata_help() -> None:
    result = runner.invoke(app, ["get-photo-metadata", "--help"])
    assert result.exit_code == 0
    assert "Extract all metadata" in result.output


def test_create_metadata_markdown_help() -> None:
    result = runner.invoke(app, ["create-metadata-markdown", "--help"])
    assert result.exit_code == 0
    assert "YAML-frontmatter" in result.output
