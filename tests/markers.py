"""Shared pytest markers for the test suite."""

import shutil

import pytest

requires_exiftool = pytest.mark.skipif(
    shutil.which("exiftool") is None,
    reason="exiftool binary not installed",
)
