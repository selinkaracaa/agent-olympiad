"""Compatibility entry point: presentation tasks now use the canonical OTC engine.

Legacy benchmark selection is retained. Format limits live in the rule card;
there is no separate discussion/synthesis loop.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from evaluation.slides_pipeline import resolve_problem_task_pdf
from run_otc_artifact import main as run_otc

ROOT = Path(__file__).resolve().parents[1]


def load_problem(benchmark, problem_id):
    data = json.loads(benchmark.read_text(encoding='utf-8'))
    items = data if isinstance(data, list) else data.get('problems', [])
    for item in items:
        if item.get('problem_id') == problem_id:
            return item
    raise ValueError(f'Problem {problem_id!r} not found in {benchmark}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path)
    parser.add_argument('--problem-id')
    parser.add_argument('--competition')
    parser.add_argument('--task-pdf', type=Path)
    parser.add_argument('--task-label')
    parser.add_argument('--agent-model')
    parser.add_argument('--rounds', type=int)
    parser.add_argument('--output', type=Path)
    # Other canonical options pass through (rubric, provider, resume, budgets).
    args, forwarded = parser.parse_known_args(argv)
    if args.benchmark:
        if not args.problem_id:
            parser.error('--benchmark requires --problem-id')
        problem = load_problem(args.benchmark.resolve(), args.problem_id)
        args.task_pdf = args.task_pdf or resolve_problem_task_pdf(problem, ROOT)
        args.competition = args.competition or args.benchmark.parent.name
        rubric = (problem.get('evaluation') or {}).get('rubric_path')
        if rubric and not any(x == '--rubric' or x.startswith('--rubric=') for x in forwarded):
            forwarded += ['--rubric', str(ROOT / rubric)]
    if not args.competition or not args.task_pdf:
        parser.error('Supply --competition and --task-pdf (or --benchmark/--problem-id)')
    if not args.output:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
        args.output = ROOT / 'results' / 'presentation_artifacts' / f'{args.competition}_{stamp}'
    forwarded += ['--competition', args.competition, '--task-pdf', str(args.task_pdf),
                  '--output', str(args.output)]
    for key, value in (('--task-text', args.task_label), ('--model', args.agent_model),
                       ('--max-turns', args.rounds)):
        if value is not None:
            forwarded += [key, str(value)]
    return run_otc(forwarded)


if __name__ == '__main__':
    raise SystemExit(main())
