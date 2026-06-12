"""
Score teamwork on existing multi-agent experiment results.

Reads saved discussion logs — no need to re-run the full experiment.
One judge API call per results file.

Usage:
  python3 score_teamwork.py [results.json ...]

  python3 score_teamwork.py data/processed/multiagent_*.json

Set PERPLEXITY_API_KEY environment variable before running.
"""

import glob
import json
import os
import sys
import time
import requests

API_KEY = os.environ.get("PERPLEXITY_API_KEY")
if not API_KEY:
    raise ValueError("Set PERPLEXITY_API_KEY environment variable")

raw_judge = None
file_args = []
for arg in sys.argv[1:]:
    if arg.startswith("agent:"):
        raw_judge = arg[len("agent:"):]
    else:
        file_args.append(arg)

JUDGE_MODEL = raw_judge or "openai/gpt-5.5"
if not file_args:
    file_args = sorted(glob.glob("data/processed/multiagent*.json"))

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def call_agent(model, system_prompt, user_prompt, max_retries=5):
    full_input = f"{system_prompt}\n\n{user_prompt}"
    for attempt in range(max_retries):
        try:
            r = requests.post(
                "https://api.perplexity.ai/v1/agent",
                headers=HEADERS,
                json={"model": model, "input": full_input},
                timeout=180
            )
            r.raise_for_status()
            data = r.json()
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        return content["text"]
            return str(data)
        except requests.exceptions.HTTPError:
            if r.status_code == 429 and attempt < max_retries - 1:
                time.sleep(10 * (attempt + 1))
            else:
                raise


TEAMWORK_RUBRIC = """Official IEO Business Case — Teamwork criteria (adapted for text-only discussion logs):

1. Participation balance — Did all team members contribute meaningfully across rounds?
2. Coordination — Did the team divide work, assign sections, or propose a shared structure without being told?
3. Genuine collaboration — Did agents build on, challenge, or refine each other's points (not just "I agree")?
4. Convergence — Did the team move toward a shared recommendation by the final round?

You cannot evaluate oral presentation timing or visible on-stage teamwork. Score only what is evident in the written discussion."""


def format_discussion(discussion):
    lines = []
    for msg in discussion:
        lines.append(f"[Student {msg['agent_id']} — Round {msg['round']}]")
        lines.append(msg["content"])
        lines.append("")
    return "\n".join(lines)


def score_teamwork(problem_id, topic, discussion):
    prompt = f"""=== CASE ===
{problem_id} — {topic}

=== OFFICIAL TEAMWORK CRITERIA (text-only adaptation) ===
{TEAMWORK_RUBRIC}

=== TEAM DISCUSSION (3 rounds, 5 agents) ===
{format_discussion(discussion)}

=== SCORING INSTRUCTIONS ===
Score teamwork out of 10 points (this is a sub-score for the Communication dimension).

For each of the 4 criteria above: brief note (1 sentence) + sub-score out of 2.5.
End with: TEAMWORK TOTAL: X/10
"""
    return call_agent(
        JUDGE_MODEL,
        "You are an IEO Business Case judge evaluating team collaboration from discussion transcripts only.",
        prompt
    )


for path in file_args:
    print(f"\nScoring: {path}")
    with open(path) as f:
        results = json.load(f)

    changed = False
    for entry in results:
        if "discussion" not in entry:
            print(f"  Skipping {entry.get('problem_id', '?')} — no discussion log")
            continue
        if entry.get("teamwork_feedback"):
            print(f"  Skipping {entry['problem_id']} — already scored")
            continue

        print(f"  Judging teamwork for {entry['problem_id']}...", end=" ", flush=True)
        feedback = score_teamwork(entry["problem_id"], entry["topic"], entry["discussion"])
        entry["teamwork_judge_model"] = JUDGE_MODEL
        entry["teamwork_feedback"] = feedback
        changed = True
        print("done")

    if changed:
        with open(path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"  Updated {path}")

print("\nDone.")
