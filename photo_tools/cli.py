"""Typer CLI entry point."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from photo_tools.exceptions import PhotoToolsError
from photo_tools.metadata.extract import extract_photo_metadata
from photo_tools.metadata.markdown import create_metadata_markdown

app = typer.Typer(
    name="photo-tools",
    help="Extract photo metadata and generate markdown frontmatter files.",
    no_args_is_help=True,
)


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def _run_command(action) -> None:
    try:
        action()
    except PhotoToolsError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=exc.exit_code) from exc


@app.callback()
def main(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable debug logging."),
    ] = False,
) -> None:
    _configure_logging(verbose)


@app.command("get-photo-metadata")
def get_photo_metadata(
    input_path: Annotated[
        Path,
        typer.Argument(help="Photo file or directory to scan."),
    ],
    output_path: Annotated[
        Path,
        typer.Argument(help="Directory where JSON metadata files are written."),
    ],
) -> None:
    """Extract all metadata from ARW, JPG, and PNG files and write JSON."""

    def action() -> None:
        count = extract_photo_metadata(input_path, output_path)
        typer.echo(f"Wrote {count} metadata file(s) to {output_path}")

    _run_command(action)


@app.command("create-metadata-markdown")
def create_metadata_markdown_cmd(
    input_path: Annotated[
        Path,
        typer.Argument(help="Metadata JSON file or directory to scan."),
    ],
    output_path: Annotated[
        Path,
        typer.Argument(help="Directory where markdown files are written."),
    ],
) -> None:
    """Create YAML-frontmatter markdown from metadata JSON files."""

    def action() -> None:
        count = create_metadata_markdown(input_path, output_path)
        typer.echo(f"Wrote {count} markdown file(s) to {output_path}")

    _run_command(action)


if __name__ == "__main__":
    app()
