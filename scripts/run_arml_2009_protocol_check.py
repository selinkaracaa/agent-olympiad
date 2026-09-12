"""Paired ARML 2009 live check with equal resources and separate artifacts."""
from __future__ import annotations

import concurrent.futures
import argparse
import hashlib
import json
import subprocess
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from contest_manifest import load_contest_manifest
from contest_adapters import grade_contest_result
from contest_budget import resolve_contest_budget
from contest_config import PROTOCOL_VERSION
from rules.loader import load_rule_card


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'results/arml_local_2009_protocol_v6')
    args=parser.parse_args()
    out = args.output.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f'Use a fresh output directory; refusing to overwrite {out}')
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / 'data/contest_manifests/generated/arml_local_2009.json'
    manifest = load_contest_manifest(manifest_path, benchmark_root=ROOT / 'data/benchmarks')
    if not grade_contest_result(manifest, {})['graded']:
        raise RuntimeError('Selected ARML tasks lack deterministic grading')
    if any('Team Answers' in task.prompt or 'Team Solutions' in task.prompt for task in manifest.tasks):
        raise RuntimeError('Answer section in public prompt')
    source_paths = sorted((ROOT/'src').rglob('*.py'))
    source_paths += [manifest_path, ROOT/'data/benchmarks/arml_local/benchmark.json']
    # Turn budget follows the official clock (ARML Local 45 min / 5 min = 9 turns, cap 90);
    # API calls = think + action per seat per turn, plus one turn-0 Coach.
    max_turns = resolve_contest_budget(manifest.competition_id).max_turns
    team_size = load_rule_card(manifest.competition_id).team_size_default
    max_api_calls = max_turns * team_size * 2 + 1
    config = {'protocol_version':PROTOCOL_VERSION,'provider':'perplexity','model':'openai/gpt-5.4-mini','team_size':team_size,'max_turns':max_turns,'max_api_calls':max_api_calls,'max_output_tokens_budget':220000,'task_ids':[task.task_id for task in manifest.tasks],'source_sha256':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}}
    (out/'paired_config.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
    for source in source_paths:
        if source.is_relative_to(ROOT/'src'):
            dest=out/'source_snapshot'/source.relative_to(ROOT)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,dest)

    def run(variant):
        dest = out / variant
        dest.mkdir(exist_ok=True)
        if (dest/'contest_session.json').exists():
            raise RuntimeError(f'Result exists; refusing to overwrite {dest}')
        command=[sys.executable,'-u',str(ROOT/'src/run_competition_batch.py'),
            '--live','--provider',config['provider'],'--model',config['model'],
            '--contest-manifest',str(manifest_path),'--system-variant',variant,
            '--action-calling','native','--team-size',str(team_size),'--max-turns',str(max_turns),
            '--max-api-calls',str(max_api_calls),'--max-total-tokens','220000',
            '--no-judge-task','--no-judge-cce','--output',str(dest)]
        (dest/'command.json').write_text(json.dumps(command, indent=2), encoding='utf-8')
        with (dest/'run.log').open('w', encoding='utf-8') as log:
            process=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        print(f'{variant}: exit={process.returncode}', flush=True)
        return variant, process.returncode

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        statuses=dict(pool.map(run, ('decentralized','otc')))
    rows={}
    for variant, code in statuses.items():
        path=out/variant/'contest_session.json'
        if code or not path.exists():
            rows[variant]={'status':'failed','exit_code':code}
            continue
        result=json.loads(path.read_text(encoding='utf-8'))
        rows[variant]={'status':'complete','grade':result['grade'],'budget':result['budget'],
            'metrics':result['metrics'],'diagnostics':result['diagnostics'],
            'submission_count':sum(bool(a) for a in result['submissions'].values()),
            'action_errors':[e['payload'] for e in result['memory']['events'] if e['kind']=='action_error']}
    (out/'paired_summary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(rows,ensure_ascii=True,indent=2),flush=True)
    if any(value['status']!='complete' for value in rows.values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
