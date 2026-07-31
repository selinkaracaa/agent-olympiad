"""Parse PDFs into text and/or page images for agent and judge packets.

Meeting decision: there is no third special PDF path — models consume either
extracted text, page images, or both. Keep page counts within context limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pypdf import PdfReader, PdfWriter

MediaMode = Literal["text", "images", "both"]


class PdfIngestError(ValueError):
    """Raised when a PDF cannot be parsed into the requested media forms."""


@dataclass(frozen=True)
class PageImage:
    path: Path
    page_number: int  # 1-indexed
    mime_type: str = "image/png"
    width: int | None = None
    height: int | None = None


@dataclass
class ParsedPdf:
    source_pdf: Path
    page_count: int
    text: str = ""
    page_images: list[PageImage] = field(default_factory=list)
    page_start: int = 1
    page_end: int | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def effective_page_end(self) -> int:
        return self.page_end if self.page_end is not None else self.page_count


def _resolve_range(
    page_count: int,
    page_start: int | None,
    page_end: int | None,
) -> tuple[int, int]:
    start = 1 if page_start is None else page_start
    end = page_count if page_end is None else page_end
    if page_count < 1:
        raise PdfIngestError("PDF has no pages.")
    if start < 1 or end < start or end > page_count:
        raise PdfIngestError(
            f"Invalid page range {start}-{end} for {page_count}-page PDF."
        )
    return start, end


def extract_pdf_text(
    pdf_path: Path,
    *,
    page_start: int | None = None,
    page_end: int | None = None,
) -> tuple[str, int, list[str]]:
    path = Path(pdf_path)
    if not path.is_file() or path.read_bytes()[:5] != b"%PDF-":
        raise PdfIngestError(f"Not a readable PDF: {path}")
    reader = PdfReader(str(path))
    start, end = _resolve_range(len(reader.pages), page_start, page_end)
    warnings: list[str] = []
    chunks: list[str] = []
    for index in range(start - 1, end):
        page_text = reader.pages[index].extract_text() or ""
        if not page_text.strip():
            warnings.append(f"Page {index + 1} produced no extractable text.")
        chunks.append(f"--- page {index + 1} ---\n{page_text.strip()}")
    return "\n\n".join(chunks).strip(), len(reader.pages), warnings


def render_pdf_pages(
    pdf_path: Path,
    output_dir: Path,
    *,
    page_start: int | None = None,
    page_end: int | None = None,
    dpi: int = 110,
    stem: str = "page",
    image_format: str = "jpeg",
    jpeg_quality: int = 70,
    max_edge: int = 1600,
) -> tuple[list[PageImage], int]:
    """Rasterize PDF pages for multimodal upload. Requires pymupdf.

    Defaults favor API-safe sizes (JPEG + long-edge cap). Full-page PNGs at
    144 DPI can be 10MB+ each and trigger TLS EOF on large POSTs.
    """
    try:
        import fitz  # pymupdf
    except ImportError as exc:
        raise PdfIngestError(
            "pymupdf is required for page-image rendering. "
            "Install with: pip install pymupdf"
        ) from exc

    path = Path(pdf_path)
    if not path.is_file() or path.read_bytes()[:5] != b"%PDF-":
        raise PdfIngestError(f"Not a readable PDF: {path}")

    fmt = image_format.lower().strip()
    if fmt in {"jpg", "jpeg"}:
        ext, mime = "jpg", "image/jpeg"
    elif fmt == "png":
        ext, mime = "png", "image/png"
    else:
        raise PdfIngestError(f"Unsupported image_format={image_format!r} (use jpeg|png).")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    document = fitz.open(path)
    try:
        start, end = _resolve_range(document.page_count, page_start, page_end)
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)
        images: list[PageImage] = []
        for page_number in range(start, end + 1):
            page = document.load_page(page_number - 1)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            long_edge = max(pixmap.width, pixmap.height)
            if max_edge > 0 and long_edge > max_edge:
                shrink = max_edge / float(long_edge)
                pixmap = page.get_pixmap(
                    matrix=fitz.Matrix(scale * shrink, scale * shrink),
                    alpha=False,
                )
            out_path = output_dir / f"{stem}_{page_number:03d}.{ext}"
            if ext == "jpg":
                pixmap.save(str(out_path), jpg_quality=jpeg_quality)
            else:
                pixmap.save(str(out_path))
            images.append(
                PageImage(
                    path=out_path,
                    page_number=page_number,
                    mime_type=mime,
                    width=pixmap.width,
                    height=pixmap.height,
                )
            )
        return images, document.page_count
    finally:
        document.close()


def slice_pdf(
    pdf_path: Path,
    output_path: Path,
    *,
    page_start: int,
    page_end: int,
) -> Path:
    """Write a contiguous page slice to a new PDF (for question-level mode)."""
    reader = PdfReader(str(pdf_path))
    start, end = _resolve_range(len(reader.pages), page_start, page_end)
    writer = PdfWriter()
    for index in range(start - 1, end):
        writer.add_page(reader.pages[index])
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        writer.write(handle)
    return output_path


def parse_pdf(
    pdf_path: Path,
    output_dir: Path | None = None,
    *,
    media: MediaMode = "both",
    page_start: int | None = None,
    page_end: int | None = None,
    max_pages: int | None = 20,
    dpi: int = 110,
    stem: str = "page",
    image_format: str = "jpeg",
    jpeg_quality: int = 70,
    max_edge: int = 1600,
) -> ParsedPdf:
    """Parse a PDF into text and/or page images."""
    path = Path(pdf_path).resolve()
    text = ""
    warnings: list[str] = []
    page_count = len(PdfReader(str(path)).pages)
    start, end = _resolve_range(page_count, page_start, page_end)
    selected = end - start + 1
    if max_pages is not None and selected > max_pages:
        raise PdfIngestError(
            f"Selected {selected} pages exceeds max_pages={max_pages}. "
            "Use a tighter page range or raise the limit."
        )

    if media in {"text", "both"}:
        text, page_count, text_warnings = extract_pdf_text(
            path, page_start=start, page_end=end
        )
        warnings.extend(text_warnings)

    images: list[PageImage] = []
    if media in {"images", "both"}:
        if output_dir is None:
            raise PdfIngestError("output_dir is required when media includes images.")
        images, page_count = render_pdf_pages(
            path,
            Path(output_dir),
            page_start=start,
            page_end=end,
            dpi=dpi,
            stem=stem,
            image_format=image_format,
            jpeg_quality=jpeg_quality,
            max_edge=max_edge,
        )
        if media == "images" and not images:
            warnings.append("No page images were rendered.")
        total_bytes = sum(image.path.stat().st_size for image in images)
        if total_bytes > 4_000_000:
            warnings.append(
                f"Rendered page images total {total_bytes / 1_000_000:.1f} MB; "
                "large uploads can fail with SSL EOF — lower dpi/max_edge if needed."
            )

    if media == "both" and text and any("no extractable text" in w for w in warnings):
        warnings.append(
            "Some pages lack text; page images are required for those regions."
        )

    return ParsedPdf(
        source_pdf=path,
        page_count=page_count,
        text=text,
        page_images=images,
        page_start=start,
        page_end=end,
        warnings=warnings,
    )
