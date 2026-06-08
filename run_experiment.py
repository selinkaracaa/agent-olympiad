import json
import os
import time
import sys
from openai import OpenAI, RateLimitError, APIStatusError

# Supports both Perplexity and OpenAI APIs
# Usage: python3 run_experiment.py [model_name]
# Example: python3 run_experiment.py openai/gpt-5.4-mini
#          python3 run_experiment.py sonar-pro

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

MODEL = sys.argv[1] if len(sys.argv) > 1 else "sonar-pro"

if PERPLEXITY_API_KEY:
    client = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")
elif OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    raise ValueError("Set PERPLEXITY_API_KEY or OPENAI_API_KEY environment variable")

print(f"Model: {MODEL}")
print(f"API:   {'Perplexity' if PERPLEXITY_API_KEY else 'OpenAI'}")


def generate_with_retry(messages, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(model=MODEL, messages=messages)
            return response.choices[0].message.content
        except (RateLimitError, APIStatusError) as e:
            if attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                print(f"  [retry {attempt+1}/{max_retries}, waiting {wait}s — {e}]")
                time.sleep(wait)
            else:
                raise


with open("data/processed/ieo_benchmark.json") as f:
    problems = json.load(f)

results = []

for problem in problems:
    print(f"\n{'='*60}")
    print(f"Running: {problem['problem_id']} — {problem['topic']}")

    # Step 1: Agent attempts the problem
    agent_answer = generate_with_retry([
        {
            "role": "system",
            "content": "You are a student taking the International Economics Olympiad. Answer the following question as completely and carefully as possible. Show all your reasoning and working."
        },
        {
            "role": "user",
            "content": problem["problem_description"]
        }
    ])
    print(f"  Agent answered ({len(agent_answer)} chars)")

    # Step 2: LLM Judge scores the agent's answer
    judge_prompt = f"""You are an expert economics judge scoring a student's answer to an International Economics Olympiad question.

QUESTION:
{problem["problem_description"]}

OFFICIAL SAMPLE SOLUTION:
{problem["gold_label"]["sample_solution"]}

OFFICIAL GRADING RUBRIC:
{problem["gold_label"]["grading_rubric"]}

STUDENT'S ANSWER:
{agent_answer}

Your task:
1. Score the student's answer according to the official grading rubric above.
2. The maximum score is {problem["total_points"]} points.
3. For each criterion in the rubric, state how many points the student earned and why.
4. End with a TOTAL SCORE in the format: "TOTAL: X/{problem["total_points"]}"
"""

    judge_feedback = generate_with_retry([
        {
            "role": "system",
            "content": "You are a strict but fair economics olympiad judge. Score answers accurately according to the provided rubric."
        },
        {
            "role": "user",
            "content": judge_prompt
        }
    ])
    print(f"  Judge scored.")

    results.append({
        "problem_id": problem["problem_id"],
        "year": problem["year"],
        "topic": problem["topic"],
        "total_points": problem["total_points"],
        "model": MODEL,
        "agent_answer": agent_answer,
        "judge_feedback": judge_feedback
    })

# Save results with model name in filename
safe_model = MODEL.replace("/", "_").replace(".", "_")
output_path = f"data/processed/results_{safe_model}.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n\nAll done! Results saved to {output_path}")

# Print summary table
print("\n" + "="*60)
print(f"SCORE SUMMARY — {MODEL}")
print("="*60)
for r in results:
    lines = r["judge_feedback"].split("\n")
    score_line = next((l for l in reversed(lines) if "TOTAL:" in l), "TOTAL: ?")
    score = score_line.replace("**", "").replace("TOTAL:", "").strip()
    print(f"{r['problem_id']:<30} {score}")
