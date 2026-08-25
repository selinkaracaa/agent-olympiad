from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Literal

from deliberation import DeliberationLedger
from env import OlympiadEnvironment
from llm import QueryFn, make_perplexity_caller, make_tinker_caller
from rules.models import AgentRole, RuleCard
from rules.views import agent_view


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROBLEM = "icpc_wf_2016_ceiling"
DEFAULT_MODEL = "openai/gpt-5.4-mini"
MAX_CODE_CHARS = 20_000

MemoryKind = Literal["note", "tool_observation"]
MemoryScope = Literal["private", "shared", "all"]

_TERM_RE = re.compile(r"[a-zA-Z0-9_]+")
_JSON_DECODER = json.JSONDecoder()


def _terms(text: str) -> set[str]:
    return {term.lower() for term in _TERM_RE.findall(text) if len(term) > 1}


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _bullets(items: Iterable[str]) -> str:
    values = [str(item).strip() for item in items if str(item).strip()]
    return "\n".join(f"- {item}" for item in values) or "- (none listed)"


PENALTY_MINUTES_PER_REJECTION = 20
PENALIZED_VERDICTS = frozenset({"WA", "RE", "TLE"})


def _normalize_io(text: str) -> str:
    lines = [line.rstrip() for line in str(text).replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def parse_public_samples(text: str) -> list[tuple[str, str]]:
    """Split Kattis-style 'Sample Input N' / 'Sample Output N' blocks."""

    text = str(text or "").replace("\r\n", "\n")
    chunks = re.split(r"Sample Input\s+\d+", text, flags=re.IGNORECASE)
    samples: list[tuple[str, str]] = []
    for chunk in chunks[1:]:
        pieces = re.split(r"Sample Output\s+\d+", chunk, maxsplit=1, flags=re.IGNORECASE)
        if len(pieces) != 2:
            continue
        prelude, rest = pieces[0].strip(), pieces[1].strip()
        if prelude:
            stdin, stdout = prelude, rest
        else:
            blocks = re.split(r"\n\s*\n", rest, maxsplit=1)
            if len(blocks) != 2:
                continue
            stdin, stdout = blocks[0].strip(), blocks[1].strip()
        stdout = re.split(
            r"\n\s*Sample Input\s+\d+",
            stdout,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0].strip()
        if stdin and stdout:
            samples.append((stdin, stdout))
    return samples


def samples_for_env(env: OlympiadEnvironment) -> list[tuple[str, str]]:
    samples = parse_public_samples(str(env.problem_data.get("problem_description") or ""))
    if samples:
        return samples
    source = env.problem_data.get("source_file")
    if source:
        path = REPO_ROOT / str(source)
        if path.is_file():
            return parse_public_samples(path.read_text(encoding="utf-8"))
    return []


def judge_python(
    env: OlympiadEnvironment,
    code: str,
    samples: list[tuple[str, str]],
) -> tuple[str, str]:
    if not samples:
        return "RE", "sample-judge: no public samples parsed"
    syntax = env._validate_isolated_code(  # noqa: SLF001
        code, extra_modules=frozenset({"sys"})
    )
    if syntax:
        return "CE", f"sample-judge: {syntax}"
    for index, (stdin, expected) in enumerate(samples, start=1):
        result = env._run_code(  # noqa: SLF001
            code,
            isolated=True,
            stdin=stdin,
            extra_modules=frozenset({"sys"}),
        )
        if "timed out" in result:
            return "TLE", f"sample-judge: TLE on sample {index}"
        if result.startswith("Code error"):
            return "RE", f"sample-judge: RE on sample {index}: {result[:240]}"
        got = result.removeprefix("Code output:\n")
        if _normalize_io(got) != _normalize_io(expected):
            return (
                "WA",
                f"sample-judge: WA on sample {index} expected {expected!r} got {got!r}",
            )
    return "AC", f"sample-judge: AC on {len(samples)} samples"


def _render_contest_rules(card: RuleCard, *, team_size: int) -> str:
    """Render the full contestant-visible rule packet. Hidden eval stays out."""

    view = agent_view(card, team_size=team_size)
    section_blocks = []
    for name, items in sorted((view.get("rule_sections") or {}).items()):
        section_blocks.append(
            f"{name.replace('_', ' ').title()}\n{_bullets(items)}"
        )
    sections = "\n\n".join(section_blocks) or "(none)"
    return f"""CONTEST RULE PACKET (always binding; complete contestant-visible copy)

PROFILE
{view["profile"]} ({view["protocol"]})

RULES TEXT
{view["rules_text"]}

HUMAN CONTEST RULES
{_bullets(view.get("human_constraints") or [])}

AGENT COLLABORATION RULES
{_bullets(view.get("agent_constraints") or [])}

RESOURCES
{_json(view.get("resources") or {})}

INFORMATION POLICY
{_json(view.get("information_policy") or {})}

ROLES
{_json(view.get("agent_roles") or [])}

RULE SECTIONS
{sections}

ANSWER FORMAT
{view.get("answer_format") or "(none)"}

DELIVERABLE
{_json(view.get("deliverable") or {})}

DELIBERATION
{_json(view.get("deliberation") or {})}

COMMUNICATION
{_json(view.get("communication") or {})}

SIMULATION
{_json(view.get("simulation") or {})}

COMPARABILITY
{_json(view.get("comparability") or {})}
"""


@dataclass(frozen=True)
class MemoryItem:
    memory_id: str
    owner: str
    kind: MemoryKind
    content: str
    created_turn: int
    content_hash: str
    shared: bool = False
    source_memory_id: str | None = None


class MemoryStore:
    """Structured private/shared memory for notes and tool observations."""

    def __init__(self, agent_names: Iterable[str]):
        self.private: dict[str, dict[str, MemoryItem]] = {
            agent_name: {} for agent_name in agent_names
        }
        self.shared: dict[str, MemoryItem] = {}
        self._private_counter = 0
        self._shared_counter = 0

    def _next_private_id(self) -> str:
        self._private_counter += 1
        return f"M{self._private_counter}"

    def _next_shared_id(self) -> str:
        self._shared_counter += 1
        return f"S{self._shared_counter}"

    def _require_agent(self, agent_name: str) -> dict[str, MemoryItem]:
        if agent_name not in self.private:
            raise KeyError(f"Unknown memory owner: {agent_name}")
        return self.private[agent_name]

    def add(
        self,
        agent_name: str,
        content: str,
        *,
        turn: int,
        kind: MemoryKind = "note",
    ) -> MemoryItem:
        memories = self._require_agent(agent_name)
        content = str(content or "").strip()
        if not content:
            raise ValueError("Memory content cannot be empty.")
        item = MemoryItem(
            memory_id=self._next_private_id(),
            owner=agent_name,
            kind=kind,
            content=content,
            created_turn=turn,
            content_hash=_digest(content),
        )
        memories[item.memory_id] = item
        return item

    def publish(
        self,
        agent_name: str,
        memory_ids: Iterable[str],
        *,
        turn: int,
    ) -> list[MemoryItem]:
        memories = self._require_agent(agent_name)
        published: list[MemoryItem] = []
        for memory_id in memory_ids:
            memory_id = str(memory_id).strip()
            source = memories.get(memory_id)
            if source is None:
                raise KeyError(f"{agent_name} does not own memory {memory_id!r}.")
            existing = next(
                (
                    item
                    for item in self.shared.values()
                    if item.source_memory_id == source.memory_id
                    and item.owner == agent_name
                    and item.content_hash == source.content_hash
                ),
                None,
            )
            if existing is not None:
                published.append(existing)
                continue
            shared_item = replace(
                source,
                memory_id=self._next_shared_id(),
                created_turn=turn,
                shared=True,
                source_memory_id=source.memory_id,
            )
            self.shared[shared_item.memory_id] = shared_item
            published.append(shared_item)
        return published

    @staticmethod
    def _rank(item: MemoryItem, query_terms: set[str]) -> tuple[int, int]:
        haystack = item.content.lower()
        score = sum(1 for token in query_terms if token in haystack)
        return score, item.created_turn

    def recall(
        self,
        agent_name: str,
        query: str = "",
        *,
        scope: MemoryScope = "all",
        top_k: int | None = 8,
    ) -> list[MemoryItem]:
        memories = self._require_agent(agent_name)
        candidates: list[MemoryItem] = []
        if scope in {"private", "all"}:
            candidates.extend(memories.values())
        if scope in {"shared", "all"}:
            candidates.extend(self.shared.values())
        query_terms = _terms(query)
        candidates.sort(key=lambda item: self._rank(item, query_terms), reverse=True)

        selected: list[MemoryItem] = []
        seen: set[str] = set()
        for item in candidates:
            if item.content_hash in seen:
                continue
            selected.append(item)
            seen.add(item.content_hash)
            if top_k is not None and len(selected) >= max(1, int(top_k)):
                break
        return selected

    @staticmethod
    def render(items: Iterable[MemoryItem]) -> str:
        rows = []
        for item in items:
            rows.append(
                f"[{item.memory_id}] kind={item.kind} owner={item.owner}\n"
                f"{item.content}"
            )
        return "\n\n".join(rows) or "(none)"

    def snapshot(self) -> dict[str, Any]:
        return {
            "private": {
                agent_name: [asdict(item) for item in memories.values()]
                for agent_name, memories in self.private.items()
            },
            "shared": [asdict(item) for item in self.shared.values()],
        }


@dataclass
class WorkstationLease:
    """One-owner lease used to hard-enforce the ICPC shared workstation."""

    owner: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)

    def acquire(self, agent_name: str, *, turn: int) -> str:
        if self.owner == agent_name:
            return f"WORKSTATION: {agent_name} already owns the lease."
        if self.owner is not None:
            return f"WORKSTATION DENIED: currently owned by {self.owner}."
        self.owner = agent_name
        self.history.append({"turn": turn, "action": "acquire", "agent": agent_name})
        return f"WORKSTATION ACQUIRED: owner={agent_name}."

    def release(self, agent_name: str, *, turn: int) -> str:
        if self.owner != agent_name:
            return (
                "WORKSTATION DENIED: only the current owner may release it; "
                f"owner={self.owner or 'none'}."
            )
        self.history.append({"turn": turn, "action": "release", "agent": agent_name})
        self.owner = None
        return "WORKSTATION RELEASED: owner=none."


@dataclass
class ScoreboardRun:
    run_id: str
    problem_id: str
    turn: int
    agent: str
    verdict: str | None
    detail: str
    pending: bool
    code: str = field(repr=False, default="")


class Scoreboard:
    """One-team sample-judge scoreboard. Not official hidden-test ranking."""

    def __init__(self, problem_id: str, samples: list[tuple[str, str]]):
        self.problem_id = problem_id
        self.samples = samples
        self.runs: list[ScoreboardRun] = []
        self.pending: ScoreboardRun | None = None
        self.status = "unattempted"
        self.first_ac_turn: int | None = None
        self._next_id = 0

    def submit(self, agent_name: str, turn: int, code: str) -> ScoreboardRun:
        if self.pending is not None:
            raise ValueError("A sample-judge run is still pending.")
        if self.accepted_run() is not None:
            raise ValueError("This problem is already AC on sample-judge.")
        self._next_id += 1
        run = ScoreboardRun(
            run_id=f"R{self._next_id}",
            problem_id=self.problem_id,
            turn=turn,
            agent=agent_name,
            verdict=None,
            detail="pending sample-judge",
            pending=True,
            code=code,
        )
        self.pending = run
        self.status = "pending"
        return run

    def resolve(self, env: OlympiadEnvironment) -> ScoreboardRun | None:
        run = self.pending
        if run is None:
            return None
        verdict, detail = judge_python(env, run.code, self.samples)
        run.verdict = verdict
        run.detail = detail
        run.pending = False
        self.pending = None
        self.runs.append(run)
        if verdict == "AC":
            if self.first_ac_turn is None:
                self.first_ac_turn = run.turn
            self.status = "AC"
        elif self.first_ac_turn is None:
            self.status = verdict
        return run

    def record_immediate(
        self,
        env: OlympiadEnvironment,
        agent_name: str,
        turn: int,
        code: str,
    ) -> ScoreboardRun:
        self._next_id += 1
        verdict, detail = judge_python(env, code, self.samples)
        run = ScoreboardRun(
            run_id=f"R{self._next_id}",
            problem_id=self.problem_id,
            turn=turn,
            agent=agent_name,
            verdict=verdict,
            detail=detail,
            pending=False,
            code=code,
        )
        self.runs.append(run)
        if verdict == "AC":
            if self.first_ac_turn is None:
                self.first_ac_turn = turn
            self.status = "AC"
        elif self.first_ac_turn is None:
            self.status = verdict
        return run

    def penalized_rejections(self) -> int:
        cutoff = self.first_ac_turn
        count = 0
        for run in self.runs:
            if run.verdict not in PENALIZED_VERDICTS:
                continue
            if cutoff is None or run.turn < cutoff:
                count += 1
        return count

    def penalty(self) -> int:
        if self.first_ac_turn is None:
            return 0
        return self.first_ac_turn + PENALTY_MINUTES_PER_REJECTION * self.penalized_rejections()

    def solved(self) -> int:
        return 1 if self.first_ac_turn is not None else 0

    def accepted_run(self) -> ScoreboardRun | None:
        return next((run for run in self.runs if run.verdict == "AC"), None)

    def verdict_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for run in self.runs:
            if run.verdict:
                counts[run.verdict] = counts.get(run.verdict, 0) + 1
        return counts

    def render(self) -> str:
        counts = self.verdict_counts()
        pending = self.pending.run_id if self.pending else "none"
        rows = [
            "=== LIVE SCOREBOARD (sample-judge) ===",
            f"solved={self.solved()}  penalty={self.penalty()}",
            (
                f"{self.problem_id}  {self.status}  "
                f"attempts={len(self.runs)} "
                f"(WA={counts.get('WA', 0)} CE={counts.get('CE', 0)} "
                f"RE={counts.get('RE', 0)} TLE={counts.get('TLE', 0)})  "
                f"pending={pending}"
            ),
        ]
        for run in self.runs[-6:]:
            rows.append(
                f"{run.run_id} T{run.turn} {run.agent} {run.verdict} {run.detail}"
            )
        if self.pending is not None:
            rows.append(
                f"{self.pending.run_id} T{self.pending.turn} {self.pending.agent} PENDING"
            )
        return "\n".join(rows)

    def snapshot(self) -> dict[str, Any]:
        return {
            "judge": "sample-judge",
            "problem_id": self.problem_id,
            "sample_count": len(self.samples),
            "status": self.status,
            "solved": self.solved(),
            "penalty": self.penalty(),
            "first_ac_turn": self.first_ac_turn,
            "penalized_rejections": self.penalized_rejections(),
            "attempts": len(self.runs),
            "verdicts": self.verdict_counts(),
            "pending": None
            if self.pending is None
            else {
                "run_id": self.pending.run_id,
                "turn": self.pending.turn,
                "agent": self.pending.agent,
            },
            "runs": [
                {
                    "run_id": run.run_id,
                    "turn": run.turn,
                    "agent": run.agent,
                    "verdict": run.verdict,
                    "detail": run.detail,
                }
                for run in self.runs
            ],
        }


@dataclass(frozen=True)
class ToolOutcome:
    message: str
    terminal: bool = False


class RuleSession:
    """Joins in-prompt contest rules, memory, debate, and prompt assembly.

    Callers need only two operations: request ``context_for`` and submit a
    parsed command to ``apply``.  The implementation owns shared-memory
    publication, workstation enforcement, debate invariants, and complete
    context construction without local token or character truncation.
    """

    def __init__(
        self,
        env: OlympiadEnvironment,
    ):
        if env.competition_id != "icpc" or env.rule_card is None:
            raise ValueError("RuleSession requires an ICPC environment with a rule card.")
        self.env = env
        self.card = env.rule_card
        self.roles = self.card.roster(env.team_size)
        self.role_by_name = {role.name: role for role in self.roles}
        self.submitter = self.roles[0].name
        self.contest_rules = _render_contest_rules(self.card, team_size=env.team_size)
        self.memory = MemoryStore(self.role_by_name)
        self.debate = DeliberationLedger()
        self.workstation = WorkstationLease()
        self.scoreboard = Scoreboard(
            str(env.problem_data.get("problem_id") or env.problem_id),
            samples_for_env(env),
        )
        self.turn = 0
        self.team_events: list[dict[str, Any]] = []
        self.action_events: list[dict[str, Any]] = []
        self.context_metrics: list[dict[str, Any]] = []
        self.focus: dict[str, str] = {agent_name: "unassigned" for agent_name in self.role_by_name}

    def _role(self, agent_name: str) -> AgentRole:
        try:
            return self.role_by_name[agent_name]
        except KeyError as exc:
            raise KeyError(f"Unknown ICPC agent: {agent_name}") from exc

    def _constitution(self, agent_name: str) -> str:
        role = self._role(agent_name)
        duties = _bullets(role.duties)
        return f"""ICPC RULE SESSION
AGENT_ID={agent_name}
OFFICIAL_ROLE={role.title}
TEMPORARY_FOCUS={self.focus[agent_name]}

OPERATING CONSTRAINTS
- You are one of exactly {self.env.team_size} equal ICPC contestants.
- Public Internet, outside problem-solving help, and hidden solutions are forbidden.
- Only the explicit shared-workstation lease owner may execute code.
- Private memory is not team knowledge until it is deliberately published.
- The CONTEST RULE PACKET below is complete and always binding.
- Debate claims should cite the rule packet, code observations, or explicit reasoning.
- Available environment tool: execute_code.

{self.contest_rules}

ROLE DUTIES
{duties}
"""

    @staticmethod
    def _action_interface() -> str:
        return """ACTION INTERFACE
Return exactly one JSON object. Use one of:
{"action":"memory_note","content":"your interpretation or algorithm note"}
{"action":"memory_recall","query":"workstation","scope":"all"}
{"action":"memory_publish","memory_ids":["M1"]}
{"action":"set_focus","content":"temporary task focus"}
{"action":"workstation_acquire"}
{"action":"execute_code","code":"import sys\\nprint(sys.stdin.read())","stdin":"sample input"}
{"action":"submit_run","code":"import sys\\nprint(sys.stdin.read())"}
{"action":"workstation_release"}
{"action":"propose","content":"algorithm or coordination proposal"}
{"action":"challenge","proposal_id":"P1","content":"evidence-based objection"}
{"action":"evidence","proposal_id":"P1","content":"test, rule citation, or proof"}
{"action":"revise","proposal_id":"P1","content":"revised proposal"}
{"action":"decide","proposal_id":"P1","outcome":"accept","reason":"why"}
{"action":"speak","content":"decision-relevant message to teammates"}
{"action":"done","content":"concise public summary of your completed work"}

MEMORY_*, SET_FOCUS, WORKSTATION_*, EXECUTE_CODE, and SUBMIT_RUN return an
observation to you immediately, after which you may take another action in
the same turn. PROPOSE, CHALLENGE, EVIDENCE, REVISE, DECIDE, SPEAK, and DONE
end the current public turn.
"""

    def _team_context(self) -> str:
        rows = [
            f"T{event['turn']} {event['agent']} [{event['kind']}]: {event['content']}"
            for event in self.team_events
        ]
        return "\n".join(rows) or "(none)"

    def _debate_context(self) -> str:
        compact = []
        for proposal in self.debate.proposals.values():
            compact.append(
                {
                    "proposal_id": proposal["proposal_id"],
                    "author": proposal["author"],
                    "current_claim": proposal["current_claim"],
                    "status": proposal["status"],
                    "decision_reason": proposal.get("decision_reason"),
                    "events": proposal["events"],
                }
            )
        return _json(compact) if compact else "(none)"

    @staticmethod
    def _trace_context(local_trace: list[dict[str, str]]) -> str:
        if not local_trace:
            return "(none)"
        rows = []
        for item in local_trace:
            rows.append(
                f"COMMAND: {item['command']}\n"
                f"OBSERVATION: {item['observation']}"
            )
        return "\n\n".join(rows)

    def context_for(
        self,
        agent_name: str,
        *,
        phase: str,
        local_trace: list[dict[str, str]],
    ) -> tuple[str, str]:
        role = self._role(agent_name)
        system = (
            self._constitution(agent_name)
            + f"\nPHASE={phase}\n\n"
            + self._action_interface()
        )
        problem = str(self.env.problem_data["problem_description"])
        query = " ".join(
            [
                phase,
                self.focus[agent_name],
                str(self.env.problem_data.get("title") or ""),
                " ".join(event["content"] for event in self.team_events[-3:]),
            ]
        )

        private_items = self.memory.recall(
            agent_name,
            query,
            scope="private",
            top_k=None,
        )
        shared_items = self.memory.recall(
            agent_name,
            query,
            scope="shared",
            top_k=None,
        )
        phase_instruction = {
            "explore": (
                "Inspect the problem against the contest rule packet you already have, "
                "publish useful notes, and make one algorithm or coordination contribution."
            ),
            "debate": (
                "Challenge, support, or revise open proposals using the rule packet, "
                "proofs, complexity analysis, edge cases, or executable evidence."
            ),
            "decision": (
                "Resolve open proposals only when the public ledger contains enough "
                "evidence. You are the designated decision recorder."
            ),
        }.get(phase, "Contribute evidence relevant to the current team state.")

        user = f"""=== PHASE OBJECTIVE ===
{phase_instruction}

=== PROBLEM ===
{problem}

=== YOUR STRUCTURED PRIVATE MEMORY ===
{self.memory.render(private_items)}

=== PUBLISHED TEAM MEMORY ===
{self.memory.render(shared_items)}

=== RECENT TEAM EVENTS ===
{self._team_context()}

=== DEBATE LEDGER ===
{self._debate_context()}

{self.scoreboard.render()}

=== TOOL TRACE FROM THIS TURN ===
{self._trace_context(local_trace)}

Current workstation owner: {self.workstation.owner or 'none'}
Current role: {role.title}; temporary focus: {self.focus[agent_name]}
Return one JSON action now."""
        self.context_metrics.append(
            {
                "turn": self.turn,
                "agent": agent_name,
                "phase": phase,
                "system_chars": len(system),
                "user_chars": len(user),
                "total_chars": len(system) + len(user),
                "problem_chars": len(problem),
                "private_memories": len(private_items),
                "shared_memories": len(shared_items),
            }
        )
        return system, user

    def _record_action(
        self,
        agent_name: str,
        action: str,
        command: dict[str, Any],
        result: str,
    ) -> None:
        safe_command = dict(command)
        self.action_events.append(
            {
                "turn": self.turn,
                "agent": agent_name,
                "action": action,
                "command": safe_command,
                "result": result,
            }
        )

    def _public_event(self, agent_name: str, kind: str, content: str) -> None:
        self.team_events.append(
            {
                "turn": self.turn,
                "agent": agent_name,
                "kind": kind,
                "content": content,
            }
        )

    def resolve_pending(self) -> ScoreboardRun | None:
        run = self.scoreboard.resolve(self.env)
        if run is None:
            return None
        self._public_event(
            run.agent,
            "verdict",
            f"{run.run_id} {run.verdict} {run.detail}",
        )
        return run

    @staticmethod
    def _required_text(command: dict[str, Any], key: str) -> str:
        value = str(command.get(key) or "").strip()
        if not value:
            raise ValueError(f"{key} is required and cannot be empty.")
        return value

    def apply(self, agent_name: str, command: dict[str, Any]) -> ToolOutcome:
        self._role(agent_name)
        if self.turn >= self.card.max_turns:
            return ToolOutcome(
                f"TURN LIMIT: reached {self.card.max_turns} session actions.",
                terminal=True,
            )
        self.turn += 1
        action = str(command.get("action") or "").strip().lower()
        if not action:
            action = "speak"
            command = {"action": "speak", "content": _json(command)}

        try:
            outcome = self._apply(agent_name, action, command)
        except (KeyError, TypeError, ValueError) as exc:
            outcome = ToolOutcome(f"ACTION ERROR: {exc}")
        self._record_action(agent_name, action, command, outcome.message)
        return outcome

    def _apply(
        self,
        agent_name: str,
        action: str,
        command: dict[str, Any],
    ) -> ToolOutcome:
        if action == "memory_note":
            content = self._required_text(command, "content")
            item = self.memory.add(agent_name, content, turn=self.turn, kind="note")
            return ToolOutcome(f"MEMORY STORED: {item.memory_id} (private note).")

        if action == "memory_recall":
            scope = str(command.get("scope") or "all").lower()
            if scope not in {"private", "shared", "all"}:
                raise ValueError("scope must be private, shared, or all.")
            items = self.memory.recall(
                agent_name,
                str(command.get("query") or ""),
                scope=scope,  # type: ignore[arg-type]
            )
            return ToolOutcome("MEMORY RECALL\n" + self.memory.render(items))

        if action == "memory_publish":
            memory_ids = command.get("memory_ids")
            if not isinstance(memory_ids, list) or not memory_ids:
                raise ValueError("memory_ids must be a non-empty array.")
            published = self.memory.publish(agent_name, memory_ids, turn=self.turn)
            ids = ", ".join(item.memory_id for item in published)
            self._public_event(agent_name, "memory_publish", f"published memories {ids}")
            return ToolOutcome(f"PUBLISHED MEMORY: {ids}")

        if action == "set_focus":
            focus = self._required_text(command, "content")
            self.focus[agent_name] = focus
            return ToolOutcome(f"TEMPORARY FOCUS SET: {focus}")

        if action == "workstation_acquire":
            return ToolOutcome(self.workstation.acquire(agent_name, turn=self.turn))

        if action == "workstation_release":
            return ToolOutcome(self.workstation.release(agent_name, turn=self.turn))

        if action == "execute_code":
            if self.workstation.owner != agent_name:
                return ToolOutcome(
                    "WORKSTATION DENIED: acquire the single shared workstation before "
                    f"executing code; owner={self.workstation.owner or 'none'}."
                )
            code = self._required_text(command, "code")
            if len(code) > MAX_CODE_CHARS:
                raise ValueError(f"code exceeds {MAX_CODE_CHARS} characters.")
            violation = self.env.validate_action("execute_code")
            if violation:
                return ToolOutcome(violation)
            stdin = command.get("stdin")
            if stdin is not None and not isinstance(stdin, str):
                raise ValueError("stdin must be a string when provided.")
            # Isolated Python with sys allowed so sample stdin/stdout programs can run.
            result = self.env._run_code(  # noqa: SLF001
                code,
                isolated=True,
                stdin=stdin,
                extra_modules=frozenset({"sys"}),
            )
            item = self.memory.add(
                agent_name,
                result,
                turn=self.turn,
                kind="tool_observation",
            )
            return ToolOutcome(f"{result}\nPRIVATE_MEMORY_ID={item.memory_id}")

        if action == "submit_run":
            if self.workstation.owner != agent_name:
                return ToolOutcome(
                    "WORKSTATION DENIED: acquire the single shared workstation before "
                    f"submitting a run; owner={self.workstation.owner or 'none'}."
                )
            if self.scoreboard.pending is not None:
                return ToolOutcome(
                    "SUBMIT DENIED: a run is still pending sample-judge; "
                    f"{self.scoreboard.pending.run_id}."
                )
            if self.scoreboard.accepted_run() is not None:
                return ToolOutcome(
                    "SUBMIT DENIED: this problem is already AC on sample-judge."
                )
            code = _strip_code_fence(self._required_text(command, "code"))
            if len(code) > MAX_CODE_CHARS:
                raise ValueError(f"code exceeds {MAX_CODE_CHARS} characters.")
            run = self.scoreboard.submit(agent_name, self.turn, code)
            self._public_event(
                agent_name,
                "submit_run",
                f"{run.run_id} pending sample-judge",
            )
            return ToolOutcome(
                f"RUN PENDING {run.run_id} (sample-judge; verdict next agent slot)."
            )

        debate_actions = {
            "propose": "propose",
            "challenge": "challenge",
            "evidence": "provide_evidence",
            "revise": "revise",
            "decide": "decide",
        }
        public_actions = set(debate_actions) | {"speak", "done"}
        if action in public_actions and self.workstation.owner == agent_name:
            return ToolOutcome(
                "WORKSTATION HELD: release the workstation before ending your "
                "public turn."
            )
        if action in debate_actions:
            ledger_action = debate_actions[action]
            if action == "propose":
                payload = self._required_text(command, "content")
            elif action == "decide":
                proposal_id = self._required_text(command, "proposal_id")
                outcome = self._required_text(command, "outcome")
                reason = self._required_text(command, "reason")
                payload = f"{proposal_id} | {outcome} | {reason}"
            else:
                proposal_id = self._required_text(command, "proposal_id")
                content = self._required_text(command, "content")
                payload = f"{proposal_id} | {content}"
            result = self.debate.record(
                agent_name=agent_name,
                action_type=ledger_action,
                payload=payload,
                turn=self.turn,
                may_decide=agent_name == self.submitter,
            )
            if result.startswith("Deliberation error:"):
                return ToolOutcome(result)
            self._public_event(agent_name, ledger_action, result)
            return ToolOutcome(result, terminal=True)

        if action in {"speak", "done"}:
            content = self._required_text(command, "content")
            self._public_event(agent_name, action, content)
            return ToolOutcome(f"PUBLIC {action.upper()}: {content}", terminal=True)

        raise ValueError(f"Unknown icpcrun action: {action!r}")

    def final_context(self, agent_name: str) -> tuple[str, str]:
        shared = self.memory.recall(
            agent_name,
            "algorithm proof complexity tests submission",
            scope="shared",
            top_k=None,
        )
        private = self.memory.recall(
            agent_name,
            "algorithm proof complexity tests submission",
            scope="private",
            top_k=None,
        )
        system = f"""FINAL_SYNTHESIS
You are {agent_name}, the designated ICPC source-code synthesizer.
- no Internet, outside help, or hidden solutions;
- produce one complete source file that reads stdin and writes stdout;
- do not wrap the source in Markdown fences.
- begin immediately with valid Python source (for example import, from, or def);
- never prefix the source with words such as code or python.

ANSWER FORMAT
{self.card.answer_format or "Python 3 program. Read all input from stdin and write the answer to stdout."}
"""
        problem = str(self.env.problem_data["problem_description"])
        user = f"""=== PROBLEM ===
{problem}

=== ACCEPTED AND OPEN DEBATE STATE ===
{self._debate_context()}

=== PUBLISHED TEAM MEMORY ===
{self.memory.render(shared)}

=== SYNTHESIZER PRIVATE MEMORY ===
{self.memory.render(private)}

=== RECENT TEAM EVENTS ===
{self._team_context()}

{self.scoreboard.render()}

Return only the complete source code now."""
        self.context_metrics.append(
            {
                "turn": self.turn,
                "agent": agent_name,
                "phase": "final",
                "system_chars": len(system),
                "user_chars": len(user),
                "total_chars": len(system) + len(user),
                "problem_chars": len(problem),
                "private_memories": len(private),
                "shared_memories": len(shared),
            }
        )
        return system, user

    def snapshot(self) -> dict[str, Any]:
        return {
            "rule_id": self.card.rule_id,
            "contest_rules_chars": len(self.contest_rules),
            "memory": self.memory.snapshot(),
            "debate": self.debate.report(),
            "workstation": {
                "owner": self.workstation.owner,
                "history": list(self.workstation.history),
            },
            "focus": dict(self.focus),
            "team_events": list(self.team_events),
            "action_events": list(self.action_events),
            "context_metrics": list(self.context_metrics),
            "scoreboard": self.scoreboard.snapshot(),
        }


def parse_agent_command(response: str) -> dict[str, Any]:
    """Extract the first JSON object; degrade non-JSON text to a public message."""

    text = str(response or "").strip()
    if not text:
        return {"action": "done", "content": "No contribution produced."}
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = _JSON_DECODER.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return {"action": "speak", "content": text}


def _strip_code_fence(response: str) -> str:
    text = str(response or "").strip()
    match = re.fullmatch(r"```(?:[a-zA-Z0-9_+.-]+)?\s*(.*?)\s*```", text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    for prefix in ("code", "python"):
        if not text.lower().startswith(prefix):
            continue
        candidate = text[len(prefix) :].lstrip()
        try:
            ast.parse(candidate)
        except SyntaxError:
            continue
        return candidate
    try:
        ast.parse(text)
        return text
    except SyntaxError:
        pass
    return text


class ScriptedMockLLM:
    """Deterministic mock that exercises memory and debate paths."""

    def __call__(self, system_prompt: str, user_prompt: str) -> str:
        if "FINAL_SYNTHESIS" in system_prompt:
            return (
                "import sys\n\n"
                "def solve() -> None:\n"
                "    _ = sys.stdin.read()\n"
                "    print(0)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()"
            )
        agent_match = re.search(r"AGENT_ID=(Agent_\d+)", system_prompt)
        phase_match = re.search(r"PHASE=([a-z_]+)", system_prompt)
        agent = agent_match.group(1) if agent_match else "Agent_1"
        phase = phase_match.group(1) if phase_match else "explore"

        if phase == "decision":
            return _json(
                {
                    "action": "decide",
                    "proposal_id": "P1",
                    "outcome": "accept",
                    "reason": "The proposal was revised after complexity and test evidence.",
                }
            )
        if phase == "debate":
            if agent == "Agent_1":
                return _json(
                    {
                        "action": "revise",
                        "proposal_id": "P1",
                        "content": "Use the reviewed algorithm, prove its invariant, and test edge cases before submission.",
                    }
                )
            return _json(
                {
                    "action": "speak",
                    "content": f"{agent} supports deciding P1 after explicit complexity and edge-case checks.",
                }
            )

        trace = user_prompt.split("=== TOOL TRACE FROM THIS TURN ===", 1)[-1]
        if "MEMORY STORED" not in trace:
            return _json(
                {
                    "action": "memory_note",
                    "content": f"{agent} notes a single reviewed algorithm and workstation-bounded tests.",
                }
            )
        if "PUBLISHED MEMORY" not in trace:
            ids = re.findall(r"MEMORY STORED: (M\d+)", trace)
            return _json(
                {
                    "action": "memory_publish",
                    "memory_ids": [ids[-1]] if ids else ["M1"],
                }
            )
        if agent == "Agent_1":
            return _json(
                {
                    "action": "propose",
                    "content": "Adopt a single reviewed algorithm and use the workstation only for bounded implementation tests.",
                }
            )
        if agent == "Agent_2":
            return _json(
                {
                    "action": "challenge",
                    "proposal_id": "P1",
                    "content": "The proposal needs an explicit complexity argument against the input bounds.",
                }
            )
        return _json(
            {
                "action": "evidence",
                "proposal_id": "P1",
                "content": "Contest rules and edge-case analysis support testing boundary-shaped inputs before finalization.",
            }
        )


@dataclass
class ICPCRunner:
    problem_id: str
    query_fn: QueryFn
    rounds: int = 2
    max_tool_steps: int = 6
    mode: str = "mock"
    model: str = "scripted-mock"

    def _run_agent_turn(self, session: RuleSession, agent_name: str, phase: str) -> None:
        session.resolve_pending()
        local_trace: list[dict[str, str]] = []
        for _ in range(max(1, self.max_tool_steps)):
            if session.turn >= session.card.max_turns:
                return
            system, user = session.context_for(
                agent_name,
                phase=phase,
                local_trace=local_trace,
            )
            response = self.query_fn(system, user)
            command = parse_agent_command(response)
            outcome = session.apply(agent_name, command)
            local_trace.append(
                {
                    "command": _json(command),
                    "observation": outcome.message,
                }
            )
            if outcome.terminal:
                return
        session._public_event(  # noqa: SLF001
            agent_name,
            "tool_limit",
            f"No public contribution before the {self.max_tool_steps}-step tool limit.",
        )

    def run(self) -> dict[str, Any]:
        if self.rounds < 1:
            raise ValueError("rounds must be positive.")
        env = OlympiadEnvironment("icpc", self.problem_id)
        session = RuleSession(env)

        for round_index in range(self.rounds):
            phase = "explore" if round_index == 0 else "debate"
            for role in session.roles:
                self._run_agent_turn(session, role.name, phase)

        if session.debate.report()["open_proposals"]:
            self._run_agent_turn(session, session.submitter, "decision")

        session.resolve_pending()
        accepted_run = session.scoreboard.accepted_run()
        if accepted_run is not None:
            final_answer = accepted_run.code
            final_source = f"sample-judge:{accepted_run.run_id}"
        else:
            final_system, final_user = session.final_context(session.submitter)
            try:
                final_answer = _strip_code_fence(self.query_fn(final_system, final_user))
            except RuntimeError as exc:
                if "empty message" not in str(exc).lower():
                    raise
                final_answer = _strip_code_fence(self.query_fn(final_system, final_user))
            final_source = "final_synthesis"
        submit_result = env.execute_action(session.submitter, "submit_final", final_answer)
        if not session.scoreboard.runs:
            run = session.scoreboard.record_immediate(
                env,
                session.submitter,
                session.turn,
                final_answer,
            )
            session._public_event(  # noqa: SLF001
                session.submitter,
                "verdict",
                f"{run.run_id} {run.verdict} {run.detail}",
            )
        grade = env.grade_submission()
        packet = {
            "schema_version": "icpcrun.v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "competition_id": "icpc",
            "problem_id": self.problem_id,
            "title": env.problem_data.get("title"),
            "mode": self.mode,
            "model": self.model,
            "rounds": self.rounds,
            "max_tool_steps": self.max_tool_steps,
            "submitted": env.submitted,
            "submitted_by": env.submitted_by,
            "submit_result": submit_result,
            "final_source": final_source,
            "final_answer": env.workspace.get("final_answer", ""),
            "grade": grade,
            "session": session.snapshot(),
            "environment_action_log": list(env.action_log),
            "limitations": [
                "No official hidden tests are stored in the current ICPC benchmark.",
                "programming_judge remains deferred; grade is judge_sandbox_required.",
                "execute_code is an isolated Python analysis proxy, not a multi-language judge.",
                "Scoreboard verdicts are sample-judge only, not official hidden tests.",
                "The current benchmark loads one problem rather than a complete World Finals packet.",
            ],
        }
        return packet


def _load_icpc_problem_ids() -> list[str]:
    benchmark = REPO_ROOT / "data" / "benchmarks" / "icpc" / "benchmark.json"
    payload = json.loads(benchmark.read_text(encoding="utf-8"))
    return [str(item["problem_id"]) for item in payload]


def run_self_test() -> dict[str, Any]:
    """Exercise the runner without API keys or external writes."""

    env = OlympiadEnvironment("icpc", DEFAULT_PROBLEM)
    session = RuleSession(env)
    boot_system, boot_user = session.context_for(
        "Agent_1", phase="explore", local_trace=[]
    )
    assert session.card.rules_text in boot_system
    assert session.card.human_constraints[0] in boot_system
    assert session.card.agent_constraints[0] in boot_system
    assert session.card.answer_format in boot_system
    assert "CONTEST RULE PACKET" in boot_system
    assert "RULE SECTIONS" in boot_system
    assert "evaluation_guidance" not in boot_system
    assert '"scoring"' not in boot_system
    assert session.card.rules_text not in boot_user
    assert "LIVE SCOREBOARD (sample-judge)" in boot_user
    assert "query_rules" not in boot_system
    assert "rules_read" not in boot_system
    assert "RuleVFS" not in boot_system
    assert "RULE CATALOG" not in boot_system

    note = session.apply(
        "Agent_1",
        {"action": "memory_note", "content": "Only the lease owner may execute code."},
    )
    assert "MEMORY STORED: M1" in note.message
    assert not session.memory.recall("Agent_2", "lease owner", scope="private")
    published = session.memory.publish("Agent_1", ["M1"], turn=session.turn)
    assert published and session.memory.recall(
        "Agent_2", "lease owner", scope="shared"
    )

    denied = session.apply(
        "Agent_2", {"action": "execute_code", "code": "print(45)"}
    )
    assert "WORKSTATION DENIED" in denied.message
    assert "ACQUIRED" in session.apply(
        "Agent_1", {"action": "workstation_acquire"}
    ).message
    code_result = session.apply(
        "Agent_1", {"action": "execute_code", "code": "print(sum(range(10)))"}
    )
    assert "45" in code_result.message
    stdin_result = session.apply(
        "Agent_1",
        {
            "action": "execute_code",
            "code": "import sys\nprint(sys.stdin.read().strip())",
            "stdin": "hello sample",
        },
    )
    assert "hello sample" in stdin_result.message
    held = session.apply(
        "Agent_1", {"action": "done", "content": "Leaving without release."}
    )
    assert "WORKSTATION HELD" in held.message
    assert not held.terminal
    assert session.workstation.owner == "Agent_1"
    assert "RELEASED" in session.apply(
        "Agent_1", {"action": "workstation_release"}
    ).message
    assert _strip_code_fence("codeimport sys\nprint(1)") == "import sys\nprint(1)"
    assert _strip_code_fence("python\nprint(1)") == "print(1)"

    samples = session.scoreboard.samples
    assert len(samples) == 2
    assert samples[0][1].strip() == "4"
    assert samples[1][1].strip() == "2"

    ceiling_ac = (
        "import sys\n"
        "def solve():\n"
        "    data = sys.stdin.read().strip().split()\n"
        "    if not data:\n"
        "        return\n"
        "    it = iter(data)\n"
        "    n = int(next(it)); k = int(next(it))\n"
        "    shapes = set()\n"
        "    for _ in range(n):\n"
        "        values = [int(next(it)) for _ in range(k)]\n"
        "        root = None\n"
        "        for v in values:\n"
        "            if root is None:\n"
        "                root = [v, None, None]\n"
        "            else:\n"
        "                cur = root\n"
        "                while True:\n"
        "                    if v < cur[0]:\n"
        "                        if cur[1] is None:\n"
        "                            cur[1] = [v, None, None]; break\n"
        "                        cur = cur[1]\n"
        "                    else:\n"
        "                        if cur[2] is None:\n"
        "                            cur[2] = [v, None, None]; break\n"
        "                        cur = cur[2]\n"
        "        def encode(node):\n"
        "            if node is None:\n"
        "                return '#'\n"
        "            return 'X' + encode(node[1]) + encode(node[2])\n"
        "        shapes.add(encode(root))\n"
        "    print(len(shapes))\n"
        "if __name__ == '__main__':\n"
        "    solve()\n"
    )
    denied_submit = session.apply(
        "Agent_2", {"action": "submit_run", "code": "print(0)"}
    )
    assert "WORKSTATION DENIED" in denied_submit.message
    assert "ACQUIRED" in session.apply(
        "Agent_1", {"action": "workstation_acquire"}
    ).message
    pending = session.apply(
        "Agent_1", {"action": "submit_run", "code": "print(0)"}
    )
    assert "RUN PENDING R1" in pending.message
    blocked = session.apply(
        "Agent_1", {"action": "submit_run", "code": ceiling_ac}
    )
    assert "SUBMIT DENIED" in blocked.message
    wa = session.resolve_pending()
    assert wa is not None and wa.verdict == "WA"
    ac_pending = session.apply(
        "Agent_1", {"action": "submit_run", "code": ceiling_ac}
    )
    assert "RUN PENDING R2" in ac_pending.message
    ac = session.resolve_pending()
    assert ac is not None and ac.verdict == "AC"
    assert session.scoreboard.solved() == 1
    assert session.scoreboard.penalty() == ac.turn + 20
    assert session.scoreboard.penalized_rejections() == 1
    assert session.scoreboard.accepted_run() is ac
    assert session.scoreboard.accepted_run().code == ceiling_ac.strip()

    final_system, _final_user = session.final_context("Agent_1")
    assert "FINAL_SYNTHESIS" in final_system
    assert "CONTEST RULE PACKET" not in final_system
    assert session.card.rules_text not in final_system

    runner = ICPCRunner(
        problem_id=DEFAULT_PROBLEM,
        query_fn=ScriptedMockLLM(),
        rounds=2,
        max_tool_steps=6,
    )
    packet = runner.run()
    assert packet["submitted"]
    assert packet["grade"]["method"] == "judge_sandbox_required"
    assert packet["session"]["memory"]["shared"]
    assert packet["session"]["debate"]["proposals"]
    assert packet["session"]["debate"]["proposals"][0]["status"] == "accept"
    assert packet["session"]["debate"]["counts"]["challenge"] == 1
    assert packet["session"]["scoreboard"]["judge"] == "sample-judge"
    assert packet["session"]["scoreboard"]["sample_count"] >= 1
    assert packet["session"]["scoreboard"]["runs"]
    assert not any(
        "ACTION ERROR" in event["result"]
        for event in packet["session"]["action_events"]
    )
    return {
        "status": "ok",
        "problem_id": packet["problem_id"],
        "submitted": packet["submitted"],
        "grade_method": packet["grade"]["method"],
        "contest_rules_chars": packet["session"]["contest_rules_chars"],
        "shared_memories": len(packet["session"]["memory"]["shared"]),
        "debate_proposals": len(packet["session"]["debate"]["proposals"]),
        "scoreboard": packet["session"]["scoreboard"]["status"],
        "context_calls": len(packet["session"]["context_metrics"]),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run an ICPC problem with the full contestant-visible rule packet, "
            "structured memory, and evidence-led multi-agent debate."
        )
    )
    parser.add_argument("--problem", default=DEFAULT_PROBLEM)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--max-tool-steps", type=int, default=6)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use a live LLM provider (see --provider).",
    )
    parser.add_argument(
        "--provider",
        choices=["perplexity", "tinker"],
        default="perplexity",
        help="Live provider when --live is set.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api", choices=["agent", "sonar"], default="agent")
    parser.add_argument(
        "--tinker-max-tokens",
        type=int,
        default=2048,
        help="max_tokens for Tinker chat completions (gpt-oss needs headroom).",
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--print-json", action="store_true")
    parser.add_argument("--list-problems", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.list_problems:
        for problem_id in _load_icpc_problem_ids():
            print(problem_id)
        return 0
    if args.self_test:
        print(_json(run_self_test()))
        return 0

    available = set(_load_icpc_problem_ids())
    if args.problem not in available:
        raise SystemExit(
            f"Unknown ICPC problem_id={args.problem!r}. Use --list-problems."
        )
    if args.live:
        if args.provider == "tinker":
            query_fn = make_tinker_caller(
                model=args.model if args.model != DEFAULT_MODEL else "openai/gpt-oss-20b",
                max_tokens=args.tinker_max_tokens,
            )
            mode = "live-tinker"
            model = args.model if args.model != DEFAULT_MODEL else "openai/gpt-oss-20b"
        else:
            query_fn = make_perplexity_caller(
                model=args.model,
                api=args.api,
                max_output_tokens=None,
            )
            mode = "live"
            model = args.model
    else:
        query_fn = ScriptedMockLLM()
        mode = "mock"
        model = "scripted-mock"

    packet = ICPCRunner(
        problem_id=args.problem,
        query_fn=query_fn,
        rounds=args.rounds,
        max_tool_steps=args.max_tool_steps,
        mode=mode,
        model=model,
    ).run()

    if args.output is not None:
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(_json(packet) + "\n", encoding="utf-8")
        print(f"Saved: {output}")
    print(
        _json(
            {
                "problem_id": packet["problem_id"],
                "mode": packet["mode"],
                "submitted": packet["submitted"],
                "submitted_by": packet["submitted_by"],
                "grade": packet["grade"],
                "contest_rules_chars": packet["session"]["contest_rules_chars"],
                "scoreboard": packet["session"].get("scoreboard"),
                "shared_memories": len(packet["session"]["memory"]["shared"]),
                "debate": packet["session"]["debate"]["counts"],
            }
        )
    )
    if args.print_json:
        print(_json(packet))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
