"""Export the actual baseline/module/competition surfaces without model calls."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from action_modules import MODULE_SPECS
from action_modules.common import CORE_ACTION_NAMES
from action_modules.task_specific import resolve_contest_interface
from artifact_contract import delivery_route
from contest_config import BASELINES, ContestRunConfig, PROTOCOL_VERSION
from contest_manifest import load_contest_manifest
from contest_policy import _resolved_actions
from rules.loader import load_rule_card
from tool_registry import ACTION_REGISTRY, competition_permissions

LABELS = {
    'single_agent': 'Single agent',
    'decentralized': 'Decentralized',
    'centralized': 'Centralized',
    'vallina_otc': 'Open Table Coach + rule card (memory off)',
    'otc': 'Open Table Coach + rule card + memory',
}


def export(output: Path):
    index = json.loads((ROOT / 'data/benchmarks/index.json').read_text(encoding='utf-8'))
    modules = {owner: [{'name': s.name, 'is_tool': s.is_tool, 'pack': s.pack}
                       for s in specs] for owner, specs in MODULE_SPECS.items()}
    baselines = {key: {'label': label, 'features': asdict(BASELINES[key])}
                 for key, label in LABELS.items()}
    competitions = []
    with tempfile.TemporaryDirectory() as directory:
        for entry in index['olympiads']:
            if entry.get('catalog_status', 'active') != 'active':
                continue
            key = entry['id']
            card = load_rule_card(key, required=True)
            records = json.loads((ROOT / entry['benchmark_path']).read_text(encoding='utf-8'))
            record = next(r for r in records if isinstance(r, dict) and r.get('problem_id')
                          and any(r.get(k) for k in ('problem_description', 'description', 'prompt')))
            manifest_path = Path(directory) / (key + '.json')
            manifest_path.write_text(json.dumps({'session_id': 'action_audit_' + key,
                'competition_id': key, 'problem_ids': [record['problem_id']], 'split_parts': False}), encoding='utf-8')
            manifest = load_contest_manifest(manifest_path, benchmark_root=ROOT / 'data/benchmarks')
            interface = resolve_contest_interface(manifest, rule_card=card)
            permitted = competition_permissions(key, rule_card=card) or set()
            rows = {}
            for variant in LABELS:
                features = BASELINES[variant]
                config = ContestRunConfig(variant, 1 if variant == 'single_agent' else card.team_size_default,
                    3, rule_card=card if features.rule_card != 'off' else None)
                specs = _resolved_actions(manifest, config)
                rows[variant] = {'modules': config.modules.as_dict(),
                    'baseline_candidate_surface': sorted(s.name for s in specs),
                    'tools': sorted(s.name for s in specs if s.is_tool),
                    'review_required': config.review_required,
                    'structured_deliberation': bool(config.otc_policy and config.otc_policy.structured_deliberation),
                    'leader': config.leader}
            tool_sets = {tuple(row['tools']) for row in rows.values()}
            assert len(tool_sets) == 1, (key, tool_sets)
            competitions.append({'competition': key, 'representative_problem': record['problem_id'],
                'delivery_route': delivery_route(card),
                'common_tools_permitted': sorted(name for name in permitted if name in ACTION_REGISTRY
                    and ACTION_REGISTRY[name].module == 'common' and ACTION_REGISTRY[name].is_tool),
                'task_specific_available': sorted(s.name for s in interface.actions if s.module == 'task_specific'),
                'interface': interface.report(), 'baselines': rows})
    left, right = baselines['vallina_otc']['features'], baselines['otc']['features']
    differences = {name: {'without_memory': left[name], 'with_memory': right[name]} for name in left if left[name] != right[name]}
    assert set(differences) == {'memory_actions'}, differences
    for competition in competitions:
        pair = competition['baselines']
        plain = set(pair['vallina_otc']['baseline_candidate_surface'])
        enhanced = set(pair['otc']['baseline_candidate_surface'])
        assert enhanced - plain == {'remember', 'recall', 'share_note'}, competition['competition']
        assert not plain - enhanced, competition['competition']
    result = {'protocol_version': PROTOCOL_VERSION, 'scope': 'Current implementation audit; no solver/evaluator runs.',
        'surface_note': 'Candidate surface precedes role/phase/state gating; it is not the callable list of any single turn.',
        'modules': modules, 'common_core': sorted(CORE_ACTION_NAMES), 'baselines': baselines,
        'otc_pair_feature_differences': differences,
        'otc_pair_is_memory_only': set(differences) == {'memory_actions'},
        'competition_count': len(competitions), 'baseline_count': len(baselines),
        'competition_tools_equal_across_baselines': True, 'competitions': competitions}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.with_suffix('.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# Baseline × action module × competition audit', '',
        f'Current protocol: `{PROTOCOL_VERSION}`. {len(competitions)} competitions × {len(baselines)} baselines.', '',
        'Generated from the canonical registry, presets, competition rules and one real representative record per competition. '
        'This is an interface audit, not a model or judge evaluation.', '',
        '## Baselines in the current implementation', '',
        '| Label | Code key | Coach | Review required | Private messages | Memory | Leader submits |',
        '|---|---|---|---|---|---|---|']
    for key, row in baselines.items():
        f = row['features']
        lines.append(f"| {row['label']} | `{key}` | {f['coach']} | {f['review_workflow']} | {f['private_channel']} | {f['memory_actions']} | {f['leader_submits']} |")
    lines += ['', '**The v10 OTC pair differs only in the memory module.** Feature difference: '
              + ', '.join(f'`{key}`' for key in differences) + '. Coach, review, communication, structured discussion and scheduling share one policy. '
              'The historical `vallina_otc` key now denotes the matched memory-off preset; v9 results keep their original meaning. '
              'Explicit CLI aliases: `otc_rule_card` and `otc_rule_card_memory`.', '',
              '## Canonical ownership', '', '| Module | Actions | Tool subset |', '|---|---|---|']
    for owner, specs in modules.items():
        lines.append('| ' + owner + ' | ' + (', '.join('`' + s['name'] + '`' for s in specs) or '(no contestant-callable action)')
                     + ' | ' + (', '.join('`' + s['name'] + '`' for s in specs if s['is_tool']) or 'none') + ' |')
    lines += ['', 'Common ownership does not grant every baseline every action. `assign_problem` is leader-only; '
              'review and deliberation actions depend on workflows; memory is opt-in. '
              'Common tools still require competition permission. Tools are a subset of actions; '
              '`submit_code` is an evaluated submission action, not a tool.', '',
              'The Coach gives one blind pre-contest brief and then exits. Rule-card enforcement is separate from '
              '`query_rules`, which remains available to all five baselines. Conversation, drafts and audit checkpoints '
              'exist even when optional memory is disabled.', '',
              'Role/phase/state gating further limits each turn: centralized workers cannot submit or assign; '
              'ICPC uses `submit_code`, answer sheets/artifacts use `submit`; reviews need eligible candidates, '
              'and workstation leases or pending verdicts can temporarily withhold tools.', '',
              'All five baselines now enter the same artifact renderer and rubric delivery path where a supported '
              'document/slide contract and rubric exist. This does not implement physical/live environments.', '',
              '## Competition tools and task-specific actions', '',
              'Common tools below are rule-permitted; task-specific availability includes resource checks for the '
              'representative record. Missing fixtures and unsupported rule verbs remain in JSON interface limitations. '
              'All five baselines receive identical competition tool sets before role/state gating.', '',
              '| Competition | Delivery route | Permitted common tools | Available task-specific actions |',
              '|---|---|---|---|']
    for row in competitions:
        lines.append(f"| {row['competition']} | {row['delivery_route']} | "
                     + (', '.join(row['common_tools_permitted']) or 'none') + ' | '
                     + (', '.join(row['task_specific_available']) or 'none') + ' |')
    output.with_suffix('.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/from_zhongzheng/baseline-action-matrix-v10-20260912')
    result = export(parser.parse_args().output)
    print(json.dumps({key: result[key] for key in ('competition_count', 'baseline_count',
        'competition_tools_equal_across_baselines', 'otc_pair_is_memory_only', 'otc_pair_feature_differences')}, indent=2))
