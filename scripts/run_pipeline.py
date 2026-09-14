"""Register every catalog track, run resumable OTC jobs, and export their results.

No unregistered fallback to the legacy per-problem runner. Unsupported routes and
missing inputs remain explicit blocked jobs in the denominator.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def safe(value):
    return hashlib.sha256(str(value).encode()).hexdigest()[:16]


def artifact_task_pdf(row):
    """Resolve one contestant PDF; declared asset roles override legacy hints."""
    assets = row.get('provenance', {}).get('assets', [])
    forbidden = {
        (ROOT / asset['path']).resolve() for asset in assets
        if asset.get('role') == 'judge_only' and asset.get('path')
    }
    pdfs = list(dict.fromkeys(
        (ROOT / asset['path']).resolve() for asset in assets
        if asset.get('role') == 'agent_visible'
        and str(asset.get('path', '')).lower().endswith('.pdf')
    ))
    source = (ROOT / row['source_file']).resolve() if row.get('source_file') else None
    # Preserve legacy records without an asset inventory, but never use an
    # unclassified fallback to override an explicit inventory.
    if not assets and source is not None:
        pdfs = [source]
    if any(pdf in forbidden for pdf in pdfs) or (not pdfs and source in forbidden):
        raise ValueError('Task PDF is marked judge_only; contestant input refused')
    if len(pdfs) != 1 or not pdfs[0].is_file() or pdfs[0].suffix.lower() != '.pdf':
        raise ValueError('Requires one verified task PDF or explicit multi-file task mapping')
    return pdfs[0]


def validate_artifact_input(job):
    """Recheck old registries against current canonical input-role metadata."""
    ids = job.get('problem_ids', [])
    if len(ids) != 1:
        raise ValueError('Artifact job requires one benchmark record or an explicit multi-file mapping')
    entries = read(ROOT / 'data/benchmarks/index.json')['olympiads']
    entry = next((item for item in entries if item['id'] == job['competition']), None)
    if entry is None:
        raise ValueError('Artifact competition is absent from the current catalog')
    rows = read(ROOT / entry['benchmark_path'])
    row = next((item for item in rows if item['problem_id'] == ids[0]), None)
    if row is None:
        raise ValueError('Artifact record is absent from the current benchmark')
    expected = artifact_task_pdf(row)
    if not job.get('task_pdf') or Path(job['task_pdf']).resolve() != expected:
        raise ValueError('Artifact task PDF changed or is not contestant-visible; re-register the job')
    return expected


def register(out):
    # Read card components without importing the runtime, so registration still
    # reports all tracks when the runtime itself has an import failure.
    from collections import OrderedDict
    index = read(ROOT / 'data/benchmarks/index.json')['olympiads']
    tracks, jobs = [], []
    for entry in index:
        name = entry['id']
        card = {}
        blockers = []
        for component in ('competition', 'collaboration', 'evaluation'):
            path = ROOT / 'data/rules' / name / (component + '.json')
            if path.is_file():
                card.update(read(path))
            else:
                blockers.append('Missing rule component: ' + str(path))
        official = card.get('deliverable', {}).get('official_deliverable')
        route = card.get('simulation', {}).get('deliverable_pipeline', {}).get('kind')
        if not route:
            route = ('slides' if official == 'slide_deck' else
                     'document' if official in {'proof_packet', 'lab_report', 'worked_answers',
                         'written_memorial', 'written_memorandum', 'written_essay', 'investment_report'} else
                     'native' if official in {'source_code', 'answer_sheet', 'puzzle_answer', 'flag', 'spoken_answer'} else
                     'external_environment')
        path = ROOT / entry['benchmark_path']
        rows = read(path) if path.is_file() else []
        if not rows:
            blockers.append('No benchmark records')
        groups = OrderedDict()
        for row in rows:
            # Preserve published packet boundaries for question-level datasets.
            key = row['problem_id']
            if name == 'icpc':
                key = 'icpc_wf_' + str(row.get('year', 'unknown'))
            elif name == 'science_bowl':
                key = row.get('parent_session_id') or row.get('packet') or key
            elif name == 'qanta':
                key = f"qanta_{row.get('year', 'unknown')}_{row.get('tournament', 'unknown')}"
            elif name == 'mystery_hunt':
                key = 'mystery_hunt_' + str(row.get('year', key))
            groups.setdefault(str(key), []).append(row)
        tracks.append(dict(competition=name, route=route, records=len(rows), sessions=len(groups), blockers=blockers))
        for key, members in groups.items():
            job_id = name + '_' + safe(key)
            job = dict(id=job_id, competition=name, session=key, route=route,
                       problem_ids=[r['problem_id'] for r in members], blockers=list(blockers))
            if route == 'native':
                if official == 'flag':
                    job['blockers'].append('Requires provisioned CTF environment; no generic text fallback')
                manifest = dict(session_id=key, competition_id=name, problem_ids=job['problem_ids'],
                                split_parts=name in {'arml_local', 'arml_national_team'})
                manifest_path = out / 'manifests' / (job_id + '.json')
                if manifest_path.exists() and read(manifest_path) != manifest:
                    raise ValueError('Changed manifest; use a fresh output root: ' + job_id)
                write(manifest_path, manifest)
                job['manifest'] = str(manifest_path)
            elif route in {'document', 'slides'}:
                row = members[0]
                try:
                    job['task_pdf'] = str(artifact_task_pdf(row))
                except ValueError as exc:
                    job['blockers'].append(str(exc))
                rubric = card.get('scoring', {}).get('rubric_path')
                if rubric and (ROOT / rubric).is_file():
                    job['rubric'] = str(ROOT / rubric)
                else:
                    job['blockers'].append('Missing configured rubric')
            else:
                job['blockers'].append('Specialized environment adapter not configured')
            jobs.append(job)
    registry = dict(tracks=tracks, jobs=jobs, track_count=len(tracks), session_count=len(jobs))
    write(out / 'registry.json', registry)
    print(json.dumps(dict(tracks=len(tracks), sessions=len(jobs),
                          blocked=sum(bool(j['blockers']) for j in jobs))), flush=True)
    return registry


def command(job, out, args, *, completed_results=None):
    dest = out / 'runs' / job['id']
    common = ['--system-variant', 'otc', '--provider', args.provider, '--model', args.model,
              '--output', str(dest)]
    if job['route'] == 'native':
        from run_competition_batch import inspect_contest_run
        from contest_manifest import load_contest_manifest
        from contest_adapters import grade_contest_result
        cli = ['--live', '--contest-manifest', job['manifest'], *common]
        state, identity = inspect_contest_run(cli)
        if state == 'complete':
            if completed_results is not None:
                from contest_run_identity import read_completed_contest_result
                completed_results[job['id']] = read_completed_contest_result(dest, identity)
            return None
        if state == 'resume' and (dest / 'contest_session.json').is_file():
            # Finalized contestants need only the missing auxiliary judges.
            # Do not require a working programming gateway or rerun submissions.
            from contest_run_identity import read_finalized_contest_result
            read_finalized_contest_result(dest, identity)
            cli.append('--resume')
            return [sys.executable, '-u', str(ROOT / 'src/run_competition_batch.py'), *cli]
        manifest = load_contest_manifest(Path(job['manifest']), benchmark_root=ROOT / 'data/benchmarks')
        if any(t.programming for t in manifest.tasks):
            if job['competition'] != 'icpc':
                raise ValueError('Programming adapter requires verified remote judge mapping before batch execution')
            if any(not t.benchmark.get('evaluation', {}).get('vjudge_prob_num') or
                   t.benchmark.get('evaluation', {}).get('status') != 'remote_judge_ready'
                   for t in manifest.tasks):
                raise ValueError('Incomplete remote judge mapping; full session retained, not silently filtered')
            if os.name == 'nt':
                probe = subprocess.run(['powershell.exe', '-NoProfile', '-Command',
                    "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' "
                    "-and $_.CommandLine -match 'run_competition_batch.py' }).Count"],
                    capture_output=True, text=True, check=True)
                if int(probe.stdout.strip() or '0'):
                    raise ValueError('Another contest runner is active; retry this job after it ends')
            subprocess.run(['docker', 'info'], check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE, timeout=15)
            with urllib.request.urlopen('http://127.0.0.1:8787/v1/health', timeout=5) as response:
                if not json.load(response).get('ok'):
                    raise ValueError('VJudge gateway is not healthy')
        elif not grade_contest_result(manifest, {'submissions': {}})['graded']:
            raise ValueError('Full-session deterministic evaluation unavailable')
        if state == 'resume':
            cli.append('--resume')
        return [sys.executable, '-u', str(ROOT / 'src/run_competition_batch.py'), *cli]
    task_pdf = validate_artifact_input(job)
    cli = ['--competition', job['competition'], '--task-pdf', str(task_pdf),
           '--rubric', job['rubric'], *common]
    if (dest / 'run_identity.json').exists():
        cli.append('--resume')
    return [sys.executable, '-u', str(ROOT / 'src/run_otc_artifact.py'), *cli]


def native_completion_state(result):
    """Contestant completion and evaluation completeness are different states."""
    grade = result['grade']
    if grade.get('graded') is True:
        return dict(status='complete')
    reasons = [row.get('reason') for row in grade.get('tasks', {}).values()
               if not row.get('graded') and row.get('reason')]
    return dict(status='ungraded', reason='; '.join(dict.fromkeys(reasons))
                or 'Contest ended, but evaluation is incomplete')


def report(out, registry, states):
    rows = []
    for job in registry['jobs']:
        state = states.get(job['id'], {})
        row = dict(competition=job['competition'], session=job['session'], route=job['route'],
                   status=state.get('status', 'blocked' if job['blockers'] else 'pending'),
                   reason=state.get('reason', '; '.join(job['blockers'])), score='', max_score='',
                   graded_tasks='', coordination='', seconds='')
        path = out / 'runs' / job['id'] / ('contest_session.json' if job['route'] == 'native' else 'result.json')
        if path.exists():
            result = read(path)
            grade = result.get('grade') or result.get('evaluation') or {}
            row.update(score=grade.get('score', grade.get('total_score', '')),
                       max_score=grade.get('max_score', ''), graded_tasks=grade.get('graded_tasks', ''),
                       coordination=result.get('metrics', {}).get('coordination_score', ''),
                       seconds=result.get('metrics', {}).get('elapsed_seconds', ''))
        rows.append(row)
    with (out / 'summary.tsv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ['status'], delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)
    write(out / 'batch_status.json', dict(counts=dict(Counter(r['status'] for r in rows)), jobs=states))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['register', 'run', 'report', 'all'])
    parser.add_argument('--output', type=Path, default=ROOT / 'results/otc_pipeline')
    parser.add_argument('--provider', default='perplexity')
    parser.add_argument('--model', default='openai/gpt-5.4-mini')
    parser.add_argument('--competitions', help='Optional comma-separated track filter; default all')
    parser.add_argument('--limit', type=int, help='Explicit pilot limit; default all sessions')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    registry = register(out) if args.stage in {'register', 'all'} else read(out / 'registry.json')
    status_path = out / 'batch_status.json'
    states = read(status_path)['jobs'] if status_path.exists() else {}
    exit_code = 0
    if args.stage in {'run', 'all'}:
        # Exclusive create prevents duplicate batch supervisors for this root.
        lock = out / 'pipeline.lock'
        with lock.open('x') as handle:
            handle.write(str(os.getpid()))
        try:
            selected = [j for j in registry['jobs'] if not args.competitions or
                        j['competition'] in args.competitions.split(',')]
            # Start with native answer sheets; expensive artifact and remote
            # sessions follow in the same durable, serial queue.
            selected.sort(key=lambda j: (j['session'] != 'arml_local_2014', j['competition'] != 'arml_local',
                                        j['route'] != 'native', j['id']))
            if args.limit is not None:
                selected = selected[:args.limit]
            for job in selected:
                if job['blockers']:
                    exit_code = 1
                    continue
                try:
                    completed_results = {}
                    cmd = command(job, out, args, completed_results=completed_results)
                    if cmd is None:
                        states[job['id']] = native_completion_state(completed_results[job['id']])
                        if states[job['id']]['status'] != 'complete':
                            exit_code = 1
                        report(out, registry, states)
                        print(job['id'], states[job['id']]['status'], flush=True)
                        continue
                    states[job['id']] = dict(status='running', command=cmd)
                    report(out, registry, states)
                    logs = out / 'logs'
                    logs.mkdir(exist_ok=True)
                    with (logs / (job['id'] + '.log')).open('a', encoding='utf-8') as log:
                        completed = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                    dest = out / 'runs' / job['id']
                    if completed.returncode:
                        raise RuntimeError(f'Runner exit {completed.returncode}; see per-job log')
                    if job['route'] == 'native':
                        if command(job, out, args, completed_results=completed_results) is not None:
                            raise RuntimeError('Runner exited without verified final result')
                        states[job['id']] = native_completion_state(completed_results[job['id']])
                    else:
                        states[job['id']] = dict(status=read(dest / 'result.json')['status'])
                    if states[job['id']]['status'] != 'complete':
                        exit_code = 1
                except Exception as exc:
                    exit_code = 1
                    states[job['id']] = dict(status='blocked', reason=f'{type(exc).__name__}: {exc}')
                report(out, registry, states)
                print(job['id'], states[job['id']]['status'], flush=True)
        finally:
            lock.unlink()
    report(out, registry, states)
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
