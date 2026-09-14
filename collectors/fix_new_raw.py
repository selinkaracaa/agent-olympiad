#!/usr/bin/env python3
"""Fix and complete raw PDF collection; write manifest with counts."""

import json
import os
import re
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
MANIFEST = os.path.join(RAW, "collection_manifest.json")

ITYM_DRIVE = {
    2025: "19StPp71NrAk2FyhgWqShvVvVvg9Rdkvm",
    2024: "1MSNwiIVsNvlKRkq8kE9VPY8tl09E-NTQ",
    2023: "18bb4AIG6yYeVYVargetR6eIWWX1oVWwH",
    2022: "1ypSNgCPzNzEPNJmk5tSG44GSgkY-D8cY",
    2021: "1DiKFv6NmERgC79FLExT0X5uhefYv8gqK",
    2020: "1R7d6mST4gWFIc1dE38ZloIBaXalNU4ic",
    2019: "13jlVoQSltOPEpXDsdkhsV-BRZunPe1_D",
    2018: "1kQZAUi4DYF6KimPxaWkLPf8HoiBc03wX",
    2017: "1nBpiEQPrUDzYWld8oW614oseFHhE5l-c",
    2016: "1-oZe97QESsGG7gHd9LmbkyVgDbE7rcCc",
    2015: "1VEawHchHG2OrQLWtGXPHVE0YvtgJiIBF",
    2014: "1BU4dNXWMYf3Gb8RVYYfZQEEvxqmn-UJJ",
    2013: "1bkcY-aw-0B7J7iKz2vwAaZhmUyKHDctI",
    2012: "1oF4Bhg1bofoEg_8VVMTwPVGzwWqgAo3c",
    2011: "1dmJQo06BFugSSpzS0hqgGqzeBPNaLf4y",
    2010: "1oLG57gJ2SseDEewxLivckBvG5MEkuw3q",
    2009: "1qNhEJ3n9HwbJPBNeyUoAIBJT3EMQ5iGF",
}

MCM_FILES = {
    "A": ("MCM", "MCM_Problem_A.pdf"),
    "B": ("MCM", "MCM_Problem_B.pdf"),
    "C": ("MCM", "MCM_Problem_C.pdf"),
    "D": ("ICM", "ICM_Problem_D.pdf"),
    "E": ("ICM", "ICM_Problem_E.pdf"),
    "F": ("ICM", "ICM_Problem_F.pdf"),
}


def curl(url, dest, min_size=5000):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    r = subprocess.run(["curl", "-sLf", "-o", dest, url], capture_output=True)
    if r.returncode != 0 or not os.path.exists(dest) or os.path.getsize(dest) < min_size:
        if os.path.exists(dest):
            os.remove(dest)
        return False
    with open(dest, "rb") as f:
        if f.read(4) != b"%PDF":
            os.remove(dest)
            return False
    return True


def curl_html(url):
    r = subprocess.run(["curl", "-sLf", url], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def pdf_text(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    except Exception:
        return ""


def count(comp, text):
    if not text:
        return None
    if comp == "iypt":
        nums = {int(m) for m in re.findall(r"(?m)(?:^|\n)\s*(\d{1,2})\.\s+[A-Za-z]", text)}
        return max(nums) if nums else 17
    if comp == "itym":
        nums = {int(m) for m in re.findall(r"(?m)(?:^|\n)\s*(\d{1,2})\.\s+[A-Z]", text)}
        return max(nums) if nums else None
    if comp == "fyziklani":
        nums = {int(m) for m in re.findall(r"Problem\s+(\d{1,2})", text, re.I)}
        return len(nums) if nums else None
    if comp == "hmmt_team":
        nums = {int(m) for m in re.findall(r"(?m)^\s*(\d{1,2})\.\s*\[", text)}
        if not nums:
            nums = {int(m) for m in re.findall(r"(?m)^\s*(\d{1,2})\.\s+", text)}
        return max(nums) if nums else 10
    if comp == "hmmt_guts":
        nums = {int(m) for m in re.findall(r"(?m)^\s*(\d{1,2})[\.\)]\s", text)}
        return len(nums) if nums else 36
    if comp == "purple_comet":
        nums = {int(m) for m in re.findall(r"(?m)^\s*(\d{1,2})[\.\)]\s", text)}
        return max(nums) if nums else 30
    if comp == "mcm_icm":
        return 1
    return None


def collect_iypt(entries):
    from pathlib import Path
    try:
        from .iypt_sources import collect_entries
    except ImportError:
        from iypt_sources import collect_entries
    collect_entries(entries, Path(ROOT))

def collect_purple_comet(entries):
    print("Purple Comet...")
    base = os.path.join(RAW, "purple_comet")
    for year in range(2005, 2027):
        for div, tag in (("HS", "hs"), ("MS", "ms")):
            url = f"https://purplecomet.org/files/{year}{div}_English.pdf"
            dest = os.path.join(base, str(year), f"purple_comet_{tag}_{year}.pdf")
            if curl(url, dest):
                q = count("purple_comet", pdf_text(dest))
                entries.append({"comp": "purple_comet", "year": year, "division": div, "file": dest, "questions": q})
                print(f"  {year} {div}: {q} q")
            time.sleep(0.05)


def collect_mcm_icm(entries):
    print("MCM/ICM...")
    base = os.path.join(RAW, "mcm_icm")
    for year in range(2000, 2026):
        got = 0
        for letter, (kind, fname) in MCM_FILES.items():
            urls = [
                f"https://www.contest.comap.com/undergraduate/contests/mcm/contests/{year}/problems/{year}_{kind}_Problem_{letter}.pdf",
                f"https://www.contest.comap.com/undergraduate/contests/mcm/contests/{year}/problems/{fname}",
                f"https://www.contest.comap.com/undergraduate/contests/mcm/contests/{year}/problems/{year}_{fname}",
            ]
            dest = os.path.join(base, str(year), f"mcm_icm_{letter}_{year}.pdf")
            for url in urls:
                if curl(url, dest, min_size=2000):
                    entries.append({"comp": "mcm_icm", "year": year, "problem": letter, "file": dest, "questions": 1})
                    got += 1
                    break
        if got:
            print(f"  {year}: {got} problems")


def scan_existing(entries):
    """Re-count PDFs already on disk."""
    specs = [
        ("fyziklani", "fyziklani_*.pdf"),
        ("hmmt_team", "hmmt_team_*.pdf"),
        ("hmmt_guts", "hmmt_guts_*.pdf"),
        ("itym", "itym_*_problems.pdf"),
    ]
    for comp, pattern in specs:
        root = os.path.join(RAW, comp.split("_")[0] if comp.startswith("hmmt") else comp)
        if not os.path.isdir(root):
            continue
        for dirpath, _, files in os.walk(root):
            for fn in files:
                if not fn.endswith(".pdf"):
                    continue
                path = os.path.join(dirpath, fn)
                if os.path.getsize(path) < 5000:
                    continue
                with open(path, "rb") as f:
                    if f.read(4) != b"%PDF":
                        continue
                year_m = re.search(r"(20\d{2}|19\d{2})", fn) or re.search(r"/(\d{4})/", path)
                year = int(year_m.group(1)) if year_m else None
                if comp == "hmmt_team" and "team" not in fn:
                    continue
                if comp == "hmmt_guts" and "guts" not in fn:
                    continue
                q = count(comp.replace("hmmt_", "hmmt_") if comp.startswith("hmmt") else comp, pdf_text(path))
                entries.append({"comp": comp, "year": year, "file": path, "questions": q})


def summarize(entries):
    out = {}
    for e in entries:
        comp = e["comp"]
        out.setdefault(comp, {"sessions": 0, "questions": 0})
        out[comp]["sessions"] += 1
        out[comp]["questions"] += e.get("questions") or 0
    return out


def main():
    entries = []
    collect_iypt(entries)
    collect_purple_comet(entries)
    collect_mcm_icm(entries)
    scan_existing(entries)
    summary = summarize(entries)
    with open(MANIFEST, "w") as f:
        json.dump({"entries": entries, "summary": summary}, f, indent=2)
    print("\n=== SUMMARY ===")
    for comp, s in sorted(summary.items()):
        print(f"{comp}: {s['sessions']} sessions, {s['questions']} questions")


if __name__ == "__main__":
    main()
