#!/usr/bin/env python3
"""Organize photos under intake into yyyy-MM_yyyyMMddHHMMSS folders using image metadata dates."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DATE_TAGS = (
    "DateTimeOriginal",
    "CreateDate",
    "MediaCreateDate",
    "ModifyDate",
    "FileModifyDate",
)

EXIFTOOL_CANDIDATES = (
    "exiftool",
    r"C:\Users\alexb\AppData\Local\Programs\ExifTool\exiftool.exe",
)


def find_exiftool() -> str:
    for candidate in EXIFTOOL_CANDIDATES:
        path = shutil.which(candidate)
        if path:
            return path
        if Path(candidate).is_file():
            return candidate
    raise FileNotFoundError(
        "ExifTool not found. Install it or add exiftool to your PATH."
    )


def month_from_date(value: str) -> str | None:
    match = re.match(r"(\d{4})[:-](\d{2})", value.strip())
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}"


def read_month(exiftool: str, filepath: Path) -> str | None:
    result = subprocess.run(
        [exiftool, "-json", str(filepath)],
        capture_output=True,
        text=True,
        check=False,
    )
    if not result.stdout.strip():
        stderr = result.stderr.strip()
        raise RuntimeError(f"exiftool failed for {filepath.name}: {stderr}")

    payload = json.loads(result.stdout)
    if not payload:
        return None

    metadata = payload[0]
    for tag in DATE_TAGS:
        value = metadata.get(tag)
        if value is None:
            continue
        month = month_from_date(str(value))
        if month:
            return month
    return None


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def collect_files(intake_dir: Path, skip_dirs: tuple[Path, ...] = ()) -> list[Path]:
    """Return every file under intake_dir, including nested folders.

    Directories in skip_dirs (and anything inside them) are ignored so the
    organizer does not move its own scripts.
    """
    skipped_roots = tuple(path.resolve() for path in skip_dirs)
    files: list[Path] = []
    for path in intake_dir.rglob("*"):
        if not path.is_file() or path.name.startswith("."):
            continue
        resolved = path.resolve()
        if any(_is_under(resolved, root) for root in skipped_roots):
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.as_posix().lower())


def unique_destination(dest: Path) -> Path:
    if not dest.exists():
        return dest

    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def organize_intake(
    intake_dir: Path,
    *,
    destination_root: Path,
    dry_run: bool,
    copy: bool,
    skip_dirs: tuple[Path, ...] = (),
) -> int:
    exiftool = find_exiftool()
    run_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    moved = 0
    skipped = 0
    errors = 0

    files = collect_files(intake_dir, skip_dirs)

    if not files:
        print(f"No files to organize in {intake_dir}")
        return 0

    for filepath in files:
        label = filepath.relative_to(intake_dir)
        try:
            month = read_month(exiftool, filepath)
        except (RuntimeError, json.JSONDecodeError) as exc:
            print(f"ERROR {label}: {exc}", file=sys.stderr)
            errors += 1
            continue

        if month is None:
            print(f"SKIP {label}: no usable date in metadata", file=sys.stderr)
            skipped += 1
            continue

        folder_name = f"{month}_{run_timestamp}"
        target_dir = destination_root / folder_name
        target_path = unique_destination(target_dir / filepath.name)

        if dry_run:
            print(f"DRY-RUN {label} -> {target_path}")
            moved += 1
            continue

        target_dir.mkdir(parents=True, exist_ok=True)
        if copy:
            shutil.copy2(filepath, target_path)
            action = "COPY"
        else:
            shutil.move(filepath, target_path)
            action = "MOVE"

        print(f"{action} {label} -> {target_path}")
        moved += 1

    print(
        f"Done: {moved} organized, {skipped} skipped, {errors} errors "
        f"(destination: {destination_root})"
    )
    return 1 if errors else 0


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    default_intake = script_dir.parent
    default_destination = default_intake.parent

    parser = argparse.ArgumentParser(
        description=(
            "Read metadata from each photo under intake, including every "
            "subdirectory, and move it into a yyyy-MM_yyyyMMddHHMMSS folder "
            "based on the capture date."
        )
    )
    parser.add_argument(
        "--intake",
        type=Path,
        default=default_intake,
        help=(
            "Directory to search recursively for photos "
            f"(default: {default_intake})"
        ),
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=default_destination,
        help=(
            "Root directory where yyyy-MM_yyyyMMddHHMMSS folders are created "
            f"(default: {default_destination})"
        ),
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy files instead of moving them out of intake",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without moving or copying files",
    )
    args = parser.parse_args()

    intake_dir = args.intake.resolve()
    if not intake_dir.is_dir():
        print(f"Intake directory does not exist: {intake_dir}", file=sys.stderr)
        return 1

    return organize_intake(
        intake_dir,
        destination_root=args.destination.resolve(),
        dry_run=args.dry_run,
        copy=args.copy,
        skip_dirs=(script_dir,),
    )


if __name__ == "__main__":
    raise SystemExit(main())