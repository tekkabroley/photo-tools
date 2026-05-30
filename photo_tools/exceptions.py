class PhotoToolsError(Exception):
    """Base error for photo-tools."""

    exit_code = 1


class UserError(PhotoToolsError):
    """Invalid input or usage."""

    exit_code = 1


class DependencyError(PhotoToolsError):
    """Missing runtime dependency (e.g. exiftool)."""

    exit_code = 2
