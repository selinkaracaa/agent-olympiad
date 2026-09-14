#!/usr/bin/env python3
"""Download raw PDFs for IYPT, HMMT, MCM/ICM, Fyziklani, Purple Comet, ITYM."""

import json
import os
import re
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
MANIFEST = os.path.join(ROOT, "data", "raw", "collection_manifest.json")


def curl(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 2000:
        return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    r = subprocess.run(["curl", "-sLf", "-o", dest, url], capture_output=True)
    return r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 2000


def curl_html(url):
    r = subprocess.run(["curl", "-sLf", url], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def pdf_text(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        pages = []
        for p in PdfReader(path).pages:
            pages.append(re.sub(r"\s+", " ", p.extract_text() or ""))
        return "\n".join(pages)
    except Exception:
        return ""


def count_questions(comp, path, text):
    if not text:
        return None
    if comp == "iypt":
        # "1. Title" or "Problem 1"
        nums = set(int(m) for m in re.findall(r"(?m)^\s*(\d{1,2})\.\s+[A-Z]", text))
        return max(nums) if nums else len(re.findall(r"(?m)^\s*\d{1,2}\.", text)) or None
    if comp == "itym":
        nums = set(int(m) for m in re.findall(r"(?m)^\s*(\d{1,2})\.\s+", text))
        return max(nums) if nums else None
    if comp == "fyziklani":
        nums = set(int(m) for m in re.findall(r"(?:Problem|Úloha|ÚLOHA)\s+(\d{1,2})", text, re.I))
        if not nums:
            nums = set(int(m) for m in re.findall(r"(?:FoL\.)?(\d{1,2})\s*\.", text))
        return len(nums) if nums else None
    if comp == "hmmt_team":
        nums = set(int(m) for m in re.findall(r"(?m)^\s*(\d{1,2})[\.\)]\s", text))
        return max(nums) if nums else None
    if comp == "hmmt_guts":
        # Guts sets often numbered 1-36 etc.
        nums = set(int(m) for m in re.findall(r"(?m)^\s*(\d{1,2})[\.\)]\s", text))
        return len(nums) if nums else max(nums) if nums else None
    if comp == "purple_comet":
        nums = set(int(m) for m in re.findall(r"(?m)^\s*(\d{1,2})[\.\)]\s", text))
        return max(nums) if nums else None
    if comp == "mcm_icm":
        return 1  # one problem statement per PDF
    return None


def gdrive_download(file_id, dest):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    return curl(url, dest)


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


def collect_iypt(entries):
    from pathlib import Path
    try:
        from .iypt_sources import collect_entries
    except ImportError:
        from iypt_sources import collect_entries
    collect_entries(entries, Path(ROOT))

def collect_itym(entries):
    print("ITYM...")
    base_dir = os.path.join(RAW, "itym")
    for year, fid in sorted(ITYM_DRIVE.items()):
        dest = os.path.join(base_dir, str(year), f"itym_{year}_problems.pdf")
        if gdrive_download(fid, dest):
            q = count_questions("itym", dest, pdf_text(dest))
            entries.append({"comp": "itym", "year": year, "file": dest, "questions": q, "url": f"gdrive:{fid}"})
            print(f"  {year}: ok ({q} q)")
        time.sleep(0.3)


def collect_fyziklani(entries):
    print("Fyziklani...")
    base_dir = os.path.join(RAW, "fyziklani")
    for year in range(2012, 2026):
        url = f"https://physicsbrawl.org/download/{year}/solutions.pdf"
        dest = os.path.join(base_dir, str(year), f"fyziklani_{year}_en.pdf")
        if not curl(url, dest):
            url = f"https://online.fyziklani.cz/download/{year}/solutions.pdf"
            curl(url, dest)
        if os.path.exists(dest) and os.path.getsize(dest) > 2000:
            q = count_questions("fyziklani", dest, pdf_text(dest))
            entries.append({"comp": "fyziklani", "year": year, "file": dest, "questions": q, "url": url})
            print(f"  {year}: ok ({q} q)")


def collect_hmmt(entries):
    print("HMMT...")
    base = "https://hmmt-archive.s3.amazonaws.com/tournaments"
    for year in range(2006, 2027):
        archive_id = (year - 1997) * 10
        for rnd in ("team", "guts"):
            url = f"{base}/{year}/feb/{rnd}/problems.pdf"
            dest = os.path.join(RAW, "hmmt", str(year), f"hmmt_{rnd}_{year}.pdf")
            if curl(url, dest):
                q = count_questions(f"hmmt_{rnd}", dest, pdf_text(dest))
                entries.append({"comp": f"hmmt_{rnd}", "year": year, "file": dest, "questions": q, "url": url})
                print(f"  {year} {rnd}: ok ({q} q)")
            time.sleep(0.1)


def collect_purple_comet(entries):
    print("Purple Comet...")
    for year in range(2005, 2027):
        for div in ("HS", "MS"):
            url = f"https://purplecomet.org/?action=resource/problems/629/{year}{div}Problems.pdf"
            dest = os.path.join(RAW, "purple_comet", str(year), f"purple_comet_{div.lower()}_{year}.pdf")
            if curl(url, dest):
                q = count_questions("purple_comet", dest, pdf_text(dest))
                entries.append({"comp": "purple_comet", "year": year, "division": div, "file": dest, "questions": q, "url": url})
                print(f"  {year} {div}: ok ({q} q)")
            time.sleep(0.1)


MCM_PROBS = {
    "A": "MCM_Problem_A.pdf",
    "B": "MCM_Problem_B.pdf",
    "C": "MCM_Problem_C.pdf",
    "D": "ICM_Problem_D.pdf",
    "E": "ICM_Problem_E.pdf",
    "F": "ICM_Problem_F.pdf",
}


def collect_mcm_icm(entries):
    print("MCM/ICM...")
    for year in range(2000, 2026):
        ok_any = False
        for letter, fname in MCM_PROBS.items():
            url = f"https://www.contest.comap.com/undergraduate/contests/mcm/contests/{year}/problems/{year}_{fname}"
            if year < 2010:
                url = f"https://www.contest.comap.com/undergraduate/contests/mcm/contests/{year}/problems/{fname}"
            dest = os.path.join(RAW, "mcm_icm", str(year), f"mcm_icm_{letter}_{year}.pdf")
            if curl(url, dest):
                entries.append({"comp": "mcm_icm", "year": year, "problem": letter, "file": dest, "questions": 1, "url": url})
                ok_any = True
        if ok_any:
            print(f"  {year}: ok")
        time.sleep(0.15)


def summarize(entries):
    out = {}
    for e in entries:
        comp = e["comp"]
        if comp not in out:
            out[comp] = {"sessions": 0, "questions": 0, "years": []}
        out[comp]["sessions"] += 1
        out[comp]["questions"] += e.get("questions") or 0
        out[comp]["years"].append(e.get("year"))
    return out


def main():
    entries = []
    collect_iypt(entries)
    collect_itym(entries)
    collect_fyziklani(entries)
    collect_hmmt(entries)
    collect_purple_comet(entries)
    collect_mcm_icm(entries)
    summary = summarize(entries)
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w") as f:
        json.dump({"entries": entries, "summary": summary}, f, indent=2)
    print("\n=== SUMMARY ===")
    for comp, s in sorted(summary.items()):
        print(f"{comp}: {s['sessions']} sessions, {s['questions']} questions")
    print(f"\nWrote {MANIFEST}")


if __name__ == "__main__":
    main()
