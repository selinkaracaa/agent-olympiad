"""Validate HTML/PDF slide decks and normalize them to an auditable PDF."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

from pypdf import PdfReader

CHROME_CANDIDATES = (
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/chromium"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
)

PRINT_CSS = """
<style id="olympiad-print-contract">
@page { size: 13.333333in 7.5in; margin: 0; }
html, body { margin: 0; padding: 0; }
section {
  box-sizing: border-box;
  width: 13.333333in;
  height: 7.5in;
  overflow: hidden;
  break-after: page;
  page-break-after: always;
}
section:last-of-type { break-after: auto; page-break-after: auto; }
.speaker-notes, [data-speaker-notes] { display: none !important; }
</style>
"""


@dataclass
class ArtifactValidation:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class NormalizedSubmission:
    source_path: Path
    source_mime_type: str
    pdf_path: Path
    validation: ArtifactValidation


class _SlideHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.section_depth = 0
        self.slide_count = 0
        self.slide_has_heading: list[bool] = []
        self.has_script = False
        self.has_video = False
        self.remote_assets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "section":
            self.section_depth += 1
            self.slide_count += 1
            self.slide_has_heading.append(False)
        elif tag in {"h1", "h2"} and self.section_depth and self.slide_has_heading:
            self.slide_has_heading[-1] = True
        elif tag == "script":
            self.has_script = True
        elif tag in {"video", "audio", "iframe"}:
            self.has_video = True

        for key in ("src", "href", "poster"):
            value = attrs_dict.get(key) or ""
            if re.match(r"^(?:https?:)?//", value, re.IGNORECASE):
                self.remote_assets.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag == "section" and self.section_depth:
            self.section_depth -= 1


def validate_html_slides(
    html: str,
    *,
    min_slides: int = 1,
    max_slides: int = 20,
) -> ArtifactValidation:
    parser = _SlideHTMLParser()
    parser.feed(html)
    errors: list[str] = []
    warnings: list[str] = []

    if parser.slide_count < min_slides:
        errors.append(f"Deck has {parser.slide_count} slides; minimum is {min_slides}.")
    if parser.slide_count > max_slides:
        errors.append(f"Deck has {parser.slide_count} slides; maximum is {max_slides}.")
    missing_titles = [
        index + 1 for index, has_heading in enumerate(parser.slide_has_heading) if not has_heading
    ]
    if missing_titles:
        errors.append(f"Slides missing an h1/h2 title: {missing_titles}")
    if parser.has_script:
        errors.append("Scripts are not allowed in slide submissions.")
    if parser.has_video:
        errors.append("Video, audio, and iframe elements are not allowed.")
    if parser.remote_assets:
        errors.append("External network assets are not allowed.")
    if re.search(r"@keyframes|animation\s*:", html, re.IGNORECASE):
        errors.append("CSS animations are not allowed.")
    if "<svg" not in html.lower():
        warnings.append("No inline SVG visualizations detected.")

    return ArtifactValidation(
        valid=not errors,
        errors=errors,
        warnings=warnings,
        metadata={
            "slide_count": parser.slide_count,
            "missing_title_slides": missing_titles,
            "remote_asset_count": len(parser.remote_assets),
        },
    )


def _chrome_binary() -> Path:
    for candidate in CHROME_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise RuntimeError("Chrome/Chromium is required to render HTML slides to PDF.")


def _inject_print_contract(html: str) -> str:
    if "</head>" in html.lower():
        index = html.lower().rfind("</head>")
        return f"{html[:index]}{PRINT_CSS}{html[index:]}"
    return f"<!doctype html><html><head>{PRINT_CSS}</head><body>{html}</body></html>"


def render_html_to_pdf(html: str, output_path: str | Path) -> Path:
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    chrome = _chrome_binary()

    with tempfile.TemporaryDirectory(prefix="olympiad-slides-") as temp_dir:
        temp = Path(temp_dir)
        html_path = temp / "deck.html"
        html_path.write_text(_inject_print_contract(html), encoding="utf-8")
        command = [
            str(chrome),
            "--headless=new",
            "--disable-gpu",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-sync",
            "--metrics-recording-only",
            "--no-first-run",
            "--no-pdf-header-footer",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=1000",
            f"--user-data-dir={temp / 'chrome-profile'}",
            f"--print-to-pdf={output}",
            html_path.as_uri(),
        ]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if output.is_file() and output.stat().st_size > 5:
                break
            if process.poll() is not None:
                break
            time.sleep(0.1)

        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        stdout, stderr = process.communicate()
        if not output.is_file() or output.stat().st_size <= 5:
            detail = (stderr or stdout or "renderer timed out without a PDF").strip()
            raise RuntimeError(f"HTML-to-PDF rendering failed: {detail}")
    return output


def validate_pdf_slides(
    pdf_path: str | Path,
    *,
    max_file_size_mb: int = 20,
    expected_aspect_ratio: float = 16 / 9,
    ratio_tolerance: float = 0.04,
) -> ArtifactValidation:
    path = Path(pdf_path)
    errors: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return ArtifactValidation(False, errors=[f"Missing PDF: {path}"])
    if path.read_bytes()[:5] != b"%PDF-":
        return ArtifactValidation(False, errors=[f"Not a valid PDF header: {path}"])

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_file_size_mb:
        errors.append(f"PDF is {size_mb:.2f} MB; maximum is {max_file_size_mb} MB.")

    try:
        reader = PdfReader(str(path))
        page_count = len(reader.pages)
        invalid_pages = []
        for index, page in enumerate(reader.pages, start=1):
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            ratio = max(width, height) / min(width, height) if min(width, height) else 0
            if width <= height or abs(ratio - expected_aspect_ratio) > ratio_tolerance:
                invalid_pages.append(index)
        if invalid_pages:
            errors.append(f"Pages are not landscape 16:9: {invalid_pages}")
    except Exception as exc:
        return ArtifactValidation(False, errors=[f"Unreadable PDF: {exc}"])

    return ArtifactValidation(
        valid=not errors,
        errors=errors,
        warnings=warnings,
        metadata={"page_count": page_count, "size_mb": round(size_mb, 4)},
    )


def normalize_submission(
    source_path: str | Path,
    output_dir: str | Path,
    *,
    min_slides: int = 1,
    max_slides: int = 20,
    max_file_size_mb: int = 20,
) -> NormalizedSubmission:
    source = Path(source_path).resolve()
    destination_dir = Path(output_dir).resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)
    normalized_pdf = destination_dir / "submission.pdf"

    if source.suffix.lower() in {".html", ".htm"}:
        html = source.read_text(encoding="utf-8")
        html_validation = validate_html_slides(
            html, min_slides=min_slides, max_slides=max_slides
        )
        if not html_validation.valid:
            return NormalizedSubmission(source, "text/html", normalized_pdf, html_validation)
        render_html_to_pdf(html, normalized_pdf)
        pdf_validation = validate_pdf_slides(
            normalized_pdf, max_file_size_mb=max_file_size_mb
        )
        pdf_validation.warnings = html_validation.warnings + pdf_validation.warnings
        pdf_validation.metadata = {
            **html_validation.metadata,
            **pdf_validation.metadata,
        }
        return NormalizedSubmission(source, "text/html", normalized_pdf, pdf_validation)

    if source.suffix.lower() == ".pdf":
        if source != normalized_pdf:
            shutil.copy2(source, normalized_pdf)
        validation = validate_pdf_slides(
            normalized_pdf, max_file_size_mb=max_file_size_mb
        )
        return NormalizedSubmission(source, "application/pdf", normalized_pdf, validation)

    return NormalizedSubmission(
        source,
        "application/octet-stream",
        normalized_pdf,
        ArtifactValidation(False, errors=["Submission must be HTML or PDF."]),
    )
