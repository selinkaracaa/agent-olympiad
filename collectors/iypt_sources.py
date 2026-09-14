"""Collect edition-verified IYPT sources from the publisher's problem index.

The tournament year comes from the content heading, never an upload directory.
Historical HTML editions retain their illustrations when no matching PDF exists.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import fitz
import requests

ROOT = Path(__file__).resolve().parents[1]
INDEX_URL = "https://iypt.org/problems/"
SOURCE_DIR = Path("data/raw/iypt/verified")
YEAR_RE = re.compile(r"Problems\s+for\s+the\s+\d+(?:st|nd|rd|th)?\s+IYPT\s*\(?\s*(\d{4})", re.I)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def title_year(text: str) -> int | None:
    match = YEAR_RE.search(text[:1500])
    return int(match.group(1)) if match else None


def normalize_legacy_encoding(text: str) -> str:
    """Undo only valid UTF-8 byte sequences misdecoded as Latin-1/Windows-1252.

    Correct Unicode (including mathematical notation) is preserved. The original
    publisher response remains archived separately, so this repair is traceable.
    """
    def byte(char):
        if ord(char) < 256:
            return ord(char)
        try:
            return char.encode("cp1252")[0]
        except UnicodeEncodeError:
            return None
    for _ in range(2):
        result, i = [], 0
        while i < len(text):
            lead = byte(text[i])
            length = 2 if lead is not None and 0xC2 <= lead <= 0xDF else 3 if lead is not None and 0xE0 <= lead <= 0xEF else 4 if lead is not None and 0xF0 <= lead <= 0xF4 else 0
            values = [byte(c) for c in text[i:i+length]] if length else []
            if length and len(values) == length and all(v is not None and 0x80 <= v <= 0xBF for v in values[1:]):
                try:
                    result.append(bytes(values).decode("utf-8"))
                    i += length
                    continue
                except UnicodeDecodeError:
                    pass
            result.append(text[i])
            i += 1
        repaired = "".join(result)
        if repaired == text:
            break
        text = repaired
    return text


def get(url: str) -> requests.Response:
    response = requests.get(url, timeout=(10, 30), headers={"User-Agent": "AgentOlympiad-source-audit/1.0"})
    response.raise_for_status()
    return response


def asset(path: Path, root: Path, mime: str, role: str = "agent_visible") -> dict:
    return dict(path=path.relative_to(root).as_posix(), mime_type=mime,
                role=role, sha256=digest(path.read_bytes()))


def edition_links(content: bytes) -> dict[int, str]:
    soup = BeautifulSoup(content, "html.parser")
    article = soup.select_one(".entry-content")
    if article is None:
        raise ValueError("IYPT index has no article; refusing navigation-link fallback")
    links = {}
    for link in article.select("a[href]"):
        label = link.get_text(" ", strip=True)
        if re.fullmatch(r"(?:19|20)\d{2}", label):
            links[int(label)] = urljoin(INDEX_URL, link["href"])
    if len(links) < 30:
        raise ValueError("IYPT year index unexpectedly incomplete")
    return links


def collect_one(root: Path, year: int, url: str) -> dict:
    response = get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    article = soup.select_one(".entry-content")
    if article is None:
        raise ValueError(f"{year}: no article body")
    headings = "\n".join(h.get_text(" ", strip=True) for h in article.select("h1,h2,h3"))
    if title_year(headings) != year:
        raise ValueError(f"{year}: article edition mismatch: {headings[:180]}")
    folder = root / SOURCE_DIR / str(year)
    folder.mkdir(parents=True, exist_ok=True)
    snapshot = folder / "publisher_page.html"
    snapshot.write_bytes(response.content)
    article = BeautifulSoup(normalize_legacy_encoding(str(article)), "html.parser")
    pdf_candidates = [urljoin(response.url, a["href"]) for a in article.select("a[href]")
                      if urlparse(a["href"]).path.lower().endswith(".pdf")]
    for pdf_url in pdf_candidates:
        # A sidebar PDF for the current edition must never replace this edition.
        if str(year) not in Path(urlparse(pdf_url).path).name:
            continue
        try:
            pdf_response = get(pdf_url)
        except requests.RequestException:
            # The publisher retains historical HTML after moving old PDF URLs.
            continue
        if not pdf_response.content.startswith(b"%PDF-"):
            continue
        with fitz.open(stream=pdf_response.content, filetype="pdf") as document:
            text = "\n\n".join(page.get_text(sort=True) for page in document)
            pages = len(document)
        if title_year(text) != year:
            continue
        target = folder / f"iypt_{year}_problems.pdf"
        target.write_bytes(pdf_response.content)
        return dict(year=year, source_url=pdf_response.url, edition_page=response.url,
                    source_file=target.relative_to(root).as_posix(), problem_description=text.strip(),
                    format="publisher_pdf", pages=pages, title_year=year,
                    assets=[asset(target, root, "application/pdf")],
                    publisher_snapshot=asset(snapshot, root, "text/html", "judge_only"))

    for tag in article.select("script,style,iframe,form,nav"):
        tag.decompose()
    images = []
    for tag in article.select("img"):
        image_url = urljoin(response.url, tag.get("src", ""))
        if urlparse(image_url).scheme not in ("http", "https"):
            raise ValueError(f"{year}: unsupported illustration URL")
        image_response = get(image_url)
        mime = image_response.headers.get("Content-Type", "").split(";")[0]
        if not mime.startswith("image/"):
            raise ValueError(f"{year}: illustration is not an image: {image_url}")
        extension = Path(urlparse(image_url).path).suffix or ".img"
        target = folder / "images" / (digest(image_response.content)[:16] + extension)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(image_response.content)
        tag["src"] = target.relative_to(folder).as_posix()
        for attr in ("srcset", "sizes", "loading", "data-src"):
            tag.attrs.pop(attr, None)
        image_asset = asset(target, root, mime)
        image_asset["source_url"] = image_response.url
        images.append(image_asset)
    for tag in article.find_all(True):
        for key in list(tag.attrs):
            if key.lower().startswith("on"):
                del tag.attrs[key]
        if tag.name == "a" and tag.get("href"):
            tag["href"] = urljoin(response.url, tag["href"])
    text = article.get_text("\n", strip=True)
    if title_year(text) != year or len(text) < 500:
        raise ValueError(f"{year}: incomplete article text")
    target = folder / f"iypt_{year}_problems.html"
    target.write_text('<!doctype html><html lang="en"><meta charset="utf-8">'
                      f'<title>IYPT {year} problems</title><body>{article}</body></html>\n', encoding="utf-8")
    return dict(year=year, source_url=response.url, edition_page=response.url,
                source_file=target.relative_to(root).as_posix(), problem_description=text,
                format="publisher_html_with_local_images", title_year=year,
                assets=[asset(target, root, "text/html"), *images],
                publisher_snapshot=asset(snapshot, root, "text/html", "judge_only"))


def collect_sources(root: Path = ROOT, years=range(1988, 2027), *, refresh=False) -> dict:
    root = root.resolve()
    manifest_path = root / SOURCE_DIR / "manifest.json"
    previous = []
    if manifest_path.exists() and not refresh:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        requested = set(years)
        previous = [s for s in manifest["sources"] if s["year"] in requested]
        for source in previous:
            if title_year(source["problem_description"]) != source["year"]:
                raise ValueError("Cached IYPT manifest has a year mismatch")
            for a in source["assets"]:
                if digest((root / a["path"]).read_bytes()) != a["sha256"]:
                    raise ValueError(f"Changed cached source: {a['path']}")
            if source["format"] == "publisher_html_with_local_images":
                target = root / source["source_file"]
                raw_text = target.read_text(encoding="utf-8")
                repaired = normalize_legacy_encoding(raw_text)
                if repaired != raw_text:
                    target.write_text(repaired, encoding="utf-8")
                    source["assets"][0]["sha256"] = digest(target.read_bytes())
                    source["problem_description"] = normalize_legacy_encoding(source["problem_description"])
                    source["encoding_normalization"] = "Reversible UTF-8 mojibake repair; original publisher bytes retained in publisher_page.html."
        if {s["year"] for s in previous} == requested and not manifest.get("errors"):
            manifest["sources"] = previous
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return manifest
    index_response = get(INDEX_URL)
    links = edition_links(index_response.content)
    sources, errors = list(previous), []
    completed = {s["year"] for s in sources}
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = {pool.submit(collect_one, root, year, links[year]): year
                for year in years if year in links and year not in completed}
        for job in as_completed(jobs):
            year = jobs[job]
            try:
                source = job.result()
                sources.append(source)
                print(f"IYPT {year}: {source['format']}", flush=True)
            except Exception as exc:
                errors.append(dict(year=year, error=str(exc)))
                print(f"IYPT {year}: ERROR {exc}", flush=True)
    errors.extend(dict(year=y, error="Edition absent from publisher index") for y in years if y not in links)
    hashes = [s["assets"][0]["sha256"] for s in sources]
    if len(hashes) != len(set(hashes)):
        raise ValueError("Different IYPT editions returned identical source files")
    manifest = dict(source_index=INDEX_URL, source_index_sha256=digest(index_response.content),
                    year_policy="content heading, not publication/upload year",
                    sources=sorted(sources, key=lambda s: s["year"]), errors=errors)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def collect_entries(entries: list, root: Path = ROOT) -> None:
    manifest = collect_sources(root)
    if manifest["errors"]:
        raise RuntimeError(f"IYPT collection incomplete: {manifest['errors']}")
    entries.extend(dict(comp="iypt", year=s["year"], file=str(root / s["source_file"]),
                        url=s["source_url"], questions=len(set(re.findall(r"(?m)^\s*(\d{1,2})[.)]\s", s["problem_description"]))))
                   for s in manifest["sources"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    result = collect_sources(refresh=args.refresh)
    print(json.dumps(dict(editions=len(result["sources"]), errors=result["errors"])))
    raise SystemExit(bool(result["errors"]))
