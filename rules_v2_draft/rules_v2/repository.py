from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from jsonschema import Draft202012Validator, FormatChecker


class RulesV2Error(ValueError):
    """Raised when callers cannot safely resolve or use a draft ruleset."""


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    location: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "location": self.location,
            "message": self.message,
        }


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    def add(self, severity: str, code: str, location: str, message: str) -> None:
        self.issues.append(ValidationIssue(severity, code, location, message))

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "issues": [issue.as_dict() for issue in self.issues],
        }


@dataclass(frozen=True)
class ResolvedRuleset:
    ruleset_id: str
    competition_id: str
    selector: dict[str, Any]
    team_size: int
    roster: tuple[dict[str, Any], ...]
    payload: dict[str, Any]


@dataclass(frozen=True)
class BenchmarkAudit:
    rows_checked: int
    rows_resolved: int
    failures: tuple[dict[str, Any], ...]

    @property
    def ok(self) -> bool:
        return not self.failures

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "rows_checked": self.rows_checked,
            "rows_resolved": self.rows_resolved,
            "failures": list(self.failures),
        }


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RulesV2Error(f"Invalid JSON in {path}: {exc}") from exc


def _json_path(parts: Iterable[Any]) -> str:
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


class RuleRepository:
    """Deep module for loading, validating, resolving, and expanding rulesets.

    Callers provide task metadata and receive one fully selected ruleset plus a
    concrete roster. Catalog selection, schema validation, provenance integrity,
    and role expansion remain inside this module.
    """

    def __init__(
        self,
        *,
        root: Path,
        catalog: dict[str, Any],
        entries: tuple[dict[str, Any], ...],
        rulesets: dict[str, dict[str, Any]],
        entry_paths: dict[str, Path],
        catalog_schema: dict[str, Any],
        ruleset_schema: dict[str, Any],
        migration_matrix: dict[str, Any],
    ) -> None:
        self.root = root
        self.project_root = root.parent
        self.catalog = catalog
        self.entries = entries
        self.rulesets = rulesets
        self.entry_paths = entry_paths
        self.catalog_schema = catalog_schema
        self.ruleset_schema = ruleset_schema
        self.migration_matrix = migration_matrix

    @classmethod
    def open(cls, root: str | Path) -> "RuleRepository":
        draft_root = Path(root).resolve()
        catalog = _read_json(draft_root / "catalog.json")
        catalog_schema = _read_json(draft_root / "schemas" / "catalog.schema.json")
        ruleset_schema = _read_json(draft_root / "schemas" / "ruleset.schema.json")
        migration_path = draft_root / "migration_matrix.json"
        migration_matrix = _read_json(migration_path) if migration_path.is_file() else {}

        entries_raw = catalog.get("entries") if isinstance(catalog, dict) else None
        entries = tuple(entries_raw) if isinstance(entries_raw, list) else ()
        rulesets: dict[str, dict[str, Any]] = {}
        entry_paths: dict[str, Path] = {}
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            ruleset_id = str(entry.get("ruleset_id") or f"<entry-{index}>")
            relative = entry.get("path")
            if not isinstance(relative, str):
                continue
            path = (draft_root / relative).resolve()
            entry_paths[ruleset_id] = path
            if not _inside(path, draft_root) or not path.is_file():
                continue
            payload = _read_json(path)
            if isinstance(payload, dict):
                rulesets[ruleset_id] = payload

        return cls(
            root=draft_root,
            catalog=catalog,
            entries=entries,
            rulesets=rulesets,
            entry_paths=entry_paths,
            catalog_schema=catalog_schema,
            ruleset_schema=ruleset_schema,
            migration_matrix=migration_matrix,
        )

    def resolve(
        self,
        task: Mapping[str, Any],
        *,
        team_size: int | None = None,
    ) -> ResolvedRuleset:
        competition_id = str(task.get("competition_id") or "").strip()
        if not competition_id:
            raise RulesV2Error("Task metadata requires competition_id.")

        matches: list[dict[str, Any]] = []
        for entry in self.entries:
            if entry.get("competition_id") != competition_id:
                continue
            selector = entry.get("selector") or {}
            if all(task.get(key) == value for key, value in selector.items()):
                matches.append(entry)
        if not matches:
            raise RulesV2Error(
                f"No ruleset matches competition_id={competition_id!r} and task metadata."
            )

        specificity = max(len(entry.get("selector") or {}) for entry in matches)
        winners = [
            entry
            for entry in matches
            if len(entry.get("selector") or {}) == specificity
        ]
        if len(winners) != 1:
            ids = ", ".join(str(entry.get("ruleset_id")) for entry in winners)
            raise RulesV2Error(f"Ambiguous ruleset selection: {ids}")

        entry = winners[0]
        ruleset_id = str(entry["ruleset_id"])
        payload = self.rulesets.get(ruleset_id)
        if payload is None:
            raise RulesV2Error(f"Ruleset {ruleset_id!r} is missing or unreadable.")

        resolved_size = team_size or self._task_team_size(task, payload)
        roster = tuple(self._generate_roster(payload, resolved_size))
        return ResolvedRuleset(
            ruleset_id=ruleset_id,
            competition_id=competition_id,
            selector=dict(entry.get("selector") or {}),
            team_size=resolved_size,
            roster=roster,
            payload=copy.deepcopy(payload),
        )

    def validate(self, *, check_source_hashes: bool = True) -> ValidationReport:
        report = ValidationReport()
        self._validate_schema(
            self.catalog,
            self.catalog_schema,
            "catalog.json",
            report,
        )
        self._validate_catalog(report)
        self._validate_migration_matrix(report)
        for ruleset_id, payload in self.rulesets.items():
            location = self._relative(self.entry_paths[ruleset_id])
            self._validate_schema(payload, self.ruleset_schema, location, report)
            self._validate_ruleset(
                ruleset_id,
                payload,
                location,
                report,
                check_source_hashes=check_source_hashes,
            )
        return report

    def _validate_migration_matrix(self, report: ValidationReport) -> None:
        matrix = self.migration_matrix
        tracks = matrix.get("tracks") if isinstance(matrix, dict) else None
        if not isinstance(tracks, list):
            report.add("error", "missing_migration_matrix", "migration_matrix.json", "tracks must be an array")
            return
        ids = [
            str(track.get("competition_id") or "")
            for track in tracks
            if isinstance(track, dict)
        ]
        expected_count = matrix.get("expected_track_count")
        if expected_count != len(tracks):
            report.add(
                "error",
                "migration_count",
                "migration_matrix.json",
                f"expected_track_count={expected_count}, actual={len(tracks)}",
            )
        duplicates = sorted(value for value, count in Counter(ids).items() if count > 1)
        if duplicates:
            report.add("error", "migration_duplicates", "migration_matrix.json", ", ".join(duplicates))

        index_path = self.project_root / "data" / "benchmarks" / "index.json"
        if index_path.is_file():
            index = _read_json(index_path)
            index_ids = {
                str(item.get("id"))
                for item in (index.get("olympiads") or [])
                if isinstance(item, dict)
            }
            matrix_ids = set(ids)
            if matrix_ids != index_ids:
                report.add(
                    "error",
                    "migration_coverage",
                    "migration_matrix.json",
                    f"missing={sorted(index_ids - matrix_ids)}, extra={sorted(matrix_ids - index_ids)}",
                )

        draft_ids = {
            str(track.get("competition_id"))
            for track in tracks
            if isinstance(track, dict) and track.get("draft_example") is True
        }
        scope = set(self.catalog.get("draft_scope") or [])
        if draft_ids != scope:
            report.add(
                "error",
                "draft_scope_matrix",
                "migration_matrix.json",
                f"draft examples={sorted(draft_ids)}, catalog scope={sorted(scope)}",
            )

        for index, track in enumerate(tracks):
            if not isinstance(track, dict):
                report.add("error", "migration_track", f"migration_matrix.json:$.tracks[{index}]", "must be an object")
                continue
            missing = [
                key
                for key in (
                    "competition_id",
                    "priority",
                    "proposed_profile",
                    "draft_example",
                    "evaluator_plan",
                    "actions",
                )
                if key not in track
            ]
            if missing:
                report.add(
                    "error",
                    "migration_track",
                    f"migration_matrix.json:$.tracks[{index}]",
                    "missing " + ", ".join(missing),
                )
            if track.get("priority") not in {"P0", "P1", "P2"}:
                report.add("error", "migration_priority", f"migration_matrix.json:$.tracks[{index}]", str(track.get("priority")))
            if track.get("proposed_profile") not in {
                "official_equivalent",
                "benchmark_native",
                "proxy",
                "non_comparable",
            }:
                report.add("error", "migration_profile", f"migration_matrix.json:$.tracks[{index}]", str(track.get("proposed_profile")))
            if not isinstance(track.get("actions"), list) or not track.get("actions"):
                report.add("error", "migration_actions", f"migration_matrix.json:$.tracks[{index}]", "actions must be non-empty")

    def audit_benchmarks(self, benchmark_root: str | Path) -> BenchmarkAudit:
        root = Path(benchmark_root).resolve()
        checked = 0
        resolved = 0
        failures: Counter[tuple[str, str]] = Counter()
        examples: dict[tuple[str, str], str] = {}

        for competition_id in self.catalog.get("draft_scope") or []:
            benchmark_path = root / competition_id / "benchmark.json"
            if not benchmark_path.is_file():
                failures[(competition_id, "benchmark.json missing")] += 1
                continue
            payload = _read_json(benchmark_path)
            rows = payload if isinstance(payload, list) else payload.get("problems") or []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                task = dict(row)
                task["competition_id"] = competition_id
                problem_id = str(task.get("problem_id") or task.get("id") or "<unknown>")
                checked += 1
                try:
                    self.resolve(task)
                    resolved += 1
                except RulesV2Error as exc:
                    key = (competition_id, str(exc))
                    failures[key] += 1
                    examples.setdefault(key, problem_id)

        rendered = tuple(
            {
                "competition_id": competition_id,
                "count": count,
                "example_problem_id": examples.get((competition_id, message)),
                "message": message,
            }
            for (competition_id, message), count in sorted(failures.items())
        )
        return BenchmarkAudit(checked, resolved, rendered)

    def _validate_schema(
        self,
        payload: Any,
        schema: dict[str, Any],
        location: str,
        report: ValidationReport,
    ) -> None:
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path)):
            report.add(
                "error",
                "schema",
                f"{location}:{_json_path(error.path)}",
                error.message,
            )

    def _validate_catalog(self, report: ValidationReport) -> None:
        ids: list[str] = []
        paths: list[str] = []
        scope = set(self.catalog.get("draft_scope") or [])
        entry_competitions: set[str] = set()

        for index, entry in enumerate(self.entries):
            location = f"catalog.json:$.entries[{index}]"
            if not isinstance(entry, dict):
                continue
            ruleset_id = str(entry.get("ruleset_id") or "")
            relative = str(entry.get("path") or "")
            competition_id = str(entry.get("competition_id") or "")
            ids.append(ruleset_id)
            paths.append(relative)
            entry_competitions.add(competition_id)

            path = self.entry_paths.get(ruleset_id)
            if path is None or not _inside(path, self.root):
                report.add("error", "unsafe_path", location, f"Path escapes draft root: {relative}")
            elif not path.is_file():
                report.add("error", "missing_ruleset", location, f"Missing ruleset file: {relative}")

            payload = self.rulesets.get(ruleset_id)
            if payload is None:
                continue
            if payload.get("ruleset_id") != ruleset_id:
                report.add("error", "catalog_mismatch", location, "ruleset_id differs from file")
            if payload.get("competition_id") != competition_id:
                report.add("error", "catalog_mismatch", location, "competition_id differs from file")
            if (payload.get("applicability") or {}).get("selector") != (entry.get("selector") or {}):
                report.add("error", "catalog_mismatch", location, "selector differs from file applicability")

        for duplicate in sorted(value for value, count in Counter(ids).items() if count > 1):
            report.add("error", "duplicate_ruleset_id", "catalog.json", duplicate)
        for duplicate in sorted(value for value, count in Counter(paths).items() if count > 1):
            report.add("error", "duplicate_ruleset_path", "catalog.json", duplicate)
        if scope != entry_competitions:
            report.add(
                "error",
                "scope_mismatch",
                "catalog.json",
                f"draft_scope={sorted(scope)} but entries cover {sorted(entry_competitions)}",
            )

        entries = [entry for entry in self.entries if isinstance(entry, dict)]
        for left_index, left in enumerate(entries):
            for right in entries[left_index + 1 :]:
                if left.get("competition_id") != right.get("competition_id"):
                    continue
                left_selector = left.get("selector") or {}
                right_selector = right.get("selector") or {}
                if len(left_selector) != len(right_selector):
                    continue
                common = set(left_selector) & set(right_selector)
                compatible = all(left_selector[key] == right_selector[key] for key in common)
                if compatible:
                    report.add(
                        "error",
                        "ambiguous_selector",
                        "catalog.json",
                        f"{left.get('ruleset_id')} overlaps {right.get('ruleset_id')} at equal specificity",
                    )

    def _validate_ruleset(
        self,
        ruleset_id: str,
        payload: dict[str, Any],
        location: str,
        report: ValidationReport,
        *,
        check_source_hashes: bool,
    ) -> None:
        team = payload.get("team") or {}
        try:
            minimum = int(team["active_min"])
            default = int(team["active_default"])
            maximum = int(team["active_max"])
        except (KeyError, TypeError, ValueError):
            return
        if not minimum <= default <= maximum:
            report.add("error", "team_range", location, "Require active_min <= active_default <= active_max")

        required_roles = team.get("required_roles") or []
        role_ids = [role.get("role_id") for role in required_roles if isinstance(role, dict)]
        if len(role_ids) != len(set(role_ids)):
            report.add("error", "duplicate_role", location, "required role IDs must be unique")
        if len(required_roles) > minimum:
            report.add(
                "error",
                "roster_minimum",
                location,
                f"{len(required_roles)} required roles cannot fit active_min={minimum}",
            )
        if maximum > len(required_roles) and not team.get("fill_role"):
            report.add("error", "missing_fill_role", location, "Variable roster requires fill_role")
        if not any(bool(role.get("may_submit")) for role in required_roles) and not bool(
            (team.get("fill_role") or {}).get("may_submit")
        ):
            report.add("error", "no_submitter", location, "At least one generated role must submit")
        for size in sorted({minimum, default, maximum}):
            try:
                self._generate_roster(payload, size)
            except RulesV2Error as exc:
                report.add("error", "roster_generation", location, str(exc))

        collaboration = payload.get("collaboration") or {}
        if team.get("topology") != collaboration.get("topology"):
            report.add("error", "topology_mismatch", location, "team and collaboration topology differ")
        self._validate_coalitions(team, collaboration, location, report)

        source_ids = {
            source.get("source_id")
            for source in (payload.get("provenance") or {}).get("sources") or []
            if isinstance(source, dict)
        }
        if len(source_ids) != len((payload.get("provenance") or {}).get("sources") or []):
            report.add("error", "duplicate_source", location, "source IDs must be unique")

        for name, resource in (payload.get("resource_policy") or {}).items():
            if not isinstance(resource, dict):
                continue
            self._check_source_refs(
                resource.get("source_refs") or [], source_ids, location, f"resource_policy.{name}", report
            )
            if resource.get("access") == "shared_capacity" and not resource.get("capacity"):
                report.add("error", "missing_capacity", location, f"{name} requires capacity")

        constraint_ids: list[str] = []
        waived_constraints = 0
        for constraint in payload.get("constraints") or []:
            if not isinstance(constraint, dict):
                continue
            constraint_ids.append(str(constraint.get("id")))
            refs = constraint.get("source_refs") or []
            self._check_source_refs(refs, source_ids, location, f"constraint.{constraint.get('id')}", report)
            if constraint.get("authority") in {"official", "eligibility"} and not refs:
                report.add(
                    "error",
                    "unsourced_official_constraint",
                    location,
                    str(constraint.get("id")),
                )
            if constraint.get("waived_for_agents"):
                waived_constraints += 1
                if not constraint.get("waiver_reason"):
                    report.add("error", "missing_waiver_reason", location, str(constraint.get("id")))
            self._check_text_policy_consistency(payload, constraint, location, report)
        for duplicate in sorted(value for value, count in Counter(constraint_ids).items() if count > 1):
            report.add("error", "duplicate_constraint", location, duplicate)

        comparability = payload.get("comparability") or {}
        waivers = comparability.get("waivers") or []
        if waived_constraints and not waivers:
            report.add("error", "unreported_waiver", location, "Waived constraints require comparability.waivers")
        self._validate_profile(payload, location, report)
        self._validate_evaluation(payload, location, report)
        self._validate_sources(payload, location, report, check_hashes=check_source_hashes)

    def _validate_coalitions(
        self,
        team: dict[str, Any],
        collaboration: dict[str, Any],
        location: str,
        report: ValidationReport,
    ) -> None:
        coalitions = collaboration.get("coalitions") or []
        topology = collaboration.get("topology")
        if topology != "multi_coalition":
            if coalitions:
                report.add("error", "unexpected_coalitions", location, "Only multi_coalition may define coalitions")
            return
        if len(coalitions) < 2:
            report.add("error", "coalition_count", location, "multi_coalition requires at least two coalitions")
        if team.get("fill_role"):
            report.add("error", "coalition_fill_role", location, "multi_coalition draft requires explicit roles")
        expected = {
            role.get("role_id")
            for role in team.get("required_roles") or []
            if isinstance(role, dict)
        }
        assigned: list[str] = []
        for coalition in coalitions:
            if isinstance(coalition, dict):
                assigned.extend(str(item) for item in coalition.get("member_role_ids") or [])
        if set(assigned) != expected or len(assigned) != len(set(assigned)):
            report.add(
                "error",
                "coalition_membership",
                location,
                "Every explicit role must belong to exactly one coalition",
            )

    def _validate_profile(
        self,
        payload: dict[str, Any],
        location: str,
        report: ValidationReport,
    ) -> None:
        profile = payload.get("profile")
        comparability = payload.get("comparability") or {}
        overall = comparability.get("overall")
        dimensions = comparability.get("dimensions") or {}
        waivers = comparability.get("waivers") or []
        unsupported = comparability.get("unsupported_mechanisms") or []
        missing_state = [
            item
            for item in (payload.get("execution") or {}).get("state_requirements") or []
            if item.get("required_for_official_equivalence")
            and item.get("status") != "enforced"
        ]
        if profile == "official_equivalent":
            non_equivalent = {
                key: value
                for key, value in dimensions.items()
                if value not in {"equivalent", "not_applicable"}
            }
            if overall != "equivalent" or non_equivalent or waivers or unsupported or missing_state:
                report.add(
                    "error",
                    "false_official_equivalence",
                    location,
                    "official_equivalent requires all dimensions equivalent, no waivers, no unsupported mechanisms, and all required state enforced",
                )
        if profile == "proxy" and overall not in {"proxy", "draft"}:
            report.add("error", "profile_overall", location, "proxy profile requires proxy/draft overall")
        if profile == "non_comparable" and overall != "non_comparable":
            report.add("error", "profile_overall", location, "non_comparable profile requires matching overall")

    def _validate_evaluation(
        self,
        payload: dict[str, Any],
        location: str,
        report: ValidationReport,
    ) -> None:
        evaluation = payload.get("evaluation") or {}
        status = evaluation.get("status")
        evaluator_id = evaluation.get("evaluator_id")
        if status in {"ready", "ready_with_limitations", "deferred"} and not evaluator_id:
            report.add("error", "missing_evaluator", location, f"status={status} requires evaluator_id")
        if status == "unassigned" and evaluator_id:
            report.add("error", "unexpected_evaluator", location, "unassigned status requires null evaluator_id")
        rubric_path = evaluation.get("rubric_path")
        if rubric_path:
            path = (self.project_root / rubric_path).resolve()
            if not _inside(path, self.project_root) or not path.is_file():
                report.add("error", "missing_rubric", location, str(rubric_path))

    def _validate_sources(
        self,
        payload: dict[str, Any],
        location: str,
        report: ValidationReport,
        *,
        check_hashes: bool,
    ) -> None:
        for source in (payload.get("provenance") or {}).get("sources") or []:
            if not isinstance(source, dict):
                continue
            source_id = str(source.get("source_id") or "<unknown>")
            snapshot = source.get("snapshot_status")
            local_path = source.get("local_path")
            expected_hash = source.get("sha256")
            if snapshot == "archived" and (not local_path or not expected_hash):
                report.add(
                    "error",
                    "incomplete_snapshot",
                    location,
                    f"{source_id} must include local_path and sha256",
                )
                continue
            if not local_path:
                continue
            path = (self.project_root / str(local_path)).resolve()
            if not _inside(path, self.project_root) or not path.is_file():
                report.add("error", "missing_source_snapshot", location, f"{source_id}: {local_path}")
                continue
            if check_hashes and expected_hash:
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                if actual != expected_hash:
                    report.add(
                        "error",
                        "source_hash_mismatch",
                        location,
                        f"{source_id}: expected {expected_hash}, got {actual}",
                    )

    def _check_source_refs(
        self,
        refs: Iterable[str],
        source_ids: set[Any],
        location: str,
        owner: str,
        report: ValidationReport,
    ) -> None:
        unknown = sorted(set(refs) - source_ids)
        if unknown:
            report.add("error", "unknown_source_ref", location, f"{owner}: {', '.join(unknown)}")

    def _check_text_policy_consistency(
        self,
        payload: dict[str, Any],
        constraint: dict[str, Any],
        location: str,
        report: ValidationReport,
    ) -> None:
        statement = str(constraint.get("statement") or "").lower()
        negative = re.search(r"\b(forbidden|prohibited|not allowed|no internet|may not use)\b", statement)
        if not negative:
            return
        for resource_name in ("internet", "code_execution", "generative_ai"):
            label = resource_name.replace("_", " ")
            if label not in statement and not (
                resource_name == "code_execution" and "code" in statement
            ):
                continue
            access = ((payload.get("resource_policy") or {}).get(resource_name) or {}).get("access")
            if access == "allowed":
                report.add(
                    "error",
                    "text_policy_conflict",
                    location,
                    f"{constraint.get('id')} forbids {resource_name} but resource policy allows it",
                )

    def _generate_roster(self, payload: dict[str, Any], team_size: int) -> list[dict[str, Any]]:
        team = payload.get("team") or {}
        minimum = int(team.get("active_min", 0))
        maximum = int(team.get("active_max", 0))
        if not minimum <= team_size <= maximum:
            raise RulesV2Error(
                f"team_size={team_size} is outside {payload.get('ruleset_id')} range {minimum}-{maximum}"
            )
        roles = list(team.get("required_roles") or [])
        if len(roles) > team_size:
            raise RulesV2Error(
                f"{payload.get('ruleset_id')} has {len(roles)} required roles but team_size={team_size}"
            )
        fill = team.get("fill_role")
        if len(roles) < team_size and not isinstance(fill, dict):
            raise RulesV2Error(
                f"{payload.get('ruleset_id')} needs fill_role for team_size={team_size}"
            )

        expanded: list[dict[str, Any]] = []
        for index, role in enumerate(roles, start=1):
            expanded.append(self._render_role(role, index, role_id=str(role["role_id"])))
        fill_index = 1
        while len(expanded) < team_size:
            assert isinstance(fill, dict)
            role_id = f"{fill['role_id']}_{fill_index}"
            expanded.append(self._render_role(fill, len(expanded) + 1, role_id=role_id))
            fill_index += 1
        return expanded

    @staticmethod
    def _render_role(role: Mapping[str, Any], agent_index: int, *, role_id: str) -> dict[str, Any]:
        return {
            "agent_name": f"Agent_{agent_index}",
            "role_id": role_id,
            "source_role_id": str(role["role_id"]),
            "title": str(role["title"]),
            "duties": list(role.get("duties") or []),
            "may_submit": bool(role.get("may_submit")),
        }

    @staticmethod
    def _task_team_size(task: Mapping[str, Any], payload: Mapping[str, Any]) -> int:
        raw = task.get("team_size")
        if isinstance(raw, int) and raw > 0:
            return raw
        if isinstance(raw, str) and raw.strip().isdigit():
            return int(raw.strip())
        return int((payload.get("team") or {})["active_default"])

    def _relative(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)
