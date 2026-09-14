"""Build safe, portable task inputs from canonical benchmark/rule components."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
import re
import shutil


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_name(value: str) -> str:
    if value in ("", ".", "..") or "/" in value or "\\" in value:
        raise ValueError(f"Unsafe task id: {value!r}")
    return re.sub(r'[<>:"|?*]', "_", value).rstrip(" .")


def section(title: str, value) -> str:
    return f"## {title}\n\n```json\n{json.dumps(value, ensure_ascii=False, indent=2)}\n```\n\n"


def build_packages(root: Path, stage: Path, index: dict, benchmarks: dict, rules: dict, hash_file) -> dict:
    """Build in a new staging tree. Caller validates it before replacing old trees."""
    base_root, last_root = stage / "base", stage / "last_exam"
    base_cards, last_cards, competitions, base_competitions, input_manifest = [], [], [], [], []
    used_dirs = set()
    for track in index["olympiads"]:
        cid = track["id"]
        competition, method, evaluation = (rules[cid][k] for k in ("competition", "collaboration", "evaluation"))
        pack = last_root / "competitions" / cid
        ground = "# Competition rules\n\n" + competition.get("rules_text", "") + "\n"
        environment = "# Environment\n\n"
        for title, key in [("Roster", "team"), ("Allowed tools", "allowed_tools"),
                           ("Resources", "resources"), ("Official execution facts", "execution"),
                           ("Deliverable", "deliverable")]:
            environment += section(title, competition.get(key, {}))
        method_text = "# Team method\n\n" + section("Collaboration configuration", method)
        write_text(pack / "input/ground_rules.md", ground)
        write_text(pack / "input/environment.md", environment)
        write_text(pack / "method/collaboration.md", method_text)
        write_json(pack / "method/roles.json", method.get("agent_roles", []))
        write_text(pack / "eval/scoring.md", "# Hidden scoring configuration\n\n" + section("Evaluation", evaluation))
        write_json(pack / "eval/evaluation.json", evaluation)
        competitions.append(dict(competition_id=cid, rule_id=competition.get("rule_id"),
                                 profile=competition.get("profile"), protocol=competition.get("protocol"),
                                 n_roles=len(method.get("agent_roles", [])),
                                 path=f"data/last_exam/competitions/{cid}", source=track["rule_card_path"]))
        rows = benchmarks[cid]
        directory_counts = Counter(safe_name(r["problem_id"]).casefold() for r in rows)
        base_competitions.append(dict(id=cid, name=track.get("name", cid),
                                      base_path=f"data/base/tasks/{cid}", benchmark_path=track["benchmark_path"],
                                      n_tasks=len(rows), eval_units=sorted({r["eval_unit"] for r in rows})))
        for row in rows:
            pid = row["problem_id"]
            folder = safe_name(pid)
            if directory_counts[folder.casefold()] > 1:
                # Windows paths are case-insensitive; preserve both canonical IDs.
                folder += "__" + hashlib.sha256(pid.encode("utf-8")).hexdigest()[:10]
            key = (cid + "/" + folder).casefold()
            if key in used_dirs:
                raise ValueError(f"Task directory collision: {pid}")
            used_dirs.add(key)
            relative = Path("tasks") / cid / folder
            task = last_root / relative
            input_dir = task / "base/input"
            input_dir.mkdir(parents=True, exist_ok=True)
            write_text(input_dir / "problem.md", row.get("problem_description", "") + "\n")
            source = (root / row["source_file"]).resolve() if row.get("source_file") else None
            source_parent = source.parent if source and source.is_file() else source
            placed = {"problem.md"}
            for asset in row.get("assets", []):
                if asset.get("role") != "agent_visible":
                    continue
                source_asset = (root / asset["path"]).resolve()
                if not source_asset.is_file():
                    raise ValueError(f"Contestant assets must be explicitly separated files: {asset['path']}")
                sha = hash_file(asset["path"])
                if asset.get("sha256") and sha != asset["sha256"]:
                    raise ValueError(f"Asset changed during packaging: {asset['path']}")
                try:
                    subpath = source_asset.relative_to(source_parent) if source_parent else Path(source_asset.name)
                except ValueError:
                    subpath = Path("assets") / sha[:12] / source_asset.name
                if subpath.as_posix().casefold() in placed:
                    subpath = Path("assets") / sha[:12] / source_asset.name
                placed.add(subpath.as_posix().casefold())
                destination = input_dir / subpath
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_asset, destination)
                input_manifest.append(dict(task_id=f"{cid}/{pid}", source=asset["path"], sha256=sha,
                                           staged=(relative / "base/input" / subpath).as_posix()))
            e = row.get("evaluation", {})
            # These files contain task/contest instructions, never answer or rubric bodies.
            write_text(input_dir / "task_sop.md", f"# Task\n\nCompetition: {cid}\n\nTask: {pid}\n\n"
                       f"Edition: {row.get('year')}\n\nTeam size: {row.get('team_size')}\n\n"
                       f"Deliverable: {e.get('deliverable', competition.get('deliverable', {}).get('official_deliverable', 'competition submission'))}\n\n"
                       "Use the attached problem materials and the inherited competition and collaboration instructions.\n")
            write_text(input_dir / "input_environment_spec.md", environment)
            write_text(input_dir / "ground_rules.md", ground)
            write_text(input_dir / "collaboration.md", method_text)
            has_gold = bool(row.get("gold_label", {}).get("expected_answer") or
                            any(p.get("expected") for p in row.get("gold_label", {}).get("parts", [])))
            reference = dict(visibility="hidden_until_grade", gold_pointer=f"{track['benchmark_path']}#{pid}.gold_label",
                             has_gold_answer=has_gold, evaluator_id=e.get("evaluator_id"),
                             evaluator_status=e.get("status"), solution_file=row.get("solution_file"),
                             evaluation=e, rubric_path=e.get("rubric_path"), deliverable=e.get("deliverable"))
            write_json(task / "eval/reference.json", reference)
            files = sorted(p.relative_to(input_dir).as_posix() for p in input_dir.rglob("*") if p.is_file())
            last_cards.append(dict(task_id=f"{cid}/{pid}", competition_id=cid, problem_id=pid,
                title=row.get("title", row.get("topic", pid)), year=row.get("year"), team_size=row.get("team_size"),
                source_url=row.get("source_url"), source_repo_path=relative.as_posix(),
                inherits_competition_pack=f"competitions/{cid}", rule_card=track["rule_card_path"],
                input=dict(visibility="agent_at_start", files=[dict(name=Path(f).name, path=f"base/input/{f}") for f in files]),
                method=dict(visibility="agent_at_start", path=f"competitions/{cid}/method"),
                eval=dict(visibility="hidden_until_grade", path="eval/reference.json", competition_eval=f"competitions/{cid}/eval")))
            shutil.copytree(task / "base", base_root / relative / "base")
            base_cards.append(dict(task_id=f"{cid}/{pid}", title=row.get("title", row.get("topic", pid)),
                summary="", category=cid, subdomain=row.get("task_type"), task_split=row["split"], eval_unit=row["eval_unit"],
                competition=row.get("competition"), year=row.get("year"), team_size=row.get("team_size"),
                source_url=row.get("source_url"), source_repo_path=relative.as_posix(), variant="base",
                input_files=[dict(name=Path(f).name, path=f"input/{f}", description="Agent-visible input") for f in files],
                evaluation=e, has_gold_answer=has_gold, solution_file=row.get("solution_file"), status=row.get("status"),
                software=[], link_modes=["copy"], taxonomy=dict(domain_code=cid, subdomain_code=row.get("task_type"))))
    n = len(last_cards)
    write_json(base_root / "index.json", dict(description="Generated canonical competition catalog", layout="ale",
               source_benchmarks="data/benchmarks", source_index="data/benchmarks/index.json", task_cards_path="data/base/task_cards.json",
               n_competitions=len(competitions), n_tasks=n, competitions=base_competitions))
    write_json(base_root / "task_cards.json", dict(description="Canonical per-task catalog", layout="ale", source_benchmarks="data/benchmarks", n_tasks=n, tasks=base_cards))
    write_json(last_root / "index.json", dict(description="Shared competition packs and isolated problem inputs", status="generated_from_data_rules",
               source_rules="data/rules", source_benchmarks="data/benchmarks", n_competitions=len(competitions), n_tasks=n,
               generate="python scripts/repair_data_catalog.py --derived-only", competitions_index="competitions/index.json",
               visibility=dict(agent_at_start=["competitions/<cid>/input", "competitions/<cid>/method", "tasks/<cid>/<pid>/base/input"],
                               hidden_until_grade=["competitions/<cid>/eval", "tasks/<cid>/<pid>/eval"])))
    write_json(last_root / "task_cards.json", dict(description="Canonical task inputs and hidden evaluation pointers", n_tasks=n, tasks=last_cards))
    write_json(last_root / "competitions/index.json", dict(description="One pack per canonical track", n_competitions=len(competitions), competitions=competitions))
    for name, tree in [("base", base_root), ("last_exam", last_root)]:
        write_json(tree / "input_asset_manifest.json", dict(visibility="maintainer_only", files=input_manifest))
        write_text(tree / "README.md", f"# data/{name}\n\nGenerated from data/benchmarks and data/rules: {len(competitions)} tracks, {n} records.\n\n"
                   "Only explicitly agent_visible files are copied into task inputs. Judge-only references remain outside input.\n\n"
                   "Resolve task directories through task_cards.json source_repo_path; case-colliding IDs use stable hash suffixes.\n\n"
                   "Task availability is defined by the canonical record's evaluation.status. A staged task is not necessarily ready.\n\n"
                   "Regenerate with `python scripts/repair_data_catalog.py --derived-only`. Previous outputs are archived under data/excluded.\n")
    return dict(n_tasks=n, n_competitions=len(competitions), staged_assets=len(input_manifest))
