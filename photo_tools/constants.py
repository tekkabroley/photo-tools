"""Shared constants for photo-tools."""

PHOTO_EXTENSIONS = frozenset({".arw", ".jpg", ".jpeg", ".png"})

S3_GALLERY_BASE_URL = (
    "https://served-photos-556758165742-us-west-2-an.s3.us-west-2.amazonaws.com/gallery"
)

DATE_FIELD_CANDIDATES = (
    "DateTimeOriginal",
    "CreateDate",
    "ModifyDate",
    "DateCreated",
)

LOCATION_FIELD_CANDIDATES = ("Location",)

COLLECTION_FIELD_CANDIDATES = (
    "Collection",
    "Keywords",
    "Subject",
    "Album",
)

WIDTH_FIELD_CANDIDATES = (
    "ImageWidth",
    "ExifImageWidth",
    "PixelXDimension",
)

HEIGHT_FIELD_CANDIDATES = (
    "ImageHeight",
    "ExifImageHeight",
    "PixelYDimension",
)

FRONTMATTER_FIELD_ORDER = (
    "date",
    "image",
    "location",
    "collection",
    "width",
    "height",
)
