"""Per-item workboard: pick a problem, record an answer, review a teammate's.

A contest run is one env over many items — an ARML answer sheet, the labelled
sub-questions of an IOAA group task. Without per-item state the team cannot see
what it already tried, so resubmitting one wrong answer costs nothing and
teaches nothing; runs collapse into that loop until the turn budget is gone.

The board keeps the history the agents were missing: who answered what, on which
turn, and how many times. It does not tell them whether an answer is right —
contests do not, and the gold label must never reach the team through here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

# A board of one is just the task itself; below this we stay out of the way.
MIN_BOARD_ITEMS = 2
# Guards against a runaway statement parse turning every numbered line into work.
MAX_BOARD_ITEMS = 40
# Turns a claim survives without its holder touching the item.
DEFAULT_CLAIM_TTL_TURNS = 3

PRIORITIES = ("high", "normal", "low")

# Tried in order; the first that finds MIN_BOARD_ITEMS distinct labels wins.
# The last is unanchored because answer-sheet contests (ARML) ship the whole
# set as one paragraph: "Team Problems 1. Compute ... 2. Compute ...".
_LABEL_PATTERNS = (
    re.compile(r"(?im)^[ \t]*(?:problem|question|task|part)\s+([0-9]{1,2}|[A-Z])\b"),
    re.compile(r"(?m)^[ \t]*\(([A-Z]{1,3}[0-9]{1,3}(?:\.[0-9]{1,2})?)\)"),
    re.compile(r"(?m)^[ \t]*([0-9]{1,2})\s*[.)]\s+\S"),
    re.compile(r"(?:(?<=\s)|\A)([0-9]{1,2})\s*[.)]\s+(?=\S)"),
)


def _keep_ordered_run(labels: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Numeric labels must read 1, 2, 3, ...

    Without this, prose like "the product of its digits is 96. 2. Compute..."
    contributes a bogus item 96 alongside the real ones.
    """
    if not labels or not all(label.isdigit() for label, _ in labels):
        return labels
    kept: list[tuple[str, int]] = []
    expected = 1
    for label, start in labels:
        if int(label) == expected:
            kept.append((label, start))
            expected += 1
    return kept


def _normalize(text: str) -> str:
    """Answer-equality key. Mirrors evaluation.gold so repeats match grading."""
    try:
        from evaluation.gold import normalize_answer

        return normalize_answer(text)
    except Exception:
        return re.sub(r"\s+", "", str(text or "").lower().strip())


def _parse_labeled_spans(text: str) -> dict[str, str]:
    """Split a statement into label -> body using the first pattern that fits."""
    blob = str(text or "")
    if not blob.strip():
        return {}
    for pattern in _LABEL_PATTERNS:
        raw = [
            (match.group(1).strip(), match.start())
            for match in pattern.finditer(blob)
        ]
        raw = _keep_ordered_run(raw)
        labels = []
        seen = set()
        for label, start in raw:
            if label in seen:
                continue
            seen.add(label)
            labels.append((label, start))
        if len(labels) < MIN_BOARD_ITEMS:
            continue
        labels = labels[:MAX_BOARD_ITEMS]
        spans: dict[str, str] = {}
        for index, (label, start) in enumerate(labels):
            end = labels[index + 1][1] if index + 1 < len(labels) else len(blob)
            spans[label] = blob[start:end].strip()
        return spans
    return {}


@dataclass
class Attempt:
    turn: int
    agent: str
    answer: str
    normalized: str


@dataclass
class Review:
    turn: int
    agent: str
    verdict: str
    comment: str
    reviewed_answer: str


@dataclass
class BoardItem:
    item_id: str
    statement: str = ""
    points: Optional[float] = None
    priority: str = "normal"
    hopeless: bool = False
    hopeless_reason: str = ""
    claimed_by: Optional[str] = None
    claimed_turn: Optional[int] = None
    attempts: list[Attempt] = field(default_factory=list)
    reviews: list[Review] = field(default_factory=list)
    repeat_attempts: int = 0

    @property
    def answer(self) -> str:
        """The recorded answer: the latest attempt, which is what gets graded."""
        return self.attempts[-1].answer if self.attempts else ""

    @property
    def answered(self) -> bool:
        return bool(self.attempts)

    def status(self) -> str:
        if self.hopeless:
            return "hopeless"
        if self.reviews:
            return "reviewed"
        if self.attempts:
            return "answered"
        if self.claimed_by:
            return "claimed"
        return "open"

    def holder(self, turn: int, ttl: int) -> Optional[str]:
        """Claim holder, or None once the claim has gone stale."""
        if self.claimed_by is None:
            return None
        touched = self.claimed_turn or 0
        for attempt in self.attempts:
            if attempt.agent == self.claimed_by:
                touched = max(touched, attempt.turn)
        for review in self.reviews:
            if review.agent == self.claimed_by:
                touched = max(touched, review.turn)
        if ttl > 0 and turn - touched > ttl:
            return None
        return self.claimed_by

    def snapshot(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "points": self.points,
            "status": self.status(),
            "priority": self.priority,
            "hopeless": self.hopeless,
            "hopeless_reason": self.hopeless_reason,
            "claimed_by": self.claimed_by,
            "claimed_turn": self.claimed_turn,
            "answer": self.answer,
            "attempts": [vars(item) for item in self.attempts],
            "reviews": [vars(item) for item in self.reviews],
            "repeat_attempts": self.repeat_attempts,
        }


class Workboard:
    """Shared per-item state for a multi-item contest run."""

    def __init__(
        self,
        items: Iterable[BoardItem],
        *,
        claim_ttl_turns: int = DEFAULT_CLAIM_TTL_TURNS,
    ):
        self.items: dict[str, BoardItem] = {item.item_id: item for item in items}
        self.claim_ttl_turns = claim_ttl_turns
        self.source = "explicit"

    # ---------------------------------------------------------------- build

    @classmethod
    def from_problem(
        cls,
        problem_data: dict[str, Any],
        *,
        claim_ttl_turns: int = DEFAULT_CLAIM_TTL_TURNS,
    ) -> Optional["Workboard"]:
        """Derive a board, or None when the task is a single deliverable.

        Only ids, points, and statement text cross this boundary. Gold parts
        also carry ``expected`` and ``reference`` (the full worked solution);
        reading either here would hand the team the answer key.
        """
        statements = _parse_labeled_spans(
            problem_data.get("problem_description")
            or problem_data.get("description")
            or problem_data.get("prompt")
            or ""
        )

        declared = problem_data.get("board_items")
        if declared:
            items = []
            for index, raw in enumerate(declared, start=1):
                if isinstance(raw, dict):
                    item_id = str(raw.get("id") or raw.get("item_id") or index).strip()
                    statement = str(raw.get("statement") or raw.get("text") or "")
                    points = raw.get("points")
                else:
                    item_id = str(raw).strip()
                    statement = ""
                    points = None
                if not item_id:
                    continue
                items.append(
                    BoardItem(
                        item_id=item_id,
                        statement=statement or statements.get(item_id, ""),
                        points=float(points) if points is not None else None,
                    )
                )
            if len(items) >= MIN_BOARD_ITEMS:
                board = cls(items, claim_ttl_turns=claim_ttl_turns)
                board.source = "board_items"
                return board

        parts = (problem_data.get("gold_label") or {}).get("parts") or []
        if len(parts) >= MIN_BOARD_ITEMS:
            items = []
            for index, part in enumerate(parts, start=1):
                item_id = str(part.get("id") or index).strip() or str(index)
                points = part.get("points")
                items.append(
                    BoardItem(
                        item_id=item_id,
                        statement=statements.get(item_id, ""),
                        points=float(points) if points is not None else None,
                    )
                )
            board = cls(items[:MAX_BOARD_ITEMS], claim_ttl_turns=claim_ttl_turns)
            board.source = "gold_parts"
            return board

        if len(statements) >= MIN_BOARD_ITEMS:
            board = cls(
                [
                    BoardItem(item_id=label, statement=body)
                    for label, body in statements.items()
                ],
                claim_ttl_turns=claim_ttl_turns,
            )
            board.source = "statement_labels"
            return board

        return None

    # --------------------------------------------------------------- lookup

    def resolve(self, ref: str) -> Optional[BoardItem]:
        """Match an item reference tolerantly: 'P3', '3', 'g01.1', 'Problem 3'."""
        raw = str(ref or "").strip()
        if not raw:
            return None
        if raw in self.items:
            return self.items[raw]
        candidates = {raw, raw.upper(), raw.lower()}
        stripped = re.sub(
            r"(?i)^(?:problem|question|task|part|p|q|t)[\s\-_.]*", "", raw
        ).strip()
        stripped = stripped.strip("()[]")
        candidates |= {stripped, stripped.upper(), stripped.lower()}
        for candidate in candidates:
            if candidate in self.items:
                return self.items[candidate]
        lowered = {key.lower(): item for key, item in self.items.items()}
        for candidate in candidates:
            if candidate.lower() in lowered:
                return lowered[candidate.lower()]
        return None

    def split_ref(self, payload: str) -> tuple[str, str]:
        """Split 'P3 | rest' or 'P3: rest' / 'P3 rest' into (ref, remainder)."""
        text = str(payload or "").strip()
        if not text:
            return "", ""
        if "|" in text:
            head, _, tail = text.partition("|")
            return head.strip(), tail.strip()
        match = re.match(r"^\s*(\S+?)\s*[:\-]\s*(.*)$", text, re.S)
        if match and self.resolve(match.group(1)):
            return match.group(1).strip(), match.group(2).strip()
        head, _, tail = text.partition(" ")
        if self.resolve(head):
            return head.strip(), tail.strip()
        return text, ""

    def unknown_ref_message(self, ref: str) -> str:
        known = ", ".join(list(self.items)[:12])
        suffix = "..." if len(self.items) > 12 else ""
        return (
            f"Board error: no item matching {ref!r}. "
            f"Known items: {known}{suffix}"
        )

    # --------------------------------------------------------------- render

    def overview(self, *, turn: int, agent_name: str | None = None) -> str:
        lines = [
            "=== PROBLEM BOARD ===",
            f"{len(self.items)} items | answered "
            f"{sum(1 for item in self.items.values() if item.answered)}"
            f"/{len(self.items)}",
        ]
        for item in self.items.values():
            holder = item.holder(turn, self.claim_ttl_turns)
            bits = [f"[{item.item_id}]", item.status()]
            if item.points is not None:
                bits.append(f"{item.points:g}pt")
            if holder:
                bits.append(
                    f"claimed by {'you' if holder == agent_name else holder}"
                )
            if item.priority != "normal":
                bits.append(f"priority={item.priority}")
            if item.attempts:
                bits.append(f"attempts={len(item.attempts)}")
                bits.append(f"answer={item.answer[:60]!r}")
            if item.reviews:
                bits.append(f"reviews={len(item.reviews)}")
            if item.hopeless and item.hopeless_reason:
                bits.append(f"({item.hopeless_reason[:60]})")
            lines.append(" | ".join(bits))
        lines.append(
            "Unanswered items score zero. Only the latest recorded answer counts."
        )
        return "\n".join(lines)

    def detail(self, item: BoardItem, *, turn: int) -> str:
        holder = item.holder(turn, self.claim_ttl_turns)
        lines = [f"=== ITEM {item.item_id} ==="]
        if item.points is not None:
            lines.append(f"Points: {item.points:g}")
        lines.append(f"Status: {item.status()}")
        lines.append(f"Claimed by: {holder or '(unclaimed)'}")
        if item.priority != "normal":
            lines.append(f"Priority: {item.priority}")
        if item.hopeless:
            lines.append(f"Marked hopeless: {item.hopeless_reason or '(no reason)'}")
        lines.append("")
        lines.append(item.statement or "(no separate statement; see the full problem)")
        lines.append("")
        if item.attempts:
            lines.append(f"--- ANSWER HISTORY ({len(item.attempts)} recorded) ---")
            for index, attempt in enumerate(item.attempts, start=1):
                lines.append(
                    f"{index}. turn {attempt.turn} | {attempt.agent}: {attempt.answer}"
                )
            if item.repeat_attempts:
                lines.append(
                    f"({item.repeat_attempts} further attempt(s) rejected as "
                    "identical to an answer already recorded)"
                )
            lines.append(f"Currently recorded: {item.answer}")
        else:
            lines.append("--- ANSWER HISTORY ---")
            lines.append("(nothing recorded yet)")
        if item.reviews:
            lines.append("")
            lines.append("--- REVIEWS ---")
            for review in item.reviews:
                lines.append(
                    f"turn {review.turn} | {review.agent} | {review.verdict}: "
                    f"{review.comment or '(no comment)'}"
                )
        return "\n".join(lines)

    def answer_sheet(self) -> str:
        rows = [
            f"{item.item_id}. {item.answer}"
            for item in self.items.values()
            if item.answered
        ]
        return "\n".join(rows)

    # --------------------------------------------------------------- mutate

    def claim(self, agent_name: str, item: BoardItem, *, turn: int) -> str:
        holder = item.holder(turn, self.claim_ttl_turns)
        if holder == agent_name:
            return f"You already hold {item.item_id}."
        if holder is not None:
            return (
                f"Board error: {item.item_id} is claimed by {holder}. "
                "Pick another item or ask them to release it."
            )
        released = [
            other.item_id
            for other in self.items.values()
            if other is not item
            and other.holder(turn, self.claim_ttl_turns) == agent_name
        ]
        for item_id in released:
            self.items[item_id].claimed_by = None
            self.items[item_id].claimed_turn = None
        item.claimed_by = agent_name
        item.claimed_turn = turn
        note = f" (released {', '.join(released)})" if released else ""
        return f"{agent_name} claimed {item.item_id}{note}. One item per agent."

    def release(self, agent_name: str, item: BoardItem, *, turn: int) -> str:
        holder = item.holder(turn, self.claim_ttl_turns)
        if holder is None:
            return f"{item.item_id} was not claimed."
        if holder != agent_name:
            return f"Board error: {item.item_id} is claimed by {holder}, not you."
        item.claimed_by = None
        item.claimed_turn = None
        return f"{agent_name} released {item.item_id}."

    def record_answer(
        self, agent_name: str, item: BoardItem, answer: str, *, turn: int
    ) -> str:
        text = str(answer or "").strip()
        if not text:
            return f"Board error: no answer given for {item.item_id}."
        holder = item.holder(turn, self.claim_ttl_turns)
        if holder is not None and holder != agent_name:
            return (
                f"Board error: {item.item_id} is claimed by {holder}. "
                "Coordinate before answering someone else's item."
            )
        normalized = _normalize(text)
        prior = next(
            (item_ for item_ in item.attempts if item_.normalized == normalized),
            None,
        )
        if prior is not None:
            item.repeat_attempts += 1
            position = (
                "already the recorded answer"
                if item.attempts[-1].normalized == normalized
                else "already tried and then changed"
            )
            return (
                f"Board error: {text!r} is {position} for {item.item_id} "
                f"(turn {prior.turn}, {prior.agent}). Recording it again changes "
                f"nothing. Try a different approach or move to another item — "
                f"{self.unanswered_count()} item(s) still have no answer."
            )
        item.attempts.append(
            Attempt(turn=turn, agent=agent_name, answer=text, normalized=normalized)
        )
        history = ", ".join(entry.answer[:30] for entry in item.attempts[:-1])
        history_note = f" Earlier answers: {history}." if history else ""
        return (
            f"Recorded for {item.item_id}: {text} "
            f"(attempt {len(item.attempts)} by {agent_name}).{history_note} "
            "No correctness feedback is available in this contest."
        )

    def review(
        self,
        agent_name: str,
        item: BoardItem,
        verdict: str,
        comment: str,
        *,
        turn: int,
    ) -> str:
        if not item.attempts:
            return (
                f"Board error: {item.item_id} has no recorded answer to review."
            )
        last = item.attempts[-1]
        if last.agent == agent_name and len(item.attempts) == 1:
            return (
                f"Board error: {item.item_id} currently holds your own answer. "
                "A review has to come from someone else."
            )
        clean_verdict = str(verdict or "").strip().lower() or "unsure"
        if clean_verdict not in {"agree", "disagree", "unsure"}:
            comment = f"{verdict} {comment}".strip()
            clean_verdict = "unsure"
        item.reviews.append(
            Review(
                turn=turn,
                agent=agent_name,
                verdict=clean_verdict,
                comment=str(comment or "").strip(),
                reviewed_answer=last.answer,
            )
        )
        return (
            f"Review recorded on {item.item_id} ({clean_verdict}) against "
            f"{last.agent}'s answer {last.answer!r}. The recorded answer is "
            "unchanged; submit a new one to replace it."
        )

    def set_priority(self, item: BoardItem, priority: str) -> str:
        value = str(priority or "").strip().lower()
        if value not in PRIORITIES:
            return f"Board error: priority must be one of {', '.join(PRIORITIES)}."
        item.priority = value
        return f"{item.item_id} priority set to {value}."

    def mark_hopeless(self, item: BoardItem, reason: str, *, hopeless: bool = True) -> str:
        item.hopeless = hopeless
        item.hopeless_reason = str(reason or "").strip() if hopeless else ""
        if not hopeless:
            return f"{item.item_id} is back in play."
        return (
            f"{item.item_id} marked hopeless ({item.hopeless_reason or 'no reason'}). "
            "It stays on the board; a recorded guess still beats leaving it blank."
        )

    # -------------------------------------------------------------- reports

    def unanswered_count(self) -> int:
        return sum(1 for item in self.items.values() if not item.answered)

    def metrics(self) -> dict[str, Any]:
        attempts = sum(len(item.attempts) for item in self.items.values())
        repeats = sum(item.repeat_attempts for item in self.items.values())
        answered = sum(1 for item in self.items.values() if item.answered)
        return {
            "board_source": self.source,
            "items_total": len(self.items),
            "items_answered": answered,
            "items_unanswered": len(self.items) - answered,
            "items_reviewed": sum(
                1 for item in self.items.values() if item.reviews
            ),
            "items_hopeless": sum(
                1 for item in self.items.values() if item.hopeless
            ),
            "attempts_recorded": attempts,
            "repeat_attempts_rejected": repeats,
            # The stubbornness number: share of answer attempts that were an
            # answer the team had already recorded for that item.
            "repeat_rate": round(repeats / (attempts + repeats), 4)
            if (attempts + repeats)
            else 0.0,
            "distinct_claimers": len(
                {
                    item.claimed_by
                    for item in self.items.values()
                    if item.claimed_by
                }
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "claim_ttl_turns": self.claim_ttl_turns,
            "metrics": self.metrics(),
            "items": [item.snapshot() for item in self.items.values()],
        }
