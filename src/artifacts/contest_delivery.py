"""Render immutable contestant versions; the same PDFs go to reviewers and judge."""
from dataclasses import asdict
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import json
import re

from pypdf import PdfReader
from artifact_contract import ArtifactContract
from artifacts.assets import file_sha256
from artifacts.slides import normalize_submission, _chrome_binary


class _SafeHTML(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'meta':
            metadata = dict(attrs)
            charset = (metadata.get('charset') or '').lower()
            name = (metadata.get('name') or '').lower()
            safe = (set(metadata) == {'charset'} and charset in {'utf-8', 'utf8'}) or (
                set(metadata) == {'name', 'content'} and
                name in {'viewport', 'description', 'author', 'keywords'} and
                metadata.get('content') is not None)
            if len(metadata) != len(attrs) or not safe:
                raise ValueError('Unsafe HTML metadata: only UTF-8 charset and passive named metadata are allowed')
        if tag in {'script', 'iframe', 'object', 'embed', 'base', 'link', 'form', 'input',
                   'video', 'audio', 'foreignobject'}:
            raise ValueError(f'Unsafe HTML element: {tag}')
        for name, value in attrs:
            if name == 'style' and re.search(r'url\s*\(|@import|\\', value or '', re.I):
                raise ValueError('CSS resource loading/escapes are disabled')
            if name.startswith('on') or name in {'srcdoc', 'srcset'}:
                raise ValueError(f'Unsafe HTML attribute: {name}')
            if name in {'src', 'href', 'xlink:href', 'poster', 'action', 'data'}:
                value = value or ''
                if value and not value.startswith('#') and not re.match(
                        r'^data:image/(png|jpeg|webp);base64,', value):
                    raise ValueError('Only inline raster images and fragment links are allowed')


def validate_source(content: str, contract: ArtifactContract):
    if not content.strip() or len(content) > contract.max_source_chars:
        raise ValueError('Empty or oversized artifact source')
    if contract.kind == 'slides':
        # Reject CSS escapes as well as imports/URLs; never let authored HTML read
        # local files or fetch resources while the browser renders it.
        if re.search(r'url\s*\(|@import|\\', content, re.I):
            raise ValueError('CSS resource loading/escapes are disabled')
        _SafeHTML(convert_charrefs=True).feed(content)


def preflight_renderer(contract: ArtifactContract):
    if contract.kind == 'slides':
        _chrome_binary()
    else:
        import reportlab.platypus  # noqa: F401


def _document_pdf(content: str, path: Path):
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.pagesizes import A4
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    style = getSampleStyleSheet()['BodyText']
    style.fontName, style.fontSize, style.leading = 'Helvetica', 11, 16
    story = []
    for line in content.splitlines():
        text = re.sub(r'([\u2e80-\u9fff\uf900-\ufaff\uff00-\uffef]+)',
                      r'<font name="STSong-Light">\1</font>', escape(line))
        story.append(Paragraph(text, style) if line.strip() else Spacer(1, 8))
    SimpleDocTemplate(str(path), pagesize=A4, rightMargin=48, leftMargin=48,
                      topMargin=48, bottomMargin=48).build(story)


class ArtifactRenderer:
    def __init__(self, root: Path, contract: ArtifactContract):
        self.root, self.contract = Path(root), contract
        self.latest = None

    def __call__(self, task, action, arguments):
        if action != 'render_artifact':
            raise ValueError(f'No artifact adapter for tool {action}; not executed')
        content = str(arguments['content'])
        validate_source(content, self.contract)
        digest = sha256(content.encode()).hexdigest()
        folder = self.root / digest
        receipt_path = folder / 'receipt.json'
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
            if (file_sha256(Path(receipt['pdf'])) != receipt['pdf_sha256'] or
                    file_sha256(Path(receipt['source'])) != digest):
                raise ValueError('Artifact receipt/hash mismatch')
            self.latest = receipt
            return receipt
        folder.mkdir(parents=True, exist_ok=True)
        source = folder / ('submission.html' if self.contract.kind == 'slides' else 'submission.txt')
        source.write_text(content, encoding='utf-8', newline='')
        if self.contract.kind == 'slides':
            normalized = normalize_submission(source, folder,
                min_slides=self.contract.min_pages, max_slides=self.contract.max_pages,
                max_file_size_mb=self.contract.max_file_size_mb)
            if not normalized.validation.valid:
                raise ValueError('; '.join(normalized.validation.errors))
            pdf = normalized.pdf_path
        else:
            pdf = folder / 'submission.pdf'
            _document_pdf(content, pdf)
        pages = len(PdfReader(str(pdf)).pages)
        if not self.contract.min_pages <= pages <= self.contract.max_pages:
            raise ValueError(f'Rendered page count {pages} violates delivery contract')
        if pdf.stat().st_size > self.contract.max_file_size_mb * 1024**2:
            raise ValueError('Rendered PDF exceeds file size limit')
        receipt = dict(valid=True, source=str(source.resolve()), pdf=str(pdf.resolve()),
                       source_sha256=digest, pdf_sha256=file_sha256(pdf), pages=pages,
                       contract=asdict(self.contract))
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        self.latest = receipt
        return receipt
