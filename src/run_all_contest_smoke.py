"""Offline catalog-wide contest-module smoke, not a solver or judge benchmark.

Uses real local task statements/rule cards, deterministic function calls, and
explicitly mocked external tools/judges. Covers every active catalog track and
all five settings; blocked cases remain in the denominator and report.
"""
from __future__ import annotations

import argparse
import json
import re
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from action_modules.common import CORE_ACTION_NAMES
from action_modules.task_specific import resolve_contest_interface
from contest_config import BASELINE_NAMES, ContestRunConfig
from contest_lifecycle import _default_executor
from contest_manifest import load_contest_manifest
from contest_runner import run_contest
from llm import LLMRequest, LLMResponse, LLMToolCall
from rules.loader import load_rule_card

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


class CatalogSmokeAgent:
    """Deterministic, schema-aware driver shared by catalog and artifact smoke."""

    def __init__(self, manifest, config, *, candidate_content="Offline smoke candidate.",
                 probe_task_tools=True):
        self.manifest = manifest
        self.config = config
        self.candidate_content = candidate_content
        self.probe_task_tools = probe_task_tools
        self.probed: set[str] = set()
        self.called: Counter[str] = Counter()
        self.candidates: dict[str, str] = {}
        self.reported: set[tuple[str, int]] = set()
        self.proposal_authors: dict[str, str] = {}
        self.challenged: set[str] = set()
        self.requests: list[LLMRequest] = []
        self.schema_names_unique = True

    def __call__(self, request: LLMRequest) -> LLMResponse:
        if not self.probe_task_tools:
            self.requests.append(request)
        if not request.tools:
            text = "Offline preparation advice; not a solution."
            if self.config.leader and request.user_prompt.startswith("OPENING LEADER PLAN"):
                ids = [task.task_id for task in self.manifest.tasks]
                text = json.dumps({
                    "summary": "The contestant Leader allocates work.",
                    "work_assignments": {
                        f"Agent_{i}": ids[i - 1::self.config.team_size]
                        for i in range(1, self.config.team_size + 1)
                    },
                    "review_assignments": {}, "task_order": ids,
                })
            return LLMResponse(text, "mock", "catalog-smoke")
        counts = Counter(tool["name"] for tool in request.tools)
        duplicates = sorted(name for name, count in counts.items() if count > 1)
        if duplicates:
            self.schema_names_unique = False
            raise ValueError("duplicate function schemas: " + ", ".join(duplicates))
        offered = {tool["name"]: tool for tool in request.tools}
        match = re.search(r"TASK STATUS (.+?)\nBUDGET", request.user_prompt, re.DOTALL)
        rows = json.loads(match.group(1)) if match else []
        by_id = {row["task_id"]: row for row in rows}
        # Parse a state-header line, never an inline mention in review guidance.
        active_match = re.search(r"^ACTIVE TASK ([^\r\n]+)\r?$", request.user_prompt, re.MULTILINE)
        active = active_match.group(1).strip() if active_match else None
        row = by_id.get(active, {})
        task_by_id = {task.task_id: task for task in self.manifest.tasks}
        if active is not None and active not in task_by_id:
            raise ValueError("Smoke prompt names unknown active task: " + active)
        active_task = task_by_id.get(active)
        programming = bool(active_task and active_task.programming)
        seat = re.search(r"\bAgent_\d+\b", request.system_prompt.split("\n", 1)[0])
        agent = seat.group(0) if seat else ""
        marker = "YOUR ELIGIBLE PENDING REVIEWS\n"
        pending = (json.JSONDecoder().raw_decode(request.user_prompt.split(marker, 1)[1])[0]
                   if marker in request.user_prompt else [])

        def choices(action, argument="problem_id"):
            prop = offered[action]["parameters"]["properties"].get(argument, {})
            fallback = list(task_by_id) if argument == "problem_id" else []
            return prop.get("enum", fallback)  # An explicit empty enum stays empty.

        def unfinished(task_id):
            status = by_id.get(task_id, {})
            if status.get("locked"):
                return False
            return task_by_id[task_id].programming or not status.get("valid_submission")

        def needs_draft(task_id):
            return unfinished(task_id) and not by_id.get(task_id, {}).get("has_draft")

        def code_for(task_id):
            attempts = by_id.get(task_id, {}).get("attempts", 0)
            return "print(0)" + (f"\n# smoke revision after attempt {attempts}" if attempts else "")

        def emit(name, arguments):
            schema = offered[name]["parameters"]
            arguments = {key: value for key, value in arguments.items() if key in schema["properties"]}
            missing = set(schema.get("required", [])) - set(arguments)
            if missing:
                raise ValueError("smoke driver omitted required arguments: " + ", ".join(sorted(missing)))
            self.called[name] += 1
            return LLMResponse("", "mock", "catalog-smoke",
                               tool_calls=(LLMToolCall(name, arguments),))

        probes = ["check_budget", "query_rules", "inspect_problem", "remember", "recall"]
        if self.probe_task_tools:
            probes += ["use_calculator", "read_lab_equipment", "read_star_chart", "web_search", "execute_code"]
        for probe in probes:
            if probe not in offered or probe in self.probed:
                continue
            if probe in {"use_calculator", "read_lab_equipment", "read_star_chart", "web_search", "execute_code"}:
                if active is None or row.get("locked"):
                    continue
            arguments = {}
            if probe == "inspect_problem":
                targets = choices(probe)
                if not targets:
                    continue
                arguments = {"problem_id": active if active in targets else targets[0]}
            elif probe == "remember":
                arguments = {"content": "Offline smoke private note, not a solution."}
            elif probe == "recall":
                arguments = {"query": "smoke"}
            elif probe == "use_calculator":
                arguments = {"expression": "6*7"}
            elif probe == "web_search":
                arguments = {"query": "offline smoke probe"}
            elif probe == "execute_code":
                arguments = {"code": code_for(active)}
                if programming:
                    self.candidates[active] = arguments["code"]
            self.probed.add(probe)
            return emit(probe, arguments)

        # Follow the card's real deliberation protocol, rather than chatting
        # indefinitely while its challenge requirement withholds submission.
        policy = self.config.otc_policy
        required_challenges = policy.min_challenges if policy and policy.structured_deliberation else 0
        if len(self.challenged) < required_challenges:
            if "challenge" in offered:
                eligible = [pid for pid in choices("challenge", "proposal_id")
                            if pid in self.proposal_authors and pid not in self.challenged
                            and self.proposal_authors[pid] != agent]
                if eligible:
                    self.challenged.add(eligible[0])
                    return emit("challenge", {"proposal_id": eligible[0],
                        "content": "Offline smoke objection: check assumptions and independent evidence."})
            if "propose" in offered and len(self.proposal_authors) < required_challenges:
                pid = f"P{len(self.proposal_authors) + 1}"
                self.proposal_authors[pid] = agent
                return emit("propose", {"content": "Offline smoke proposal: draft, independently check, then submit."})

        if pending and "review_answer" in offered:
            target = pending[0]
            return emit("review_answer", {
                "problem_id": target["problem_id"], "version_hash": target["version_hash"],
                "decision": "approve", "content": "Offline mock review; not a correctness claim.",
            })
        if "finish_contest" in offered:
            return emit("finish_contest", {"reason": "All smoke tasks submitted."})
        if "submit" in offered and not offered["submit"]["parameters"]["properties"]:
            return emit("submit", {})

        if active and row.get("has_draft") and not row.get("locked"):
            approved = not self.config.review_required or row.get("independent_approval")
            candidate = row.get("state") in {"candidate", "review"}
            if candidate and approved:
                if programming and "submit_code" in offered:
                    return emit("submit_code", {"code": self.candidates.get(active, code_for(active))})
                if not programming and "submit" in offered:
                    return emit("submit", {"answer": self.candidates.get(active, self.candidate_content)})
            version = (active, row.get("versions", 0))
            if (programming and candidate and self.config.review_required
                    and row.get("latest_author") == agent and version not in self.reported
                    and not row.get("independent_approval") and "speak" in offered):
                self.reported.add(version)
                return emit("speak", {"content": "Sample evidence recorded; please independently review this source."})

        # A solved task is not a reason to keep rewriting the same answer.
        if active is None or not unfinished(active):
            if "select_problem" in offered:
                targets = [tid for tid in choices("select_problem") if unfinished(tid)]
                if targets:
                    return emit("select_problem", {"problem_id": targets[0]})
        if active and programming and not row.get("locked") and "execute_code" in offered:
            if needs_draft(active) or row.get("state") == "submitted":
                source = code_for(active)
                self.candidates[active] = source
                return emit("execute_code", {"code": source})
        if (active and self.manifest.metadata.get("artifact_contract")
                and needs_draft(active) and "render_pdf" in offered):
            self.candidates[active] = self.candidate_content
            return emit("render_pdf", {"content": self.candidate_content})
        if "work" in offered:
            targets = [tid for tid in choices("work") if needs_draft(tid)
                       and not (task_by_id[tid].programming and self.config.review_required)]
            target = active if active in targets else next(iter(targets), None)
            if target:
                source = code_for(target) if task_by_id[target].programming else self.candidate_content
                arguments = {"content": source}
                if target != active or "problem_id" in offered["work"]["parameters"].get("required", []):
                    arguments["problem_id"] = target
                self.candidates[target] = source
                return emit("work", arguments)
        if "select_problem" in offered:
            targets = [tid for tid in choices("select_problem") if tid != active and needs_draft(tid)]
            if targets:
                return emit("select_problem", {"problem_id": targets[0]})
        if "rest" in offered:
            return emit("rest", {"reason": "Waiting for a legal next step or verdict."})
        raise RuntimeError("No supported deterministic action offered: " + ", ".join(offered))


def mock_task_executor(task, action, arguments):
    if action == "use_calculator":
        return _default_executor(task, action, arguments)
    if action == "execute_code":
        return {"valid": True, "sample_verdict": "AC",
                "result": "MOCK sample evidence; source was not executed.", "mock": True}
    if action == "submit_code":
        return {"valid": True, "verdict": "AC", "mock": True}
    return {"valid": True, "result": "MOCK external tool response.", "mock": True}


def run_case(manifest, card, variant, turns):
    team_size = 1 if variant == "single_agent" else card.team_size_default
    config = ContestRunConfig(
        variant, team_size, turns,
        max_tokens=200000,
        minutes_per_turn=0, rule_card=card if variant in {"otc", "vallina_otc"} else None,
    )
    agent = CatalogSmokeAgent(manifest, config)
    result = run_contest(
        manifest, lambda *_: "Offline smoke thought.", config,
        action_request_fn=agent, action_transport="native",
        coach_query_fn=lambda *_: "Offline blind preparation advice.",
        task_action_executor=mock_task_executor,
    )
    errors = [event for event in result["memory"]["events"] if event["kind"] == "action_error"]
    checks = {
        "no_action_errors": not errors,
        "common_core_present": CORE_ACTION_NAMES <= set(result["action_names"]),
        "module_selection_recorded": result["modules"] == config.modules.as_dict(),
        "memory_tools_gated": (
            {"remember", "recall", "share_note"} <= set(result["action_names"])
            if config.modules.memory
            else not ({"remember", "recall", "share_note"} & set(result["action_names"]))
        ),
        "budget_respected": (config.max_api_calls is None or result["budget"]["api_calls_used"] <= config.max_api_calls),
        "task_progress": all(bool(result["submissions"].get(task.task_id)) for task in manifest.tasks),
        "unique_function_schemas": agent.schema_names_unique,
        "common_probes_executed": {"check_budget", "query_rules", "inspect_problem"} <= set(agent.called),
    }
    if any(task.programming for task in manifest.tasks):
        checks["mock_programming_accepted"] = all(
            result["diagnostics"]["attempts_to_ac"].get(task.task_id) is not None
            for task in manifest.tasks if task.programming
        )
    if config.otc_policy is not None and config.otc_policy.structured_deliberation:
        checks["required_challenges_executed"] = sum(
            event["kind"] == "challenge" for event in result["memory"]["events"]
        ) >= config.otc_policy.min_challenges
    brief_count = sum(
        event["kind"] == "precontest_coach_guidance" and event["actor"] == "Coach"
        for event in result["memory"]["events"]
    )
    checks["coach_lifecycle"] = brief_count == int(config.modules.coach)
    if not config.modules.memory:
        checks["no_memory_events"] = not any(
            event["kind"] in {"note", "note_shared", "recall_result"}
            for event in result["memory"]["events"]
        )
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks, "action_errors": errors,
        "called_actions": dict(agent.called), "result": result,
    }


def run_catalog(output: Path, *, turns: int = 12, competitions=None):
    index = json.loads((ROOT / "data/benchmarks/index.json").read_text(encoding="utf-8"))
    entries = [entry for entry in index["olympiads"] if entry.get("catalog_status", "active") == "active"]
    if competitions:
        wanted = set(competitions)
        unknown = wanted - {entry["id"] for entry in entries}
        if unknown:
            raise ValueError("Unknown catalog competitions: " + ",".join(sorted(unknown)))
        entries = [entry for entry in entries if entry["id"] in wanted]
    if output.exists():
        raise ValueError(f"Use a fresh smoke output directory: {output}")
    output.mkdir(parents=True)
    rows = []
    for entry in entries:
        competition = entry["id"]
        preflight_error = None
        manifest = card = interface = None
        try:
            data = json.loads((ROOT / entry["benchmark_path"]).read_text(encoding="utf-8"))
            candidates = [row for row in data if isinstance(row, dict) and row.get("problem_id")
                          and any(row.get(key) for key in ("problem_description", "description", "prompt"))]
            if not candidates:
                raise ValueError("No usable public task statement in benchmark")
            selected = candidates[0]
            manifest_path = output / "manifests" / f"{competition}.json"
            write_json(manifest_path, {
                "session_id": f"module_smoke_{competition}", "competition_id": competition,
                "problem_ids": [selected["problem_id"]], "split_parts": False,
                "competition_description": entry.get("name", competition),
            })
            manifest = load_contest_manifest(manifest_path, benchmark_root=ROOT / "data/benchmarks")
            card = load_rule_card(competition, required=True)
            interface = resolve_contest_interface(manifest, rule_card=card).report()
        except Exception:
            preflight_error = traceback.format_exc()
        for variant in BASELINE_NAMES:
            row = {"competition": competition, "setting": variant,
                   "evaluation_status_counts": entry.get("evaluation_status_counts", {}),
                   "task_interface": interface}
            try:
                if preflight_error:
                    row.update(status="BLOCKED", error=preflight_error)
                else:
                    case = run_case(manifest, card, variant, turns)
                    write_json(output / "cases" / competition / f"{variant}.json", case)
                    row.update({key: value for key, value in case.items() if key != "result"})
            except Exception:
                row.update(status="FAIL", error=traceback.format_exc())
            rows.append(row)
            print(f"{competition:26s} {variant:14s} {row['status']}", flush=True)
    counts = dict(Counter(row["status"] for row in rows))
    summary = {
        "protocol": "catalog_module_offline_smoke_v1",
        "scope": "one real representative record per active competition, all contest settings",
        "competition_count": len(entries), "setting_count": len(BASELINE_NAMES),
        "expected_cases": len(entries) * len(BASELINE_NAMES), "completed_cases": len(rows),
        "counts": counts, "live_llm": False, "live_external_tools": False,
        "live_judge": False, "calculator": "real local implementation",
        "all_cases": rows,
    }
    write_json(output / "summary.json", summary)
    report = [
        "# Catalog module smoke", "",
        f"Competitions: {len(entries)}; settings: {len(BASELINE_NAMES)}; cases: {len(rows)}.",
        f"Statuses: {json.dumps(counts, sort_keys=True)}.", "",
        "Offline smoke only. External tools and programming verdicts are mocked.",
        "PASS means the runtime checks passed, not evaluator or simulator readiness.", "",
        "| Competition | Setting | Status | Failed checks / blocker |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        detail = ",".join(k for k, ok in row.get("checks", {}).items() if not ok)
        if row.get("error"):
            detail = row["error"].strip().splitlines()[-1]
        report.append(f"| {row['competition']} | {row['setting']} | {row['status']} | {detail.replace('|', '/')} |")
    report.extend(["", "## Competition interface limitations", ""])
    for entry in entries:
        row = next(item for item in rows if item["competition"] == entry["id"])
        issues = (row.get("task_interface") or {}).get("limitations", [])
        if issues:
            report.append(f"- {entry['id']}: " + "; ".join(issues))
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "counts": counts, "cases": len(rows)}), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--turns", type=int, default=12)
    parser.add_argument("--competition", action="append")
    args = parser.parse_args()
    if args.turns < 1:
        parser.error("--turns must be positive")
    output = args.output or ROOT / "results" / (
        "module_smoke_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    )
    summary = run_catalog(output, turns=args.turns, competitions=args.competition)
    raise SystemExit(1 if any(summary["counts"].get(key, 0) for key in ("FAIL", "BLOCKED")) else 0)


if __name__ == "__main__":
    main()
