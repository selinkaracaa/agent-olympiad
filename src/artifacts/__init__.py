"""Artifact loading, validation, and normalization."""

from .assets import Asset, AssetError, load_assets
from .pdf_ingest import (
    MediaMode,
    PageImage,
    ParsedPdf,
    PdfIngestError,
    extract_pdf_text,
    parse_pdf,
    render_pdf_pages,
    slice_pdf,
)
from .slides import (
    ArtifactValidation,
    NormalizedSubmission,
    normalize_submission,
    validate_html_slides,
    validate_pdf_slides,
)

__all__ = [
    "ArtifactValidation",
    "Asset",
    "AssetError",
    "MediaMode",
    "NormalizedSubmission",
    "PageImage",
    "ParsedPdf",
    "PdfIngestError",
    "extract_pdf_text",
    "load_assets",
    "normalize_submission",
    "parse_pdf",
    "render_pdf_pages",
    "slice_pdf",
    "validate_html_slides",
    "validate_pdf_slides",
]
