"""Render the reviewed local HTML/PDF assets, without editing PDF originals."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from repair_mystery_hunt_sources_20260913 import CACHE, SELECTED

cache = ROOT / CACHE
rendered = cache / "renders"
rendered.mkdir(parents=True, exist_ok=True)
chrome = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
profile = cache / "chrome_review_profile"
heights = {"mystery_hunt_00002": 700, "mystery_hunt_00003": 700,
           "mystery_hunt_00004": 850, "mystery_hunt_00006": 850,
           "mystery_hunt_00007": 1600, "mystery_hunt_00014": 1800,
           "mystery_hunt_00028": 4300, "mystery_hunt_00032": 1000,
           "mystery_hunt_00033": 1600, "mystery_hunt_00035": 700,
           "mystery_hunt_00036": 1700, "mystery_hunt_00038": 1000,
           "mystery_hunt_00044": 2300, "mystery_hunt_00819": 1700}
for pid in sorted(SELECTED):
    page = cache / "prepared" / pid / "input/puzzle.html"
    output = rendered / (pid + ".png")
    proc = subprocess.run([str(chrome), "--headless=new", "--disable-gpu", "--disable-extensions",
        "--no-first-run", "--no-default-browser-check", "--disable-background-networking",
        "--user-data-dir=" + str(profile), "--hide-scrollbars", "--force-device-scale-factor=1",
        "--screenshot=" + str(output), "--window-size=1400," + str(heights[pid]),
        "--virtual-time-budget=1000", page.as_uri()], capture_output=True, timeout=45)
    if proc.returncode or not output.is_file():
        raise RuntimeError(proc.stderr.decode(errors="replace"))
    print(pid, output.stat().st_size, flush=True)
poppler = next((ROOT / "data/.cache/science_olympiad_repair_20260913/poppler").rglob("pdftoppm.exe"))
for pdf in (cache / "prepared").rglob("*.pdf"):
    subprocess.run([str(poppler), "-r", "110", "-png", str(pdf), str(rendered / pdf.stem)], check=True, capture_output=True)
    print(pdf.name, "rendered with Poppler", flush=True)
