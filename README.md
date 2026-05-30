# photo-tools

CLI utility to extract metadata from photo files (ARW, JPG, PNG) and generate YAML-frontmatter markdown files.

## Requirements

- Python 3.10+
- [ExifTool](https://exiftool.org/) installed and available on `PATH`

### Install ExifTool

| Platform | Command |
|----------|---------|
| Windows | Download from [exiftool.org](https://exiftool.org/) or `choco install exiftool` |
| macOS | `brew install exiftool` |
| Linux | `apt install libimage-exiftool-perl` (Debian/Ubuntu) |

## Install

The project uses a virtual environment at `.venv/`.

**Windows (cmd):**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e ".[dev]"
```

Or use the helper:

```cmd
activate-cli.cmd
```

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

CLI-only dependencies (no test tools):

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

### Extract photo metadata to JSON

```bash
photo-tools get-photo-metadata INPUT_PATH OUTPUT_PATH
```

- `INPUT_PATH` — photo file or directory (walks subdirectories)
- `OUTPUT_PATH` — directory for JSON files named `{stem}.json`

Example: `DSC00037.ARW` → `DSC00037.json`

Duplicate stems in a directory walk log a warning and are skipped (first file wins).

### Create markdown frontmatter from JSON

```bash
photo-tools create-metadata-markdown INPUT_PATH OUTPUT_PATH
```

- `INPUT_PATH` — metadata JSON file or directory
- `OUTPUT_PATH` — directory for markdown files named `{stem}.md`

Example output:

```markdown
---
date: 2025:08:27 21:37:45-07:00
image: https://served-photos-556758165742-us-west-2-an.s3.us-west-2.amazonaws.com/gallery/DSC00037.jpg
location: Portland, OR
collection: Bridges
width: 9214
height: 6143
---
```

### Field mapping

| Field | Source |
|-------|--------|
| `date` | `DateTimeOriginal`, `CreateDate`, `ModifyDate`, `DateCreated` |
| `image` | Constructed S3 URL from JSON filename stem (always `.jpg`) |
| `location` | `Location`, or `City` + `State`, or `GPSPosition`, or `Sub-location` |
| `collection` | `Collection`, `Keywords`, `Subject`, `Album` |
| `width` | `ImageWidth`, `ExifImageWidth`, `PixelXDimension` |
| `height` | `ImageHeight`, `ExifImageHeight`, `PixelYDimension` |

Missing metadata fields are written blank. `image` is always constructed.

### Upload files to S3

```bash
photo-tools write-to-s3 INPUT_PATH S3_PATH
```

- `INPUT_PATH` — file or directory (walks subdirectories; uploads every file)
- `S3_PATH` — destination URI, e.g. `s3://my-bucket/gallery/`

Directory uploads preserve relative paths under the S3 prefix. A single file is placed directly under the prefix using its filename.

Credentials are read from `.env` and `.env.local` in the **current working directory** (`.env.local` overrides `.env`). Copy `.env.example` to get started:

```bash
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-west-2
```

Example:

```bash
photo-tools write-to-s3 C:\Users\alexb\Pictures\portfolio\ s3://my-bucket/gallery/
```

### Options

```bash
photo-tools -v get-photo-metadata photos/ output/json/
```

## Tests

With the venv activated:

```bash
pytest
pytest --cov=photo_tools --cov-report=term-missing
```

Tests marked `requires_exiftool` are skipped when ExifTool is not installed.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | User error (bad input path, invalid file type, invalid JSON) |
| 2 | Runtime dependency error (ExifTool missing or failed) |
