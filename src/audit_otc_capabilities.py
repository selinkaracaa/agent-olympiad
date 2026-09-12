"""List configured OTC routes separately from actual artifact grading readiness."""
import json
from pathlib import Path
from collections import Counter
from artifact_contract import delivery_route, contract_for, resolve_rubric
from artifacts.contest_delivery import preflight_renderer
from contest_config import ContestRunConfig
from evaluation.models import load_rubric
from rules.loader import load_rule_card, DEFAULT_RULES_ROOT
from rules.storage import iter_rule_card_ids

ROOT = Path(__file__).resolve().parents[1]


def audit():
    rows = []
    for name in iter_rule_card_ids(DEFAULT_RULES_ROOT):
        card = load_rule_card(name)
        route = delivery_route(card)
        row = dict(competition=name, route=route, otc_configured=False,
                   artifact_preflight_ready=False)
        try:
            ContestRunConfig('otc', card.team_size_default, card.simulation['max_turns'],
                             rule_card=card)
            row['otc_configured'] = True
            if route in {'slides', 'document'}:
                preflight_renderer(contract_for(card))
                rubric = load_rubric(resolve_rubric(card, ROOT))
                row.update(artifact_preflight_ready=True, rubric_max_score=rubric.total_points,
                           scope='artifact proxy only; task PDF still requires validation')
            else:
                row['scope'] = ('Existing native runner; evaluator must be checked per contest'
                                if route == 'native' else 'Requires a specialized adapter')
        except (ValueError, ImportError, FileNotFoundError, RuntimeError) as exc:
            row['blocker'] = str(exc)
        rows.append(row)
    return dict(routes=dict(Counter(row['route'] for row in rows)), competitions=rows)


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
