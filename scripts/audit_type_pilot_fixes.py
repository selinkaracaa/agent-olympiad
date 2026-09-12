"""Offline checks of preserved pilots; never rewrites scores or calls a model."""
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from artifact_contract import contract_for
from artifacts.contest_delivery import ArtifactRenderer
from contest_adapters import grade_contest_result
from contest_manifest import ContestManifest, ManifestTask
from otc_artifact_pipeline import submission_diagnostics
from rules.loader import load_rule_card


def main():
    base = ROOT / 'results/otc_type_representatives_v1'
    original = json.loads((base / 'qanta_1997/contest_session.json').read_text(encoding='utf-8'))
    rows = json.loads((ROOT / 'data/benchmarks/qanta/benchmark.json').read_text(encoding='utf-8'))
    indexed = {r['problem_id']: r for r in rows}
    tasks = tuple(ManifestTask(**t, prompt='', benchmark=indexed[t['parent_problem_id']])
                  for t in original['manifest']['tasks'])
    manifest = ContestManifest(original['session_id'], 'qanta', tasks)
    grade = grade_contest_result(manifest, original)
    print(json.dumps({'offline_regrade_only': True, 'original_score': original['grade']['score'],
                      'current_grader_score': grade['score'], 'max_score': grade['max_score']}))
    assert original['grade']['score'] == 2 and grade['score'] == 5 and grade['max_score'] == 7
    checked = 0
    with tempfile.TemporaryDirectory() as tmp:
        renderer = ArtifactRenderer(Path(tmp), contract_for(load_rule_card('ieo_business_case')))
        for line in (base / 'ieo_business_case_2021/calls.jsonl').read_text(encoding='utf-8').splitlines():
            for call in json.loads(line).get('tool_calls', []):
                if call['name'] == 'work':
                    renderer(None, 'render_artifact', {'content': call['arguments']['content']})
                    checked += 1
    assert checked == 6
    print(json.dumps({'original_ieo_work_attempts_rendered': checked}))
    iol = json.loads((base / 'iol_team_2007/contest_session.json').read_text(encoding='utf-8'))
    diagnostic = submission_diagnostics(iol['session_checkpoint']['tasks'][0], True)
    assert diagnostic['code'] == 'current_version_rejected'
    print(json.dumps({'iol_code': diagnostic['code'], 'rejections': len(diagnostic['rejections'])}))


if __name__ == '__main__':
    main()
