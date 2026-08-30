"""Export a transcript as a readable private-think to committed-action trace."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _quote(text: str) -> str:
    lines = (text or "(empty)").splitlines() or ["(empty)"]
    return "\n".join(f"> {line}" if line else ">" for line in lines)


def build_markdown(transcript: dict[str, Any], source: Path) -> str:
    metadata = transcript.get("metadata") or {}
    thoughts: dict[tuple[int, str], list[str]] = defaultdict(list)
    for agent, entries in (transcript.get("private_thoughts") or {}).items():
        for entry in entries:
            thoughts[(int(entry.get("turn", 0)), str(agent))].append(
                str(entry.get("content") or "")
            )

    actions: dict[tuple[int, str], dict[str, Any]] = {}
    for entry in transcript.get("action_log") or []:
        agent = str(entry.get("agent") or "")
        if not agent or agent in {"Coach", "Contest_Control"}:
            continue
        action = str(entry.get("action") or "")
        if action == "submit_final":
            continue
        actions[(int(entry.get("turn", 0)), agent)] = entry

    keys = sorted(
        set(thoughts) | set(actions),
        key=lambda item: (item[0], item[1]),
    )
    lines = [
        "# Think → Action Trace",
        "",
        f"- Competition: `{metadata.get('competition_id', 'unknown')}`",
        f"- Problem: `{metadata.get('problem_id', 'unknown')}`",
        f"- Source: `{source}`",
        "- Private think was visible only to its owner during the run.",
        "- Action payload was written to public, group/direct, or private state.",
        "",
    ]
    current_turn: int | None = None
    for turn, agent in keys:
        if turn != current_turn:
            lines.extend([f"## Turn {turn}", ""])
            current_turn = turn
        action = actions.get((turn, agent)) or {}
        action_name = str(action.get("action") or "(no action)")
        target = action.get("target")
        recipients = action.get("recipients") or []
        if recipients:
            destination = ", ".join(str(item) for item in recipients)
        elif target:
            destination = str(target)
        else:
            destination = str(action.get("visibility") or "private")
        lines.extend(
            [
                f"### {agent}",
                "",
                "**Private think**",
                "",
                _quote("\n\n".join(thoughts.get((turn, agent), []))),
                "",
                f"**Committed action:** `{action_name}` → `{destination}`",
                "",
                "**Action payload / summary**",
                "",
                _quote(str(action.get("payload") or "(empty)")),
            ]
        )
        if action.get("protocol_error"):
            lines.extend(
                [
                    "",
                    f"**Protocol error:** `{action['protocol_error']}`",
                    "",
                    "**Raw response preview**",
                    "",
                    _quote(str(action.get("raw_response_preview") or "(not saved)")),
                ]
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    transcript = json.loads(args.transcript.read_text(encoding="utf-8"))
    output = args.output or args.transcript.with_name(
        args.transcript.stem + "__think_to_action.md"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        build_markdown(transcript, args.transcript),
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
