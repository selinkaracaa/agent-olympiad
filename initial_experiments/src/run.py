"""
Multi-Agent Olympiad Experiment

Teams of agents collaborate on olympiad team tasks with no pre-assigned roles.

Usage:
  python3 src/run.py agent:openai/gpt-5.5 slides --rounds 20
  python3 src/run.py agent:openai/gpt-5.4-mini --olympiad iol_team --smoke --limit 1
  python3 initial_experiments/src/run.py agent:openai/gpt-5.5 --benchmark data/benchmarks/iol_team/benchmark.json --format answer

Set PERPLEXITY_API_KEY environment variable before running.
"""

import argparse
import json
import os
import sys
import time
import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_DIR = os.path.join(REPO_ROOT, "initial_experiments", "results")

API_KEY = os.environ.get("PERPLEXITY_API_KEY")
if not API_KEY:
    raise ValueError("Set PERPLEXITY_API_KEY environment variable")

TEST_TASK_TYPES = {"team_contest", "team_power", "team_practical"}


def parse_model_arg(arg):
    if arg.startswith("agent:"):
        return arg[len("agent:"):], "agent"
    return arg, "sonar"


def parse_args():
    parser = argparse.ArgumentParser(description="Multi-agent olympiad experiment")
    parser.add_argument("agent_model", nargs="?", default="agent:openai/gpt-5.5")
    parser.add_argument("judge_model", nargs="?", default=None)
    parser.add_argument("format", nargs="?", default=None, choices=["report", "slides", "answer"])
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--agents", type=int, default=None)
    parser.add_argument("--smoke", action="store_true", help="Quick test: 2 agents, 2 rounds")
    parser.add_argument("--benchmark", default=None, help="Path to benchmark JSON")
    parser.add_argument("--olympiad", default=None, help="Olympiad id from data/benchmarks/index.json")
    parser.add_argument("--limit", type=int, default=None, help="Max problems to run")
    parser.add_argument("--year", type=int, default=None, help="Run only this problem year")
    parser.add_argument("--years", default=None, help="Comma-separated years, e.g. 2018,2021,2023")
    parser.add_argument("--with-gold", action="store_true", help="Only problems with official solutions")
    parser.add_argument("--merge-into", default=None, help="Merge results into existing JSON by problem_id")
    args = parser.parse_args()
    if args.judge_model is None:
        args.judge_model = args.agent_model
    elif args.judge_model in ("report", "slides", "answer"):
        args.format = args.judge_model
        args.judge_model = args.agent_model
    if args.smoke:
        args.rounds = 2
        if args.agents is None:
            args.agents = 2
    return args


args = parse_args()
AGENT_MODEL, AGENT_API = parse_model_arg(args.agent_model)
JUDGE_MODEL, JUDGE_API = parse_model_arg(args.judge_model)
NUM_ROUNDS = args.rounds
OLYMPIAD_ID = args.olympiad
EXPLICIT_AGENTS = args.agents

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def is_test_task(problem):
    return problem.get("task_type") in TEST_TASK_TYPES


def default_format(problems):
    if problems and is_test_task(problems[0]):
        return "answer"
    return "slides"



def call_sonar(model, system_prompt, user_prompt, max_retries=5):
    from openai import OpenAI, RateLimitError, APIStatusError
    client = OpenAI(api_key=API_KEY, base_url="https://api.perplexity.ai")
    for attempt in range(max_retries):
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user",   "content": user_prompt}]
            )
            return r.choices[0].message.content
        except (RateLimitError, APIStatusError):
            if attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                print(f"  [retry {attempt+1}/{max_retries}, waiting {wait}s]")
                time.sleep(wait)
            else:
                raise


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
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                wait = 15 * (attempt + 1)
                print(f"  [{status} retry {attempt+1}/{max_retries}, waiting {wait}s]")
                time.sleep(wait)
            else:
                raise
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                wait = 15 * (attempt + 1)
                print(f"  [network retry {attempt+1}/{max_retries}, waiting {wait}s]")
                time.sleep(wait)
            else:
                raise


def generate(model, api, system_prompt, user_prompt):
    if api == "agent":
        return call_agent(model, system_prompt, user_prompt)
    return call_sonar(model, system_prompt, user_prompt)


def is_valid_output(text, min_len=200):
    if not text or len(text.strip()) < min_len:
        return False
    head = text.strip()[:80]
    if head.startswith("{") and ("'output':" in text or '"output":' in text):
        return False
    if "'reasoning_tokens'" in text or '"reasoning_tokens"' in text:
        return False
    return True


def generate_with_retry(model, api, system_prompt, user_prompt, min_len=200, max_attempts=3):
    prompt = user_prompt
    for attempt in range(max_attempts):
        response = generate(model, api, system_prompt, prompt)
        if is_valid_output(response, min_len=min_len):
            return response
        if attempt < max_attempts - 1:
            print(f"  [invalid output ({len(response)} chars), retry {attempt + 2}/{max_attempts}]")
            prompt = user_prompt + "\n\nIMPORTANT: Reply with plain-text answer content only. No JSON, no API metadata."
    return response


AGENT_SYSTEM_PROMPT = """You are one student on a team competing in an International Olympiad team contest. You are working with teammates to solve a shared problem.

Your team should:
- Decompose the task into sub-problems and divide work naturally
- Discuss, challenge, and refine each other's reasoning
- Review progress before producing a final team answer

You will see what your teammates have already written in the shared workspace. Read it carefully, then add your contribution. You can:
- Take on a sub-task your team has not covered yet
- Challenge or refine something a teammate said, if you disagree
- Coordinate with your team (e.g. suggest who should handle what next)
- Propose structure for the final answer

There are no assigned roles — figure out how to work together as a real team would.
Be concise but substantive. Do not repeat what teammates have already said."""


def build_discussion_history(messages):
    if not messages:
        return "(no messages yet — you are the first to contribute)"
    lines = []
    for msg in messages:
        lines.append(f"[Student {msg['agent_id']} — Round {msg['round']}]")
        lines.append(msg["content"])
        lines.append("")
    return "\n".join(lines)


def problem_label(problem):
    return "PROBLEM" if is_test_task(problem) else "BUSINESS CASE"


def build_agent_user_prompt(problem, messages, round_num, agent_id):
    history = build_discussion_history(messages)
    label = problem_label(problem)
    return f"""=== {label} ===
{problem["problem_description"]}

=== TEAM DISCUSSION SO FAR ===
{history}

=== YOUR TURN ===
You are Student {agent_id}. This is Round {round_num} of {NUM_ROUNDS}.
What is your contribution to the team's work?"""


def build_synthesis_user_prompt(problem, messages, output_format):
    history = build_discussion_history(messages)
    text = problem["problem_description"]
    label = problem_label(problem)

    if output_format == "answer":
        return f"""=== {label} ===
{text}

=== FULL TEAM DISCUSSION ===
{history}

=== FINAL TEAM ANSWER SHEET ===
Write the team's complete final answer. Number each part (a, b, c...) to match the problem.
Include all reasoning conclusions as concise final answers. This is what the team submits."""

    if output_format == "slides":
        return f"""=== {label} ===
{text}

=== FULL TEAM DISCUSSION ===
{history}

=== FINAL SLIDE DECK ===
Create a complete presentation slide deck (10–15 slides).

--- Slide N: [Title] ---
• Bullet point (max 5 bullets per slide)
Speaker notes: [1-3 sentences]

Cover all required areas from the case. Use numbers where possible."""

    return f"""=== {label} ===
{text}

=== FULL TEAM DISCUSSION ===
{history}

=== FINAL REPORT ===
Write the complete final team report synthesizing your team's best thinking."""


def synthesis_system_prompt(problem, output_format):
    if output_format == "answer":
        return "You are one student on an olympiad team. Write the team's final submitted answer sheet."
    if output_format == "slides":
        return "You are one student on an IEO Business Case team. Create the final presentation slide deck."
    return "You are one student on an IEO Business Case team. Write the final strategic case report."


def build_judge_user_prompt(problem, final_output, output_format):
    gold = problem.get("gold_label", {})
    rubric = gold.get("grading_rubric") or ""
    text = problem["problem_description"]

    if is_test_task(problem):
        expected = gold.get("expected_answer") or "(not provided)"
        max_pts = problem.get("total_points") or 100
        return f"""=== PROBLEM ===
{text}

=== OFFICIAL SOLUTION / MARKING SCHEME ===
{expected}

=== GRADING NOTES ===
{rubric}

=== TEAM'S FINAL ANSWER ===
{final_output}

=== SCORING ===
Compare the team's answer to the official solution. Award partial credit per sub-part.
For each major section: state points earned and brief justification.
End with: TOTAL: X/{max_pts}"""

    deliverable = {"slides": "SLIDE DECK", "report": "FINAL REPORT"}.get(output_format, "FINAL REPORT")
    note = (
        "Score the slide deck for a 10-minute oral presentation (written deck only)."
        if output_format == "slides"
        else "Score the written report."
    )
    return f"""=== BUSINESS CASE TASK ===
{text}

=== OFFICIAL EVALUATION RUBRIC ===
{rubric}

=== TEAM'S {deliverable} ===
{final_output}

=== SCORING INSTRUCTIONS ===
{note}
Score strictly on the 4 official dimensions. Total out of 50 points.
For each dimension: score and 2-3 sentence justification.
End with: TOTAL: X/50"""


def judge_system_prompt(problem):
    if is_test_task(problem):
        return "You are an expert olympiad grader for team contest problems. Score fairly against the official solution."
    return "You are an expert judge for the IEO Business Case competition. Score fairly and strictly."


def load_benchmarks(benchmark_path, olympiad_id):
    if olympiad_id:
        index_path = os.path.join(REPO_ROOT, "data", "benchmarks", "index.json")
        with open(index_path) as f:
            index = json.load(f)
        match = next((o for o in index["olympiads"] if o["id"] == olympiad_id), None)
        if not match:
            raise ValueError(f"Unknown olympiad: {olympiad_id}")
        benchmark_path = match["benchmark_path"]

    if benchmark_path:
        with open(benchmark_path) as f:
            data = json.load(f)
        return data if isinstance(data, list) else [data]

    raise ValueError(
        "Provide --olympiad <id> or --benchmark <path>. "
        "(Solo IEO open-question defaults were removed.)"
    )


def ready_problems(problems, limit, year, years, with_gold):
    ready = [p for p in problems if p.get("problem_description", "").strip()]
    if with_gold:
        ready = [p for p in ready if p.get("gold_label", {}).get("expected_answer")]
    if years:
        ready = [p for p in ready if p.get("year") in years]
    elif year is not None:
        ready = [p for p in ready if p.get("year") == year]
    if limit:
        ready = ready[:limit]
    return ready


def parse_years(args):
    if not args.years:
        return None
    return [int(y.strip()) for y in args.years.split(",") if y.strip()]


def load_existing_results(path):
    if not path or not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


def save_results(path, md_path, results):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    with open(md_path, "w") as f:
        for r in results:
            f.write(f"# {r['problem_id']} — {r['topic']}\n\n")
            f.write(f"**Agents:** {r['agent_model']}  \n")
            f.write(f"**Judge:** {r['judge_model']}  \n")
            f.write(f"**Format:** {r['output_format']}  \n\n")
            f.write("## Score\n\n")
            f.write(r["judge_feedback"] + "\n\n---\n\n")
            content = r.get("final_slides") or r.get("final_answer") or r.get("final_report", "")
            label = {"slides": "Slides", "answer": "Answer"}.get(r["output_format"], "Report")
            f.write(f"## {label}\n\n{content}\n")


def merge_results(existing, new_results):
    by_id = {r["problem_id"]: r for r in existing}
    for r in new_results:
        by_id[r["problem_id"]] = r
    return sorted(by_id.values(), key=lambda r: (r.get("year") or 0, r["problem_id"]))


YEAR_LIST = parse_years(args)
problems = load_benchmarks(args.benchmark, args.olympiad)
problems = ready_problems(problems, args.limit, args.year, YEAR_LIST, args.with_gold)

if not problems:
    print("No problems with text found. Run a collection script first or check --benchmark/--olympiad.")
    sys.exit(1)

if args.format is None:
    OUTPUT_FORMAT = default_format(problems)
else:
    OUTPUT_FORMAT = args.format

safe_model = AGENT_MODEL.replace("/", "_").replace(".", "_")
safe_judge = JUDGE_MODEL.replace("/", "_").replace(".", "_")
format_suffix = f"_{OUTPUT_FORMAT}" if OUTPUT_FORMAT != "report" else ""
rounds_suffix = f"_{NUM_ROUNDS}r" if NUM_ROUNDS != 3 else ""
olympiad_suffix = f"_{OLYMPIAD_ID}" if OLYMPIAD_ID else ""
default_output = os.path.join(
    RESULTS_DIR,
    f"multiagent{olympiad_suffix}{format_suffix}{rounds_suffix}_{safe_model}_judgedby_{safe_judge}.json",
)
output_path = args.merge_into or default_output
md_path = output_path.replace(".json", ".md")

print(f"Agent model : {AGENT_MODEL}")
print(f"Judge model : {JUDGE_MODEL}")
print(f"Format      : {OUTPUT_FORMAT}")
print(f"Rounds      : {NUM_ROUNDS}")
print(f"Tools       : none (POST /v1/agent with model + input only)")
if OLYMPIAD_ID:
    print(f"Olympiad    : {OLYMPIAD_ID}")
if args.merge_into:
    print(f"Merge into  : {args.merge_into}")
print(f"\nFound {len(problems)} problem(s) to run.")

all_results = load_existing_results(args.merge_into) if args.merge_into else []
new_results = []

for problem in problems:
    n_agents = EXPLICIT_AGENTS if EXPLICIT_AGENTS is not None else (problem.get("team_size") or 5)
    print(f"\n{'='*60}")
    print(f"{problem['problem_id']} — {problem['topic']} ({n_agents} agents)")
    print(f"{'='*60}")

    shared_messages = []

    for round_num in range(1, NUM_ROUNDS + 1):
        print(f"\n  --- Round {round_num} ---")
        for agent_id in range(1, n_agents + 1):
            print(f"  Agent {agent_id} thinking...", end=" ", flush=True)
            user_prompt = build_agent_user_prompt(problem, shared_messages, round_num, agent_id)
            response = generate(AGENT_MODEL, AGENT_API, AGENT_SYSTEM_PROMPT, user_prompt)
            shared_messages.append({"agent_id": agent_id, "round": round_num, "content": response})
            print(f"done ({len(response)} chars)")

    print(f"\n  --- Final synthesis ({OUTPUT_FORMAT}) ---")
    synthesis_prompt = build_synthesis_user_prompt(problem, shared_messages, OUTPUT_FORMAT)
    synthesis_system = synthesis_system_prompt(problem, OUTPUT_FORMAT)
    final_output = generate_with_retry(AGENT_MODEL, AGENT_API, synthesis_system, synthesis_prompt)
    print(f"  Final {OUTPUT_FORMAT} written ({len(final_output)} chars)")

    print("  Judge scoring...", end=" ", flush=True)
    judge_prompt = build_judge_user_prompt(problem, final_output, OUTPUT_FORMAT)
    judge_feedback = generate(JUDGE_MODEL, JUDGE_API, judge_system_prompt(problem), judge_prompt)
    print("done")

    result = {
        "problem_id": problem["problem_id"],
        "year": problem.get("year"),
        "topic": problem["topic"],
        "task_type": problem.get("task_type"),
        "agent_model": AGENT_MODEL,
        "judge_model": JUDGE_MODEL,
        "output_format": OUTPUT_FORMAT,
        "num_agents": n_agents,
        "num_rounds": NUM_ROUNDS,
        "discussion": shared_messages,
        "judge_feedback": judge_feedback,
    }
    key = {"slides": "final_slides", "answer": "final_answer"}.get(OUTPUT_FORMAT, "final_report")
    result[key] = final_output
    new_results.append(result)
    all_results = merge_results(all_results, [result])
    save_results(output_path, md_path, all_results)
    print(f"  Saved checkpoint → {output_path}")

print(f"\nAll done! Results saved to {output_path}")
print(f"Readable version: {md_path}")

print("\n" + "=" * 60)
print(f"SCORE SUMMARY  |  Agents: {AGENT_MODEL}  |  Judge: {JUDGE_MODEL}")
print("=" * 60)
for r in new_results:
    lines = r["judge_feedback"].split("\n")
    score_line = next((l for l in reversed(lines) if "TOTAL:" in l.upper()), "TOTAL: ?")
    score = score_line.replace("**", "").replace("TOTAL:", "").strip()
    print(f"{r['problem_id']:<35} {score}")
