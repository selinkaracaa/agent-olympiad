# Input Environment and Settings

## System
- Competition id: `iol_team`
- Problem id: `iol_team_2007`
- Task type: `team_contest`
- Eval unit: `session`
- Status: `collected`

## Team / Tooling Rules
- Display name: International Linguistics Olympiad — Team Contest
- Default team size: 4
- Allowed tools: query_rules

### Rules text
The official IOL Team Contest uses exactly 4 team members collaborating freely with a shared answer sheet. External web search, calculators, and code execution are not permitted. Agents may contribute, update shared notes, inspect competition rules, or skip a turn. One designated synthesizer submits the final team answer. Team sizes 2–3 are experimental only and require an explicit non-comparable override.

## Evaluation Hints (for harness, not a gold key)
- Evaluator: `rubric_llm_v1`
- Evaluator status: `ready`
- Rubric path: `data/rubrics/worked_answer_100_v1.json`
- Deliverable: `worked_answers`
