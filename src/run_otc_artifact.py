"""Run the canonical OTC team on a slide/document artifact and rubric evaluation."""
import argparse
import json
from pathlib import Path
from llm import resolve_request_fn
from otc_artifact_pipeline import prepare_artifact_run, run_artifact_contest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--competition', required=True)
    parser.add_argument('--system-variant', choices=['otc', 'vallina_otc', 'vanilla_otc'], default='otc')
    parser.add_argument('--task-pdf', type=Path, required=True)
    parser.add_argument('--task-pages')
    parser.add_argument('--task-text', default='')
    parser.add_argument('--rubric', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rules-root', type=Path)
    parser.add_argument('--team-size', type=int)
    parser.add_argument('--max-turns', type=int)
    parser.add_argument('--max-api-calls', type=int)
    parser.add_argument('--max-tokens', type=int, default=220000)
    parser.add_argument('--max-output-tokens', type=int, default=8192)
    parser.add_argument('--provider', default='perplexity')
    parser.add_argument('--model')
    parser.add_argument('--judge-provider')
    parser.add_argument('--judge-model')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    args = vars(parser.parse_args(argv))
    from dotenv import load_dotenv
    load_dotenv()
    resume, prepare = args.pop('resume'), args.pop('prepare_only')
    run = prepare_artifact_run(**args)
    if prepare:
        print(json.dumps({'identity': run['identity']['fingerprint'],
                          'kind': run['contract'].kind, 'team_size': run['config'].team_size,
                          'turns': run['config'].max_turns, 'api_calls': run['config'].max_api_calls}))
        return 0
    result = run_artifact_contest(run, resume=resume,
        agent_request=resolve_request_fn(provider=run['provider'], model=run['model'],
                                        max_output_tokens=run['max_output_tokens']),
        judge_request=resolve_request_fn(provider=run['judge_provider'], model=run['judge_model'],
                                        max_output_tokens=run['max_output_tokens']))
    print(json.dumps({'status': result['status'], 'output': str(args['output'])}))
    return 0 if result['status'] == 'complete' else 2


if __name__ == '__main__':
    raise SystemExit(main())
