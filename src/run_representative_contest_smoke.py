"""Representative offline smoke; no production source modifications."""
import argparse
import json
from datetime import datetime, timezone
import traceback
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import Mock

from action_modules.task_specific import resolve_contest_interface
from artifact_contract import ArtifactContract
from artifacts.assets import file_sha256
from artifacts.contest_delivery import ArtifactRenderer
from contest_config import BASELINES
from contest_manifest import load_contest_manifest
from evaluation.models import load_rubric
from llm import LLMResponse, LLMToolCall
from otc_artifact_pipeline import prepare_artifact_run, run_artifact_contest
from rules.loader import load_rule_card
from run_all_contest_smoke import CatalogSmokeAgent, run_case, write_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / ("five_baseline_representative_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
VARIANTS = ("single_agent", "decentralized", "centralized", "vallina_otc", "otc")
LABELS = {"single_agent": "Single agent", "decentralized": "Decentralized",
          "centralized": "Centralized", "vallina_otc": "Open Table Coach + rule card",
          "otc": "Open Table Coach + rule card + memory"}
NATIVE = (
    ("icpc", "icpc_wf_2012_5", 5, "five programming problems"),
    ("arml_local", "arml_local_2009", 4, "four split answer-sheet questions"),
    ("hmmt_guts", None, 3, "three split questions from the first structured Guts record; selection recorded"),
    ("mystery_hunt", None, 3, "three puzzle records"),
    ("ioaa_group", None, 1, "star-chart tool capability and answer flow"),
    ("ijso_practical", None, 1, "laboratory tool capability and answer flow"),
)
ARTIFACTS = (("mcm", "document"), ("ieo_business_case", "slides"))
TURNS, ARTIFACT_TURNS, TOKENS = 32, 12, 200000


def common_details(result, manifest, variant):
    events = result["memory"]["events"]
    errors = [e for e in events if e["kind"] == "action_error"]
    tasks = result["session_checkpoint"]["tasks"]
    checks = {
        "no_action_errors": not errors,
        "all_tasks_have_nonempty_submission": all(bool(result["submissions"].get(t.task_id)) for t in manifest.tasks),
        "all_tasks_have_candidate": all(bool(t["versions"]) for t in tasks),
        "correct_variant": result["system_variant"] == variant,
        "memory_setting": result["modules"]["memory"] == (variant == "otc"),
        "coach_setting": result["modules"]["coach"] == (variant in {"vallina_otc", "otc"}),
        "coach_once": sum(e["kind"] == "precontest_coach_guidance" and e["actor"] == "Coach"
                          for e in events) == int(variant in {"vallina_otc", "otc"}),
        "unique_action_names": len(result["action_names"]) == len(set(result["action_names"])),
        "token_budget": result["budget"]["tokens_used"] <= TOKENS,
    }
    if variant == "centralized":
        checks["leader_is_contestant_not_coach"] = result["plan_author"] == "Agent_1"
        checks["no_external_coach_events"] = not any(e["actor"] == "Coach" for e in events)
        checks["only_leader_submits_in_play"] = not any(
            e["kind"] in {"submit", "submit_code", "finish_contest"}
            and e["actor"].startswith("Agent_") and e["actor"] != "Agent_1" for e in events)
    if variant != "otc":
        checks["memory_tools_not_called"] = not any(e["kind"] in {"note", "note_shared", "recall_result"} for e in events)
    if any(t.programming for t in manifest.tasks):
        accepted = result["diagnostics"]["attempts_to_ac"]
        checks["all_programming_tasks_accepted"] = all(accepted.get(t.task_id) is not None for t in manifest.tasks if t.programming)
        queued = {e["event_id"] for e in events if e["kind"] == "verdict_queued"}
        delivered = {e["payload"]["queued_event_id"] for e in events if e["kind"] == "verdict_delivered"}
        checks["all_delayed_verdicts_delivered"] = queued == delivered
    if BASELINES[variant].coach == "card":
        from contest_config import ContestRunConfig
        card = load_rule_card(manifest.competition_id, required=True)
        policy = ContestRunConfig(variant, card.team_size_default, TURNS, rule_card=card).otc_policy
        if policy.structured_deliberation:
            checks["required_challenges_executed"] = sum(e["kind"] == "challenge" for e in events) >= policy.min_challenges
    warnings = []
    if result["diagnostics"].get("deadline_submission"):
        warnings.append("deadline_collection_used")
    if any(e["kind"] == "deadline_drafts_submitted" and e["payload"].get("review_gate_waived") for e in events):
        warnings.append("deadline_review_gate_waived_by_current_protocol")
    return {
        "checks": checks, "action_errors": errors,
        "action_error_counts": dict(Counter(e["payload"].get("error", "") for e in errors)),
        "warnings": warnings, "budget": result["budget"], "modules": result["modules"],
        "baseline": result["baseline"], "protocol_version": result["protocol_version"],
        "task_ids": [t.task_id for t in manifest.tasks], "task_count": len(manifest.tasks),
        "nonempty_submission_count": sum(bool(v) for v in result["submissions"].values()),
        "called_actions": dict(Counter(e["kind"] for e in events if e["actor"].startswith("Agent_"))),
    }


def benchmark_rows(competition):
    index = json.loads((ROOT / "data/benchmarks/index.json").read_text(encoding="utf-8"))
    entry = next(r for r in index["olympiads"] if r["id"] == competition)
    rows = json.loads((ROOT / entry["benchmark_path"]).read_text(encoding="utf-8"))
    return [r for r in rows if isinstance(r, dict) and r.get("problem_id")
            and any(r.get(k) for k in ("problem_description", "description", "prompt"))]


def representative_manifest(competition, existing=None, count=1):
    if existing:
        manifest = load_contest_manifest(ROOT / "data/contest_manifests" / (existing + ".json"),
                                         benchmark_root=ROOT / "data/benchmarks")
    else:
        rows = benchmark_rows(competition)
        chosen = rows[:count] if competition == "mystery_hunt" else rows[:1]
        if competition == "hmmt_guts":
            structured = [row for row in rows
                          if len((row.get("gold_label") or {}).get("parts") or []) >= count]
            if not structured:
                raise ValueError("HMMT smoke requires a public record with structured part IDs")
            chosen = structured[:1]
        path = OUT / "manifests" / (competition + ".json")
        write_json(path, {"session_id": "representative_" + competition, "competition_id": competition,
                          "problem_ids": [r["problem_id"] for r in chosen],
                          "split_parts": competition == "hmmt_guts"})
        manifest = load_contest_manifest(path, benchmark_root=ROOT / "data/benchmarks")
    tasks = manifest.tasks[:count]
    if len(tasks) != count:
        raise ValueError(f"Expected {count} representative tasks, found {len(tasks)}")
    metadata = dict(manifest.metadata)
    if competition == "hmmt_guts" and existing is None:
        metadata["smoke_selection"] = {
            "previous_record": rows[0]["problem_id"],
            "selected_record": chosen[0]["problem_id"],
            "split_parts": True,
            "selection_rule": f"first record with at least {count} structured parts",
            "scope_note": "This does not repair missing part IDs in the previous record.",
        }
    return replace(manifest, session_id="representative_" + competition, tasks=tasks, metadata=metadata)


def record(row, rows):
    rows.append(row)
    write_json(OUT / "cases" / row["scenario"] / (row["variant"] + ".json"), row)
    write_json(OUT / "progress.json", {"completed": len(rows), "expected": 40,
                                     "counts": dict(Counter(r["status"] for r in rows))})
    print(f"{len(rows):02d}/40 {row['scenario']:20} {row['variant']:14} {row['status']}", flush=True)


def run_native(rows):
    for competition, existing, count, description in NATIVE:
        try:
            manifest = representative_manifest(competition, existing, count)
            card = load_rule_card(competition, required=True)
            interface = resolve_contest_interface(manifest, rule_card=card).report()
            preflight = None
        except Exception:
            preflight = traceback.format_exc()
        for variant in VARIANTS:
            row = dict(scenario=competition, competition=competition, variant=variant,
                       scope=description, pipeline="native", external_tools="mock", live_judge=False)
            if preflight:
                row.update(status="BLOCKED", error=preflight)
            else:
                try:
                    case = run_case(manifest, card, variant, TURNS)
                    details = common_details(case["result"], manifest, variant)
                    details["checks"].update(case["checks"])
                    row.update(details, interface=interface,
                               fixture_selection=manifest.metadata.get("smoke_selection"),
                               status="PASS" if all(details["checks"].values()) else "FAIL")
                    write_json(OUT / "traces" / competition / (variant + ".json"), case["result"])
                except Exception:
                    row.update(status="FAIL", error=traceback.format_exc())
            record(row, rows)


def task_pdf(competition):
    manifest = representative_manifest(competition)
    statement = manifest.tasks[0].prompt
    renderer = ArtifactRenderer(OUT / "task_inputs" / competition,
                               ArtifactContract("document", max_pages=100, max_source_chars=200000))
    receipt = renderer(None, "render_pdf", {"content": statement})
    return Path(receipt["pdf"]), statement, manifest.tasks[0].task_id


def mock_judge(prepared):
    rubric = load_rubric(prepared["rubric"])
    payload = {
        "criteria": [dict(id=c.id, score=c.min_score, max_score=c.max_score,
                          evidence=["Offline smoke fixture, not a solution-quality claim."],
                          justification="Mock judge response validates delivery only.",
                          confidence=1, observable=c.observable) for c in rubric.criteria],
        "total_score": sum(c.min_score for c in rubric.criteria), "max_score": rubric.total_points,
        "warnings": [], "limitations": ["No real model judged this artifact."],
    }
    return Mock(return_value=LLMResponse(json.dumps(payload), "mock", "mock-judge"))


def run_artifacts(rows):
    for competition, kind in ARTIFACTS:
        try:
            pdf, statement, task_id = task_pdf(competition)
            preflight = None
        except Exception:
            preflight = traceback.format_exc()
        for variant in VARIANTS:
            row = dict(scenario=competition, competition=competition, variant=variant,
                       pipeline="artifact_" + kind, scope="real rendering, review, delivery, completed-run resume",
                       live_judge=False, live_llm=False)
            if preflight:
                row.update(status="BLOCKED", error=preflight)
            else:
                try:
                    prepared = prepare_artifact_run(
                        competition=competition, task_pdf=pdf, task_text=statement,
                        output=OUT / "artifacts" / competition / variant,
                        max_turns=ARTIFACT_TURNS, max_tokens=TOKENS, provider="openai", model="mock",
                        judge_model="mock-judge", system_variant=variant)
                    source = ("<html><body><section><h1>Offline smoke candidate</h1>"
                              "<p>Evidence, assumptions and a proposed conclusion.</p>"
                              "</section></body></html>" if kind == "slides" else
                              "Offline smoke candidate\n\nAssumptions and method\n"
                              "This is a deterministic delivery fixture, not a solved contest problem.\n\n"
                              "Validation\nCheck source, PDF and submission identity.\n\nConclusion\nSmoke only.")
                    # Keep artifact solver tools offline; render_pdf still uses
                    # the real versioned renderer and delivery executor.
                    team = CatalogSmokeAgent(prepared["manifest"], prepared["config"],
                                             candidate_content=source, probe_task_tools=False)
                    judge = mock_judge(prepared)
                    result = run_artifact_contest(prepared, agent_request=team, judge_request=judge)
                    contest = json.loads(Path(result["contest_file"]).read_text(encoding="utf-8"))
                    details = common_details(contest, prepared["manifest"], variant)
                    artifact, checks = result.get("artifact", {}), details["checks"]
                    checks["artifact_complete"] = result["status"] == "complete"
                    checks["unique_function_schemas"] = team.schema_names_unique
                    checks["pdf_tool_exercised"] = team.called["render_pdf"] > 0
                    checks["external_solver_tools_not_called"] = not any(
                        team.called[name] for name in ("execute_code", "web_search"))
                    checks["judge_called_once"] = judge.call_count == 1
                    checks["real_pdf_matches_receipt"] = bool(artifact) and file_sha256(Path(artifact["pdf"])) == artifact["pdf_sha256"]
                    checks["judged_pdf_matches_receipt"] = bool(artifact) and judge.call_count == 1 and file_sha256(judge.call_args.args[0].attachments[-1].path) == artifact["pdf_sha256"]
                    checks["source_preserved"] = bool(artifact) and Path(artifact["source"]).read_text(encoding="utf-8") == source
                    checks["coach_has_no_task_attachment"] = all(not r.attachments for r in team.requests if r.purpose == "coach")
                    if result["status"] == "complete":
                        repeated = run_artifact_contest(prepared, resume=True,
                            agent_request=Mock(side_effect=AssertionError("agent rerun")),
                            judge_request=Mock(side_effect=AssertionError("judge rerun")))
                        checks["completed_resume_reuses_artifact"] = repeated["artifact"] == artifact
                    else:
                        checks["completed_resume_reuses_artifact"] = False
                    row.update(details, artifact=artifact, source_task_id=task_id,
                               interface=resolve_contest_interface(prepared["manifest"], rule_card=prepared["card"]).report(),
                               status="PASS" if all(checks.values()) else "FAIL")
                except Exception:
                    row.update(status="FAIL", error=traceback.format_exc())
            record(row, rows)


def report(rows):
    summary = {
        "protocol": "five_baseline_representative_smoke_v2", "expected_cases": 40,
        "completed_cases": len(rows), "counts": dict(Counter(r["status"] for r in rows)),
        "baseline_labels": LABELS, "baseline_configs": {v: asdict(BASELINES[v]) for v in VARIANTS},
        "baseline_caveat": "The two OTC presets differ only in the optional memory module under contest_session_v10.",
        "native_turns": TURNS, "artifact_turns": ARTIFACT_TURNS, "max_tokens": TOKENS,
        "budget_scope": "same turn/token cap within each scenario; single-agent one seat, teams card default",
        "live_llm": False, "live_judge": False, "native_external_tools": "mock except local calculator",
        "artifact_rendering": "real PDF and preview generation", "all_cases": rows,
        "by_baseline": {v: dict(Counter(r["status"] for r in rows if r["variant"] == v)) for v in VARIANTS},
    }
    write_json(OUT / "summary.json", summary)
    lines = [
        "# Five-baseline representative smoke", "",
        "Real local representative inputs; no live model or judge. PDF rendering is real.",
        "Native tools are mocked except the local calculator. No solution quality claim.", "",
        f"Completed: {len(rows)}/40. Counts: {json.dumps(summary['counts'])}.", "",
        "The OTC pair shares review, private channels and structured context; only memory differs.",
        "Team size is card-default; single-agent size is one.", "",
        "| Scenario | Single | Decentralized | Centralized | OTC + rules | OTC + rules + memory |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for scenario in [i[0] for i in NATIVE] + [i[0] for i in ARTIFACTS]:
        found = {r["variant"]: r for r in rows if r["scenario"] == scenario}
        lines.append("| " + scenario + " | " + " | ".join(found[v]["status"] for v in VARIANTS) + " |")
    lines.extend(["", "## Failures / blocked cases", ""])
    for r in rows:
        if r["status"] != "PASS":
            reason = ", ".join(k for k, ok in r.get("checks", {}).items() if not ok)
            lines.append(f"- {r['scenario']} / {r['variant']}: {reason}; {r.get('action_error_counts', {})}")
            if r.get("error"):
                lines.append(chr(96)*3 + "text\n" + r["error"] + "\n" + chr(96)*3)
    lines.extend(["", "## Fixture selection", ""])
    for r in rows:
        if r["variant"] == "single_agent" and r.get("fixture_selection"):
            lines.append("- " + r["scenario"] + ": " + json.dumps(r["fixture_selection"]))
    lines.extend(["", "## Coverage limits and deadline collection", ""])
    for r in rows:
        issues = r.get("interface", {}).get("limitations", [])
        if issues or r.get("warnings"):
            lines.append(f"- {r['scenario']} / {r['variant']}: " + "; ".join(r.get("warnings", []) + issues))
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "counts": summary["counts"], "by_baseline": summary["by_baseline"],
        "failed": [{"scenario": r["scenario"], "variant": r["variant"],
                    "checks": {k: v for k, v in r.get("checks", {}).items() if not v},
                    "errors": r.get("action_error_counts", {}), "exception": r.get("error", "")[-1500:]}
                   for r in rows if r["status"] != "PASS"]}), flush=True)


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    OUT = (args.output or OUT).resolve()
    if OUT.exists():
        parser.error("Use a fresh output directory; previous smoke evidence is preserved.")
    OUT.mkdir(parents=True)
    completed = []
    write_json(OUT / "protocol.json", {"expected_cases": 40, "variants": VARIANTS,
        "native": NATIVE, "artifacts": ARTIFACTS, "live_llm": False, "live_judge": False,
        "native_turns": TURNS, "artifact_turns": ARTIFACT_TURNS})
    run_native(completed)
    run_artifacts(completed)
    report(completed)
    return int(any(row["status"] != "PASS" for row in completed))


if __name__ == "__main__":
    raise SystemExit(main())
