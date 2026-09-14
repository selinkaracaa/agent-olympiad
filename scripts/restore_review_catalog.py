"""Restore review candidates; reuse same-track rubrics without inventing gold answers.

Idempotent, scoped migration. Existing rows win over archived rows. Original files
are backed up once; official rubric protocols are never overwritten.
"""
from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
from src.evaluation.models import load_rubric

BACKUP = ROOT / 'data/excluded/pre_restore_review_20260911'
POLICY = {
    'same_competition_only': True,
    'cross_year_rubric_reuse': True,
    'copy_other_year_answers': False,
    'invent_official_weights': False,
    'missing_packet_or_environment_stays_not_ready': True,
    'excluded_competitions': ['envirothon'],
}


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8-sig'))


def save(path, value):
    target = ROOT / path
    content = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    if target.exists() and target.read_text(encoding='utf-8') == content:
        return
    if target.exists():
        backup = BACKUP / path
        if not backup.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')


def numeric(path):
    try:
        load_rubric(ROOT / path)
        return True
    except (KeyError, TypeError, ValueError):
        return False


def restore(rows, removed):
    result = copy.deepcopy(rows)
    existing = {r['problem_id'] for r in result}
    for item in removed:
        if item['dataset'] == 'envirothon':
            continue
        row = copy.deepcopy(item['row'])
        if row['problem_id'] in existing:
            continue
        row['restoration_review'] = {
            'status': 'restored_for_user_review',
            'date': '2026-09-11',
            'original_exclusion_reason': item['reason'],
            'archive': 'data/excluded/formal_packet_review_20260911/manifest.json',
        }
        row.setdefault('evaluation', {}).update(status='not_ready', evaluator_id=None)
        result.append(row)
        existing.add(row['problem_id'])
    return result


def main():
    archive = read('data/excluded/formal_packet_review_20260911/manifest.json')
    # Flatten only the published scientific subcriteria (0, .5, 1). This is
    # a report-only subtotal, NOT the official grade/TP/team ranking formula.
    donor = 'data/rubrics/ichto_2025_official_scoring_v1.json'
    source = read(donor)
    criteria = []
    role = next(x for x in source['role_rubrics'] if x['id'] == 'reporter_scientific')
    for group in role['criteria']:
        for name in group['subcriteria']:
            criteria.append(dict(id=f'scientific_{len(criteria)+1}', name=name,
                                 max_score=1, min_score=0,
                                 description=f"{group['name']}: {name}. Score 0, 0.5, or 1 from submitted scientific evidence; do not assume unreported experiments occurred."))
    adapted = 'data/rubrics/ichto_report_scientific_9_reused_v1.json'
    save(adapted, dict(rubric_id='ichto_report_scientific_9_reused_v1',
         title='IChTo 2025 scientific subcriteria reused for written reports',
         total_points=len(criteria), criteria=criteria,
         source_rubric_path=donor, source_edition=2025,
         scoring_basis='Published scientific subcriterion subtotal; benchmark report-only adaptation, not official technical/rating points.',
         not_observable_from_deck=['Live debate', 'Opponent and reviewer performance', 'Official jury aggregation and ranking']))
    load_rubric(ROOT / adapted)

    index = read('data/benchmarks/index.json')
    report = {'policy': POLICY, 'restored_by_track': {}, 'tracks': {}}
    for track in index['olympiads']:
        cid = track['id']
        assert cid != 'envirothon'
        path = track['benchmark_path']
        original = read(path)
        removed = [x for x in archive['removed'] if x['dataset'] == cid]
        rows = restore(original, removed)
        if removed:
            report['restored_by_track'][cid] = len(removed)
        changed = rows != original
        cards = []
        for row in rows:
            e = row.setdefault('evaluation', {})
            # Existing rubric belongs to this track: reuse criteria, never answer maps.
            paths = e.get('rubric_paths') or ([e['rubric_path']] if e.get('rubric_path') else [])
            eligible = cid in {'cfa_research_challenge', 'debatebench', 'ijso_practical',
                               'odyssey_of_the_mind', 'gcch_harvard', 'eoes', 'ichto'}
            if eligible and paths:
                e.setdefault('pre_reuse_evaluation', copy.deepcopy(e))
                e['rubric_reuse'] = dict(source_competition=cid, target_competition=cid,
                    target_year=row.get('year'), source_rubric_paths=paths,
                    source_editions={'ichto': [2025], 'gcch_harvard': ['2024-2026'],
                                     'eoes': [2022, 2023]}.get(cid, ['existing same-competition rubric; edition unspecified']),
                    official_year_equivalence=False,
                    scoring_basis='Same-competition criteria reuse; not other-year answers or verified official historical scoring.')
                changed = True
            if cid == 'ichto':
                e.update(rubric_path=adapted, evaluator_id='rubric_llm_v1',
                         status='ready_with_limitations',
                         limitations='2025 scientific criteria reused across years as a 9-point written-report subtotal. No live debate, official TP conversion, or team ranking is reproduced.')
                e['rubric_reuse']['source_rubric_paths'] = [donor]
            elif cid == 'ijso_practical' and row.get('year') in (2007, 2008) and not row.get('restoration_review'):
                e.update(evaluator_id='rubric_llm_v1', status='ready_with_limitations',
                         limitations='Shared IJSO 40-point report rubric; no task-specific marking scheme. Qualitative report assessment only, not official answer accuracy or physical lab performance.')
            elif cid in {'eoes', 'gcch_harvard'}:
                e.update(evaluator_id=None, status='not_ready',
                         limitations='Same-competition cross-year protocol reuse is allowed. The archived protocol has no executable numeric criteria; numeric rubric integration is still required. Other-year task answers and unpublished weights are not substituted.')

            if eligible:
                e['scorecard_path'] = f'data/rubrics/task_scorecards/{cid}.json'
                e['scorecard_key'] = row['problem_id']
            paths = e.get('rubric_paths') or ([e['rubric_path']] if e.get('rubric_path') else [])
            rubrics = []
            for rp in paths:
                data = read(rp)
                is_numeric = numeric(rp)
                rubrics.append(dict(path=rp, sha256=hashlib.sha256((ROOT/rp).read_bytes()).hexdigest(),
                    format='numeric_rubric' if is_numeric else 'official_protocol_or_answer_map',
                    rubric_id=data.get('rubric_id'), total_points=data.get('total_points'),
                    criteria=data.get('criteria', []) if is_numeric else [],
                    not_observable_from_deck=data.get('not_observable_from_deck', [])))
            cards.append(dict(problem_id=row['problem_id'], year=row.get('year'),
                evaluation_status=e.get('status'), evaluator_id=e.get('evaluator_id'),
                rubrics=rubrics, answer_key_path=e.get('answer_key_path'),
                rubric_variant=e.get('rubric_variant'), official_rubric_map=e.get('official_rubric_map'),
                judge_assets=[a for a in row.get('assets', []) if a.get('role') == 'judge_only'],
                limitations=e.get('limitations'), rubric_reuse=e.get('rubric_reuse'),
                scoring_basis=e.get('rubric_reuse', {}).get('scoring_basis', 'Existing scoring basis retained.'),
                numeric_rubric_available=any(r['format']=='numeric_rubric' for r in rubrics)))
        assert len({r['problem_id'] for r in rows}) == len(rows), cid
        if changed:
            save(path, rows)
            save(f'data/rubrics/task_scorecards/{cid}.json',
                 dict(schema_version='1.0', dataset=cid, visibility='judge_only', records=cards))
            rule_path = f'data/rules/{cid}/evaluation.json'
            rule = read(rule_path)
            rule['scoring']['rubric_reuse_policy'] = POLICY
            rule['scoring']['benchmark_readiness_source'] = path
            if cid == 'ichto':
                rule['scoring'].update(rubric_path=adapted, evaluator_id='rubric_llm_v1',
                                       evaluator_status='ready_with_limitations')
                rule['evaluation_guidance'] = (
                    'Benchmark adaptation: use the shared 2025 scientific report rubric (9 points). '
                    'This is not the official live tournament TP/RP score. '
                    'Use each benchmark record for readiness and deliverable requirements. '
                    'Official-performance metadata below describes source mechanics, not this adaptation.')
            save(rule_path, rule)
        track.update(problems_collected=len(rows), catalog_status='active' if rows else 'empty',
                     eval_units=sorted({r.get('eval_unit','session') for r in rows}),
                     evaluation_status_counts=dict(Counter(r.get('evaluation',{}).get('status','unknown') for r in rows)))
        if changed:
            report['tracks'][cid] = dict(records=len(rows), statuses=track['evaluation_status_counts'])
    index.update(active_tracks=sum(x['problems_collected']>0 for x in index['olympiads']),
                 total_records=sum(x['problems_collected'] for x in index['olympiads']))
    save('data/benchmarks/index.json', index)
    report.update(active_tracks=index['active_tracks'], total_records=index['total_records'])
    save('data/benchmarks/restoration_review_20260911.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
