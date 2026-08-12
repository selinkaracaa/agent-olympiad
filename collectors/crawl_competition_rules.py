"""
Download official competition rule pages/PDFs into data/rules/sources/.

Usage:
  python collectors/crawl_competition_rules.py
  python collectors/crawl_competition_rules.py --only iol_team,icpc,purple_comet
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO = Path(__file__).resolve().parents[1]
OUT_ROOT = REPO / "data" / "rules" / "sources"
INDEX = REPO / "data" / "benchmarks" / "index.json"

# Prefer official regulations / contestant guidelines over landing pages.
SOURCE_MAP: dict[str, list[dict[str, str]]] = {
    "iol_team": [
        {"title": "IOL Regulations PDF", "url": "https://ioling.org/rules/rules.pdf"},
        {"title": "IOL Contestant Guidelines", "url": "https://ioling.org/guidelines/en/"},
    ],
    "ioaa_group": [
        {
            "title": "IOAA Organisation / Statutes",
            "url": "https://ioaastrophysics.org/about-ioaa/organisation-and-governance",
        }
    ],
    "arml_power": [
        {
            "title": "ARML Competition Rules",
            "url": "https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public",
        }
    ],
    "arml_national_team": [
        {
            "title": "ARML Competition Rules",
            "url": "https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public",
        }
    ],
    "arml_national_power": [
        {
            "title": "ARML Competition Rules",
            "url": "https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public",
        }
    ],
    "arml_local": [
        {
            "title": "ARML Competition Rules",
            "url": "https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public",
        }
    ],
    "ijso_practical": [
        {"title": "IJSO Statutes", "url": "https://ijsoweb.org/qna/IJSO-Statutes-Qatar-2019.pdf"}
    ],
    "ieo_business_case": [
        {
            "title": "IEO Regulations",
            "url": "https://files.ieo-official.org/IEO_Regulations_of_Competition.pdf",
        },
        {"title": "IEO Syllabus", "url": "https://files.ieo-official.org/IEO_Syllabus.pdf"},
    ],
    "hmmt_guts": [
        {
            "title": "HMMT Testing Information",
            "url": "https://hmmt.co/www/tournaments/testing",
        }
    ],
    "fyziklani": [
        {
            "title": "Physics Brawl Online Rules 2025",
            "url": "https://physicsbrawl.org/download/2025/rules-en-250901.pdf",
        }
    ],
    "purple_comet": [
        {"title": "Purple Comet Rules", "url": "https://purplecomet.org/rules"},
        {"title": "Purple Comet FAQ", "url": "https://purplecomet.org/faq"},
    ],
    "wsc_writing": [
        {"title": "World Scholar's Cup Events", "url": "https://scholarscup.org/events/"}
    ],
    "jessup": [{"title": "Jessup", "url": "https://www.ilsa.org/jessup/"}],
    "iiot": [{"title": "IIOT Regulations", "url": "https://iio.team/documents/Regulations.pdf"}],
    "icpc": [
        {
            "title": "ICPC docs programming environment",
            "url": "https://docs.icpc.global/worldfinals-programming-environment/",
        },
        {
            "title": "ICPC 2024 Tech Notes PDF",
            "url": "https://docs.icpc.global/wp-content/uploads/2024/08/2024-TechNotes.pdf",
        },
    ],
    "cfa_research_challenge": [
        {
            "title": "CFA Research Challenge",
            "url": "https://www.cfainstitute.org/insights/events/research-challenge",
        }
    ],
    "eoes": [
        {
            "title": "EOES Previous Olympiads",
            "url": "https://www.eoes.science/Previous%20olympiads/previous.html",
        }
    ],
    "ethics_bowl_appe": [
        {
            "title": "APPE Cases Rules Guidelines",
            "url": "https://www.appe-ethics.org/cases-rules-guidelines/",
        }
    ],
    "ethics_bowl_nhseb": [
        {"title": "NHSEB Case Library", "url": "https://nhseb.org/case-library"}
    ],
    "ichto": [{"title": "IChTo Problems", "url": "http://ichto.org/en/problems/"}],
    "pumac_power": [
        {
            "title": "PUMaC Archives",
            "url": "https://jason-shi-f9dm.squarespace.com/archives",
        }
    ],
    "vis_moot": [{"title": "Vis Moot", "url": "https://www.vismoot.org/"}],
    "wharton_investment": [
        {
            "title": "Wharton Global Youth",
            "url": "https://globalyouth.wharton.upenn.edu/",
        }
    ],
    "ccdc": [{"title": "National CCDC", "url": "https://www.nationalccdc.org/"}],
    "debatebench": [
        {"title": "DebateBench datasets portal", "url": "https://huggingface.co/datasets"}
    ],
    # University-level Global Case Competition at Harvard, not the high-school
    # Harvard Crimson Global Case Competition at casecomp.org.
    "gcch_harvard": [
        {"title": "GCCH 2026", "url": "https://www.thecasecompetition.org/gcch-2026"},
        {"title": "GCCH", "url": "https://www.thecasecompetition.org/"},
    ],
    "history_olympiad": [
        {
            "title": "History Olympiad Resources",
            "url": "https://www.historyolympiad.com/resources/",
        }
    ],
    "ioai_team": [
        {"title": "IOAI Resources", "url": "https://ioai-official.org/resources/"}
    ],
    "science_olympiad": [{"title": "Science Olympiad", "url": "https://www.soinc.org/"}],
    "wro": [{"title": "WRO Association", "url": "https://wro-association.org/"}],
    "odyssey_of_the_mind": [
        {
            "title": "Odyssey of the Mind home",
            "url": "https://www.odysseyofthemind.com/",
        }
    ],
    "wmtc": [{"title": "WMTC", "url": "https://wmtc.international/"}],
    "science_bowl": [
        {
            "title": "NSB Regional Competition Resources",
            "url": "https://science.osti.gov/wdts/nsb/Regional-Competitions/Resources",
        }
    ],
    "qanta": [{"title": "QANTA GitHub", "url": "https://github.com/Pinafore/qanta"}],
    "mystery_hunt": [{"title": "MIT Mystery Hunt", "url": "https://puzzles.mit.edu/"}],
    "nyu_ctf_bench": [
        {
            "title": "NYU CTF Bench README",
            "url": "https://github.com/NYU-LLM-CTF/NYU_CTF_Bench",
        }
    ],
    "cybench": [
        {"title": "Cybench README", "url": "https://github.com/andyzorigin/cybench"}
    ],
}


def _slug(url: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", url.split("?")[0].rstrip("/").split("/")[-1])
    return name[:80] or "index"


def _extract_pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
        import io

        reader = PdfReader(io.BytesIO(data))
        pages = []
        for page in reader.pages[:40]:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)
    except Exception as exc:  # noqa: BLE001 - crawl should continue
        return f"[pdf text extraction failed: {exc}]"


def _html_to_text(html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</p>", "\n\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch(url: str, timeout: int = 45) -> tuple[bytes, str]:
    req = Request(
        url,
        headers={
            "User-Agent": "AgentOlympiadRuleCrawler/1.0 (+research; respectful fetch)",
            "Accept": "*/*",
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read(8_000_000)
        ctype = (resp.headers.get("Content-Type") or "").lower()
    return data, ctype


def crawl_one(cid: str, sources: list[dict[str, str]]) -> dict:
    out_dir = OUT_ROOT / cid
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "competition_id": cid,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "sources": [],
    }
    for index, source in enumerate(sources, start=1):
        url = source["url"]
        title = source.get("title") or url
        entry: dict = {"title": title, "url": url, "status": "pending"}
        try:
            data, ctype = fetch(url)
            is_pdf = "pdf" in ctype or url.lower().endswith(".pdf")
            raw_name = f"{index:02d}_{_slug(url)}"
            if is_pdf and not raw_name.lower().endswith(".pdf"):
                raw_name += ".pdf"
            elif not is_pdf and not Path(raw_name).suffix:
                raw_name += ".html"
            raw_path = out_dir / raw_name
            raw_path.write_bytes(data)
            if is_pdf:
                text = _extract_pdf_text(data)
                text_path = out_dir / (raw_path.stem + ".txt")
            else:
                text = _html_to_text(data.decode("utf-8", errors="replace"))
                text_path = out_dir / (raw_path.stem + ".txt")
            text_path.write_text(text[:200_000], encoding="utf-8")
            entry.update(
                {
                    "status": "ok",
                    "content_type": ctype,
                    "bytes": len(data),
                    "raw_file": str(raw_path.relative_to(REPO)).replace("\\", "/"),
                    "text_file": str(text_path.relative_to(REPO)).replace("\\", "/"),
                    "text_chars": len(text),
                    "text_preview": text[:1500],
                }
            )
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            entry.update({"status": "error", "error": str(exc)})
        manifest["sources"].append(entry)
        time.sleep(0.4)
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="", help="Comma-separated competition ids")
    args = parser.parse_args()
    only = {item.strip() for item in args.only.split(",") if item.strip()}

    index = json.loads(INDEX.read_text(encoding="utf-8"))
    wanted = [row["id"] for row in index["olympiads"]]
    if only:
        wanted = [cid for cid in wanted if cid in only]

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    summary = {"crawled_at": datetime.now(timezone.utc).isoformat(), "competitions": {}}
    ok = err = missing = 0
    for cid in wanted:
        sources = SOURCE_MAP.get(cid)
        if not sources:
            # fall back to rule card provenance or index source_url
            rule_path = REPO / "data" / "rules" / f"{cid}.json"
            sources = []
            if rule_path.exists():
                card = json.loads(rule_path.read_text(encoding="utf-8"))
                for item in (card.get("provenance") or {}).get("sources") or []:
                    if item.get("url"):
                        sources.append(
                            {"title": item.get("title") or item["url"], "url": item["url"]}
                        )
            if not sources:
                olympiad = next(o for o in index["olympiads"] if o["id"] == cid)
                if olympiad.get("source_url"):
                    sources = [
                        {
                            "title": olympiad.get("name") or cid,
                            "url": olympiad["source_url"],
                        }
                    ]
        if not sources:
            missing += 1
            summary["competitions"][cid] = {"status": "missing_source"}
            print(f"[missing] {cid}")
            continue
        print(f"[crawl] {cid} ({len(sources)} urls)")
        manifest = crawl_one(cid, sources)
        statuses = [s["status"] for s in manifest["sources"]]
        if any(s == "ok" for s in statuses):
            ok += 1
        else:
            err += 1
        summary["competitions"][cid] = {
            "status": "ok" if "ok" in statuses else "error",
            "sources": statuses,
        }

    summary_path = OUT_ROOT / "crawl_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"done ok={ok} error={err} missing={missing} summary={summary_path}")


if __name__ == "__main__":
    main()
