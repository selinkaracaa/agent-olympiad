import json
import os
import time
from google import genai
from google.genai import errors as genai_errors

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash-lite"


def generate_with_retry(contents, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model=MODEL, contents=contents)
            return response.text
        except genai_errors.ServerError as e:
            if attempt < max_retries - 1:
                wait = 10 * (attempt + 1)
                print(f"  [503 retry {attempt+1}/{max_retries}, waiting {wait}s]")
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
    agent_prompt = f"""You are a student taking the International Economics Olympiad. Answer the following question as completely and carefully as possible. Show all your reasoning and working.

{problem["problem_description"]}"""

    agent_answer = generate_with_retry(agent_prompt)
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

    judge_feedback = generate_with_retry(judge_prompt)
    print(f"  Judge scored.")

    results.append({
        "problem_id": problem["problem_id"],
        "year": problem["year"],
        "topic": problem["topic"],
        "total_points": problem["total_points"],
        "agent_answer": agent_answer,
        "judge_feedback": judge_feedback
    })

# Save results
output_path = "data/processed/experiment_results.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n\nAll done! Results saved to {output_path}")

# Print summary table
print("\n" + "="*60)
print(f"SCORE SUMMARY ({MODEL})")
print("="*60)
for r in results:
    lines = r["judge_feedback"].split("\n")
    score_line = next((l for l in reversed(lines) if "TOTAL:" in l), "TOTAL: ?")
    print(f"{r['problem_id']:<30} {score_line.strip()}")
