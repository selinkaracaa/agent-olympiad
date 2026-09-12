import csv
import json
from collections import defaultdict
from pathlib import Path


def util(sess: Path):
    d = json.loads(sess.read_text(encoding="utf-8"))
    m = d.get("metrics") or {}
    g = d.get("grade") or {}
    u = m.get("task_utility")
    if u is None:
        u = g.get("task_utility")
    if u is None:
        sc, mx = g.get("score"), g.get("max_score")
        if sc is not None and mx:
            u = float(sc) / float(mx)
    return None if u is None else float(u)


def competition_of(pid: str) -> str:
    if pid.startswith("arml_national_power"):
        return "arml_national_power"
    if pid.startswith("arml_national_team"):
        return "arml_national_team"
    if pid.startswith("arml_power"):
        return "arml_power"
    if pid.startswith("arml_local"):
        return "arml_local"
    return "other"


def load(root: str):
    root_p = Path(root)
    rows = []
    summary = root_p / "summary.tsv"
    if summary.exists():
        for r in csv.DictReader(summary.open(encoding="utf-8"), delimiter="\t"):
            if r.get("status") not in {"ok", "skipped_complete", ""}:
                continue
            pid = r["problem_id"]
            cid = r.get("competition_id") or competition_of(pid)
            sess = root_p / pid / "contest_session.json"
            if sess.exists():
                u = util(sess)
            elif r.get("task_utility") not in (None, ""):
                u = float(r["task_utility"])
            else:
                u = None
            rows.append((cid, pid, u))
        return rows
    for sess in sorted(root_p.glob("*/contest_session.json")):
        pid = sess.parent.name
        rows.append((competition_of(pid), pid, util(sess)))
    return rows


otc = load("results/arml_all_protocol_v3_otc_20260909")
van = load("results/arml_all_protocol_v3_vanilla_20260909")
van_by = {pid: (cid, u) for cid, pid, u in van}

print(f"OTC sessions: {len(otc)}  Vanilla sessions: {len(van)}")
print()
for label, rows in [("OTC", otc), ("Vanilla", van)]:
    by = defaultdict(list)
    for cid, pid, u in rows:
        by[cid].append((pid, u))
    print(f"=== {label} ===")
    for cid in [
        "arml_local",
        "arml_national_team",
        "arml_national_power",
        "arml_power",
    ]:
        rs = by.get(cid, [])
        us = [u for _, u in rs if u is not None]
        nz = sum(1 for u in us if u > 0)
        mean = sum(us) / len(us) if us else float("nan")
        print(
            f"  {cid:24s} n={len(rs):2d} scored={len(us):2d} "
            f"mean_util={mean * 100:5.1f}% nz={nz}/{len(us) if us else 0}"
        )
    print()

print("=== paired OTC vs Vanilla (local + national_team) ===")
print(f"{'problem_id':28s} {'OTC':>8s} {'Van':>8s}")
for cid, pid, ou in otc:
    if cid not in {"arml_local", "arml_national_team"}:
        continue
    vu = van_by.get(pid, (None, None))[1]
    os_ = f"{ou * 100:5.1f}%" if ou is not None else "  n/a"
    vs_ = f"{vu * 100:5.1f}%" if vu is not None else "  n/a"
    print(f"{pid:28s} {os_:>8s} {vs_:>8s}")

# means for paired only
paired = []
for cid, pid, ou in otc:
    if cid not in {"arml_local", "arml_national_team"}:
        continue
    vu = van_by.get(pid, (None, None))[1]
    if ou is not None and vu is not None:
        paired.append((cid, ou, vu))
print()
for cid in ["arml_local", "arml_national_team"]:
    ps = [(o, v) for c, o, v in paired if c == cid]
    if not ps:
        continue
    print(
        f"mean {cid}: OTC {sum(o for o, _ in ps) / len(ps) * 100:.1f}%  "
        f"Vanilla {sum(v for _, v in ps) / len(ps) * 100:.1f}%  n={len(ps)}"
    )

print()
print("=== Vanilla power (already rubric-scored) ===")
print(f"{'problem_id':28s} {'util':>8s} {'score':>12s}")
for cid, pid, u in van:
    if cid not in {"arml_national_power", "arml_power"}:
        continue
    sess = Path("results/arml_all_protocol_v3_vanilla_20260909") / pid / "contest_session.json"
    g = (json.loads(sess.read_text(encoding="utf-8")).get("grade") or {}) if sess.exists() else {}
    sc, mx = g.get("score"), g.get("max_score")
    us = f"{u * 100:5.1f}%" if u is not None else "  n/a"
    ss = f"{sc}/{mx}" if sc is not None else "n/a"
    print(f"{pid:28s} {us:>8s} {ss:>12s}")
