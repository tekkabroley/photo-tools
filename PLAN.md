# Implementation Plan — photo-tools CLI

Derived from [SPEC.md](./SPEC.md). No implementation until this plan is approved.

---

## Goal

Build a Python CLI (Typer) that:

1. Extracts **all available metadata** from ARW, JPG, and PNG files and writes per-file JSON.
2. Reads metadata JSON and produces YAML-frontmatter markdown files with six target fields.

---

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Metadata engine | [ExifTool](https://exiftool.org/) via [PyExifTool](https://pypi.org/project/PyExifTool/) | Only practical way to get complete metadata from ARW plus JPG/PNG EXIF/XMP/IPTC in one pipeline. Spec requires *all* metadata. |
| ExifTool binary | Required system dependency | PyExifTool wraps the `exiftool` executable. Document install in README; tests skip ARW/integration cases when binary absent. |
| JSON shape | Flat dict keyed by ExifTool tag names (string keys, JSON-serializable values) | Preserves full metadata without lossy normalization. Field mapping for markdown step reads from this dict. |
| Output filename | `{photo_stem}.json` / `{json_stem}.md` | e.g. `DSC00037.ARW` → `DSC00037.json`. Matches spec example (`DSC00037.md`). |
| Supported extensions | `.arw`, `.jpg`, `.jpeg`, `.png` (case-insensitive) | Spec lists ARW, JPG, PNG. |
| Directory walk | `pathlib` recursive glob | Walk all subdirectories; process every matching file. |
| Markdown JSON input | Files ending in `.json` when walking directories | Step 2 consumes JSON produced by step 1, not raw photos. |
| Duplicate stems | Warn and skip | When a directory walk would write the same `{stem}.json` or `{stem}.md` twice, log a warning and skip the duplicate. First encountered file wins. |
| S3 image base URL | Fixed constant | See `image` field below. |

### Field mapping (`create_metadata_markdown`)

Spec fields (note: spec typo `heigt` → `height`).

| Output field | Source |
|--------------|--------|
| `date` | Metadata — first match: `DateTimeOriginal`, `CreateDate`, `ModifyDate`, `DateCreated` |
| `image` | **Constructed** — not read from metadata. See below. |
| `location` | Metadata — composite: `Location` → `City` + `State` → `GPSPosition` → `Sub-location` |
| `collection` | Metadata — first match: `Collection`, `Keywords`, `Subject`, `Album`, `XMP:Collection` |
| `width` | Metadata — first match: `ImageWidth`, `ExifImageWidth`, `PixelXDimension` |
| `height` | Metadata — first match: `ImageHeight`, `ExifImageHeight`, `PixelYDimension` |

Missing metadata fields → empty string after the colon (key still present in frontmatter).

#### `image` URL construction

Always derived from the JSON filename stem. Extension in the URL is always `.jpg`, regardless of source photo format (ARW, PNG, etc.).

```
https://served-photos-556758165742-us-west-2-an.s3.us-west-2.amazonaws.com/gallery/{stem}.jpg
```

Example: `DSC00037.json` → `https://served-photos-556758165742-us-west-2-an.s3.us-west-2.amazonaws.com/gallery/DSC00037.jpg`

Store base URL in `constants.py` as `S3_GALLERY_BASE_URL`.

---

## Project Layout

```
photo-tools/
├── pyproject.toml              # package metadata, entry point, dev deps
├── README.md                   # install, exiftool requirement, usage examples
├── SPEC.md
├── AGENTS.md
├── PLAN.md
├── photo_tools/
│   ├── __init__.py
│   ├── __main__.py             # python -m photo_tools
│   ├── cli.py                  # Typer app + command registration
│   ├── constants.py            # extensions, field fallback maps, S3_GALLERY_BASE_URL
│   ├── paths.py                # walk helpers, output naming
│   ├── metadata/
│   │   ├── __init__.py
│   │   ├── extract.py          # ExifTool read → dict → JSON write
│   │   └── markdown.py         # JSON read → frontmatter MD write
│   └── exceptions.py           # typed errors for CLI exit codes
├── tests/
│   ├── conftest.py             # fixtures, exiftool availability marker
│   ├── fixtures/
│   │   ├── sample.jpg          # minimal JPEG with injectable EXIF (generated in conftest)
│   │   ├── sample.png
│   │   └── sample_metadata.json
│   ├── test_paths.py
│   ├── test_extract.py
│   ├── test_markdown.py
│   └── test_cli.py
└── .gitignore
```

**CLI entry point:** `photo-tools` → `photo_tools.cli:app`

**Commands:**

```bash
photo-tools get-photo-metadata  INPUT_PATH  OUTPUT_PATH
photo-tools create-metadata-markdown  INPUT_PATH  OUTPUT_PATH
```

---

## Phases

### Phase 1 — Project scaffold

**Issue:** `[Phase 1] Scaffold Python package and Typer CLI`

**Branch:** `feature/phase-1-scaffold-python-package`

**Build:**

- `pyproject.toml` with `typer`, `pyexiftool`, `pytest`, `pytest-cov`
- Package skeleton and Typer app with both commands stubbed (help text, path args)
- `README.md` with ExifTool install notes (Windows/macOS/Linux)
- `.gitignore` for `__pycache__`, `.pytest_cache`, `dist/`, `.venv/`

**Tests:**

- `test_cli.py`: `--help` exits 0; both subcommands appear in help output

---

### Phase 2 — `get_photo_metadata`

**Issue:** `[Phase 2] Implement get-photo-metadata command`

**Branch:** `feature/phase-2-get-photo-metadata`

**Build:**

- `paths.py`: resolve file vs directory; `iter_photo_files()`; ensure output dir exists; duplicate-stem tracking
- `extract.py`:
  - Single file → read metadata via ExifTool (`-json`, `-n` or equivalent for parseable output)
  - Directory → recursive walk, filter by extension
  - Write `{stem}.json` to output dir (UTF-8, pretty-printed)
  - Duplicate stem → log warning, skip file (first wins)
- Wire command in `cli.py` with Typer `Path` types and clear error messages
- Handle: missing input, non-photo file, empty directory, ExifTool not found

**Tests (write before implementation):**

| Test | Case |
|------|------|
| `test_extract_single_jpg` | JPG fixture → JSON with expected EXIF keys |
| `test_extract_single_png` | PNG fixture → JSON written |
| `test_extract_directory_recursive` | Nested dirs, multiple photos, correct output count |
| `test_extract_skips_non_photos` | `.txt` ignored |
| `test_extract_case_insensitive_ext` | `.JPG`, `.Arw` matched |
| `test_extract_missing_input` | Raises / exit 1 |
| `test_extract_creates_output_dir` | Output path created if missing |
| `test_extract_empty_directory` | No files written, exit 0 |
| `test_extract_arw` | Skipped if no exiftool; runs if available |
| `test_extract_duplicate_stem_skipped` | Two photos same stem in different subdirs → warning, one JSON written |

---

### Phase 3 — `create_metadata_markdown`

**Issue:** `[Phase 3] Implement create-metadata-markdown command`

**Branch:** `feature/phase-3-create-metadata-markdown`

**Build:**

- `markdown.py`:
  - Load JSON (single file or walk for `*.json`)
  - Map metadata fields via fallback table; blank when absent
  - Build `image` URL from JSON stem + `S3_GALLERY_BASE_URL`
  - Duplicate stem → log warning, skip file (first wins)
  - Write `{stem}.md` with `---` YAML frontmatter block (exact spec format)
- Wire command in `cli.py`

**Tests (write before implementation):**

| Test | Case |
|------|------|
| `test_markdown_all_fields_present` | Full JSON → all frontmatter fields populated |
| `test_markdown_image_url_constructed` | `DSC00037.json` → S3 URL with `DSC00037.jpg` |
| `test_markdown_missing_fields_blank` | Sparse JSON → keys present, values empty (except `image`, always set) |
| `test_markdown_duplicate_stem_skipped` | Two JSONs same stem in different subdirs → warning, one MD written |
| `test_markdown_location_composite` | City + State joined as `Portland, OR` |
| `test_markdown_single_file` | One JSON in → one MD out |
| `test_markdown_directory_walk` | Multiple JSONs in tree |
| `test_markdown_invalid_json` | Malformed input → clear error |
| `test_markdown_missing_input` | Exit 1 |
| `test_markdown_output_format` | Matches spec example structure (--- blocks, field order) |

---

### Phase 4 — Hardening and docs

**Issue:** `[Phase 4] Harden edge cases and finalize docs`

**Branch:** `feature/phase-4-hardening-and-docs`

**Build:**

- Consistent exit codes (1 user error, 2 runtime/dependency error)
- Logging at INFO for files processed (optional `-v` flag if time permits)
- README: full usage examples, field-mapping table, test instructions
- Verify `pytest` passes with coverage on core modules

**Tests:**

| Test | Case |
|------|------|
| `test_overwrite_existing_output` | Re-run overwrites JSON/MD cleanly |
| `test_unicode_filename` | Non-ASCII stem handled |
| `test_cli_integration` | End-to-end: extract JPG → create markdown |
| `test_large_nested_tree` | Many files, no duplicate outputs |

---

## Resolved Decisions

| Question | Decision |
|----------|----------|
| ExifTool as system dependency | **Yes** — use ExifTool + PyExifTool |
| Output naming | **`{stem}.json`** — e.g. `DSC00037.ARW` → `DSC00037.json` |
| `image` field | **Constructed** from S3 base URL + JSON stem + `.jpg` suffix (never read from metadata, never blank) |
| Duplicate stems in directory walk | **Warn and skip** — first file wins, subsequent duplicates logged and ignored |

---

## Test Strategy

- **Runner:** pytest
- **Fixtures:** Generate minimal JPG/PNG in `conftest.py` using Pillow; inject EXIF via `piexif` for JPG tests
- **Marker:** `@pytest.mark.requires_exiftool` for tests needing the binary
- **CI:** Run pytest; ExifTool optional job or install exiftool in CI for full suite
- **Target:** ≥90% coverage on `photo_tools/metadata/` and `photo_tools/paths.py`

---

## Dependencies

```toml
[project]
dependencies = [
  "typer>=0.12",
  "pyexiftool>=0.5",
]

[project.optional-dependencies]
dev = [
  "pytest>=8",
  "pytest-cov>=5",
  "pillow>=10",      # test fixtures only
  "piexif>=1.1",     # test fixtures only
]

[project.scripts]
photo-tools = "photo_tools.cli:app"
```

---

## Approval Checklist

- [ ] Plan reviewed and approved
- [x] Open questions answered
- [ ] GitHub issues created (one per phase)
- [ ] Implementation begins on feature branches only
