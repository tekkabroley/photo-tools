"""Upload files to Amazon S3 using credentials from .env / .env.local."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

from photo_tools.exceptions import DependencyError, UserError
from photo_tools.paths import iter_all_files

logger = logging.getLogger(__name__)

_REQUIRED_ENV_VARS = ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY")


def load_env_files() -> None:
    """Load .env then .env.local from the current working directory."""
    cwd = Path.cwd()
    load_dotenv(cwd / ".env")
    load_dotenv(cwd / ".env.local", override=True)


def _require_credentials() -> None:
    missing = [name for name in _REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        raise UserError(
            "Missing S3 credentials. Set "
            + ", ".join(missing)
            + " in .env or .env.local (see .env.example)."
        )


def parse_s3_path(s3_path: str) -> tuple[str, str]:
    """Parse s3://bucket/prefix into bucket name and key prefix."""
    parsed = urlparse(s3_path)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise UserError(
            f"Invalid S3 path: {s3_path!r}. Expected format: s3://bucket-name/optional/prefix"
        )

    bucket = parsed.netloc
    prefix = parsed.path.lstrip("/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"
    return bucket, prefix


def object_key_for_file(
    file_path: Path,
    input_path: Path,
    key_prefix: str,
    *,
    single_file_input: bool,
) -> str:
    """Build the S3 object key for a local file."""
    if single_file_input:
        relative = file_path.name
    else:
        relative = file_path.relative_to(input_path).as_posix()

    return f"{key_prefix}{relative}" if key_prefix else relative


def upload_to_s3(input_path: Path, s3_path: str) -> int:
    """Upload one file or a directory tree to S3. Returns count of files uploaded."""
    if not input_path.exists():
        raise UserError(f"Input path does not exist: {input_path}")

    load_env_files()
    _require_credentials()

    bucket, key_prefix = parse_s3_path(s3_path)
    files = list(iter_all_files(input_path))
    if not files:
        logger.warning("No files found under %s", input_path)
        return 0

    try:
        client = boto3.client("s3")
    except BotoCoreError as exc:
        raise DependencyError(f"Failed to create S3 client: {exc}") from exc

    single_file_input = input_path.is_file()
    uploaded = 0
    for file_path in files:
        key = object_key_for_file(
            file_path, input_path, key_prefix, single_file_input=single_file_input
        )
        try:
            client.upload_file(str(file_path), bucket, key)
        except (BotoCoreError, ClientError) as exc:
            raise DependencyError(
                f"Failed to upload {file_path} to s3://{bucket}/{key}: {exc}"
            ) from exc
        logger.info("Uploaded %s -> s3://%s/%s", file_path, bucket, key)
        uploaded += 1

    return uploaded
