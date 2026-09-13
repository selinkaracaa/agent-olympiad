"""Contest collaboration -> versioned PDF -> rubric judge for all baselines.

Uses the canonical contest engine. There is no separate team loop or unreviewed
post-contest synthesis. Judge configuration never reaches contestant prompts.
"""
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
import json

from artifact_contract import contract_for, resolve_rubric
from artifacts.assets import file_sha256
from artifacts.contest_delivery import ArtifactRenderer, preflight_renderer
from artifacts.pdf_ingest import parse_pdf
from contest_config import ContestRunConfig, canonical_baseline
from contest_adapters import EnvironmentTaskExecutor
from contest_manifest import ContestManifest, ManifestTask
from contest_runner import run_contest
from contest_run_identity import build_run_identity, validate_run_identity, content_hash
from evaluation.models import CriterionResult, EvaluationResult, load_rubric
from evaluation.slides_pipeline import build_task_asset, evaluate_slide_deck
from evaluation.rubric_llm import RubricDocumentEvaluator
from llm import LLMAttachment, LLMRequest
from rules.loader import load_rule_card

ROOT = Path(__file__).resolve().parents[1]


def submission_diagnostics(task, review_required):
    """Explain a non-submission without changing approval or grading semantics."""
    versions = task.get('versions') or []
    if not versions:
        return {'code': 'no_rendered_version', 'rejections': []}
    latest = versions[-1]
    current = [r for r in task.get('reviews', []) if not r.get('stale')
               and r.get('version_hash') == latest['version_hash']]
    rejections = [{'reviewer': r['reviewer'], 'body': r['body']}
                  for r in current if r['decision'] == 'reject']
    approved = any(r['decision'] == 'approve' and r['reviewer'] != latest['author']
                   for r in current)
    if not latest.get('evidence_refs'):
        code = 'missing_render_evidence'
    elif review_required and rejections:
        code = 'current_version_rejected'
    elif review_required and not approved:
        code = 'awaiting_independent_approval'
    else:
        code = 'eligible_version_not_submitted'
    return {'code': code, 'version_hash': latest['version_hash'],
            'author': latest['author'], 'current_review_count': len(current),
            'rejections': rejections}


def _write(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def prepare_artifact_run(*, competition, task_pdf, output, rubric=None, task_pages=None,
                         task_text='', team_size=None, max_turns=None, max_api_calls=None,
                         max_tokens=220000, provider='perplexity', model=None,
                         judge_provider=None, judge_model=None, rules_root=None,
                         max_output_tokens=8192, system_variant='otc'):
    system_variant = canonical_baseline(system_variant)
    aliases = {'pplx': 'perplexity', 'oai': 'openai'}
    provider = aliases.get(provider, provider)
    judge_provider = aliases.get(judge_provider, judge_provider) or provider
    if provider not in {'perplexity', 'openai'} or judge_provider not in {'perplexity', 'openai'}:
        raise ValueError('Artifact runner requires a PDF/image-capable provider')
    model = model or ('openai/gpt-5.4' if provider == 'perplexity' else 'gpt-4.1')
    judge_model = judge_model or (model if judge_provider == provider else
                                 'openai/gpt-5.4' if judge_provider == 'perplexity' else 'gpt-4.1')
    if max_output_tokens <= 0:
        raise ValueError('max_output_tokens must be positive')
    card = load_rule_card(competition, rules_root=rules_root, required=True)
    contract = contract_for(card)
    rubric_path = resolve_rubric(card, ROOT, rubric)
    rubric_obj = load_rubric(rubric_path)  # Fail before any model calls or output writes.
    task_asset = build_task_asset(Path(task_pdf), task_pages)
    if task_asset.page_end - task_asset.page_start + 1 > 100:
        raise ValueError('Task exceeds 100 pages; explicitly select the intended page range')
    preflight_renderer(contract)
    if judge_provider == 'perplexity' and contract.max_pages > 20:
        raise ValueError('Image rubric judge supports up to 20 submission pages; use a PDF judge')
    if ((judge_provider or provider) in {'perplexity', 'pplx'} and
            task_asset.page_end - task_asset.page_start + 1 > 20):
        raise ValueError('Image rubric judge supports up to 20 task pages; select --task-pages '
                         'explicitly or use a PDF-capable judge provider')
    count = team_size if team_size is not None else (1 if system_variant == 'single_agent' else card.team_size_default)
    turns = max_turns if max_turns is not None else int(card.simulation['max_turns'])
    config = ContestRunConfig(system_variant, count, turns, max_api_calls=max_api_calls,
                              max_tokens=max_tokens, rule_card=card, minutes_per_turn=0)
    if config.otc_policy is not None and config.otc_policy.char_limit('work') < contract.max_source_chars:
        raise ValueError('Rule card work limit is smaller than artifact source limit')
    manifest = ContestManifest(f'{competition}-artifact', competition, (
        ManifestTask('deliverable', 'deliverable', None,
                     task_text or 'Solve the attached official task and produce the required deliverable.',
                     'artifact', rubric_obj.total_points, False, {}),
    ), metadata={'task_family': 'general', 'artifact_contract': asdict(contract)})
    identity = build_run_identity(manifest, config, execution={
        'pipeline': contract.version, 'provider': provider, 'model': model,
        'max_output_tokens': max_output_tokens,
        'budget_basis': 'rule-card simulation rounds; no inferred official clock',
        'task_pdf_sha256': task_asset.sha256,
        'task_pages': [task_asset.page_start, task_asset.page_end],
    }, evaluation={'provider': judge_provider or provider, 'model': judge_model,
                   'rubric_sha256': file_sha256(rubric_path),
                   'rubric_override': rubric is not None}, source_root=ROOT / 'src')
    return dict(card=card, contract=contract, rubric=rubric_path, task_asset=task_asset,
                config=config, manifest=manifest, identity=identity, output=Path(output),
                provider=provider, judge_provider=judge_provider or provider,
                model=model, judge_model=judge_model, max_output_tokens=max_output_tokens)


def _attachments(asset, provider, work_dir, role='agent_visible'):
    if provider in {'perplexity', 'pplx'}:
        parsed = parse_pdf(asset.path, work_dir, media='images', max_pages=100,
                           page_start=asset.page_start, page_end=asset.page_end)
        return tuple(LLMAttachment(path=p.path, mime_type=p.mime_type, role=role)
                     for p in parsed.page_images)
    return (LLMAttachment(path=asset.path, mime_type='application/pdf', role=role,
                          page_start=asset.page_start, page_end=asset.page_end),)


def _evaluation_binding(identity, receipt, evaluation):
    return {'run_fingerprint': identity['fingerprint'],
            'source_sha256': receipt['source_sha256'],
            'pdf_sha256': receipt['pdf_sha256'],
            'evaluation_sha256': content_hash(evaluation)}


def _validate_completed_result(prepared, result, output):
    """Certify the result snapshot, not just the directory's identity file."""
    validate_run_identity(result.get('run_identity'), prepared['identity'],
                          artifact=output / 'result.json')
    if result.get('graded') is not True or not isinstance(result.get('evaluation'), dict):
        raise ValueError('Completed artifact lacks a successful evaluation')
    try:
        receipt, evaluation = result['artifact'], result['evaluation']
        binding = _evaluation_binding(prepared['identity'], receipt, evaluation)
        if result.get('evaluation_binding') != binding:
            raise ValueError('Completed artifact evaluation binding mismatch')
        if (file_sha256(Path(receipt['pdf'])) != receipt['pdf_sha256'] or
                file_sha256(Path(receipt['source'])) != receipt['source_sha256']):
            raise ValueError('Completed artifact PDF or source was modified')
        session_path = output / 'contest_session.json'
        if Path(result['contest_file']).resolve() != session_path:
            raise ValueError('Completed artifact points to a different contest session')
        contest = json.loads(session_path.read_text(encoding='utf-8'))
        validate_run_identity(contest.get('run_identity'), prepared['identity'], artifact=session_path)
        source = contest.get('submissions', {}).get('deliverable')
        if (not source or sha256(source.encode('utf-8')).hexdigest() != receipt['source_sha256']
                or contest.get('session_checkpoint', {}).get('final_summary') is None):
            raise ValueError('Completed artifact is not bound to the finalized submission')
        rubric = load_rubric(prepared['rubric'])
        if evaluation.get('rubric_id') != rubric.rubric_id:
            raise ValueError('Completed artifact evaluation uses a different rubric')
        checked = EvaluationResult(**{**evaluation, 'criteria': [
            CriterionResult(**item) for item in evaluation['criteria']]})
        checked.validate(rubric)
    except (KeyError, TypeError, OSError) as exc:
        raise ValueError(f'Incomplete completed artifact: {exc}') from exc


def run_artifact_contest(prepared, *, agent_request, judge_request, resume=False,
                         renderer=None):
    p = prepared
    output = p['output'].resolve()
    identity_path = output / 'run_identity.json'
    if output.exists() and any(output.iterdir()):
        if not resume or not identity_path.is_file():
            raise ValueError('Nonempty output requires --resume and a matching run identity')
        validate_run_identity(json.loads(identity_path.read_text(encoding='utf-8')),
                              p['identity'], artifact=identity_path)
    elif resume:
        raise ValueError('No existing artifact run to resume')
    output.mkdir(parents=True, exist_ok=True)
    _write(identity_path, p['identity'])
    if (output / 'result.json').is_file():
        result = json.loads((output / 'result.json').read_text(encoding='utf-8'))
        if result.get('status') == 'complete':
            _validate_completed_result(p, result, output)
            return result
    renderer = renderer or ArtifactRenderer(output / 'versions', p['contract'])
    executor = EnvironmentTaskExecutor(p['manifest'], benchmark_root=ROOT / 'data/benchmarks',
                                      renderer=renderer, rule_card=p['card'])
    task_attachments = _attachments(p['task_asset'], p['provider'], output / 'task_pages')
    review_attachment_cache = {}
    checkpoint = None
    checkpoint_path = output / 'contest_checkpoint.json'
    if checkpoint_path.is_file():
        checkpoint = json.loads(checkpoint_path.read_text(encoding='utf-8'))
        validate_run_identity(checkpoint['run_identity'], p['identity'], artifact=checkpoint_path)
        task = checkpoint['session']['tasks'][0]
        if task['versions']:
            renderer(None, 'render_pdf', {'content': task['versions'][-1]['content']})
    calls_path = output / 'calls.jsonl'

    def invoke(fn, request):
        response = fn(request)
        with calls_path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'purpose': request.purpose, 'model': response.model,
                'usage': response.usage, 'tool_calls': [asdict(x) for x in response.tool_calls]},
                ensure_ascii=False) + '\n')
        return response

    def decorate(request, *, coach=False):
        if coach:
            return request  # Coach must never see the task PDF or rendered answer.
        attachments = task_attachments
        if renderer.latest:
            key = renderer.latest['source_sha256']
            if key not in review_attachment_cache:
                asset = build_task_asset(Path(renderer.latest['pdf']))
                review_attachment_cache[key] = _attachments(asset, p['provider'],
                    output / 'review_pages' / key)
            attachments += review_attachment_cache[key]
        return replace(request, system_prompt=request.system_prompt + '\n' + p['contract'].prompt(review_required=p['config'].review_required),
                       attachments=attachments)

    def query(system, user):
        coach = system.startswith('You are Coach')
        request = LLMRequest(system_prompt=system, user_prompt=user,
                             purpose='coach' if coach else 'private_think')
        return invoke(agent_request, decorate(request, coach=coach)).text

    def act(request):
        return invoke(agent_request, decorate(request))

    def persist(session, memory):
        _write(checkpoint_path, {'session': session, 'memory': memory,
                                 'run_identity': p['identity']})

    session_path = output / 'contest_session.json'
    if session_path.is_file():
        contest = json.loads(session_path.read_text(encoding='utf-8'))
        validate_run_identity(contest['run_identity'], p['identity'], artifact=session_path)
    else:
        contest = run_contest(p['manifest'], query, p['config'], action_request_fn=act,
            action_transport='native', coach_query_fn=query, task_action_executor=executor,
            checkpoint_callback=persist,
            session_checkpoint=checkpoint['session'] if checkpoint else None,
            memory_checkpoint=checkpoint['memory'] if checkpoint else None)
        contest['run_identity'] = p['identity']
        _write(session_path, contest)
    source = contest['submissions'].get('deliverable', '')
    if not source:
        result = dict(status='unsubmitted', graded=False,
                      reason='No artifact candidate was available for submission',
                      contest_file=str(session_path), run_identity=p['identity'])
        result['submission_diagnostics'] = submission_diagnostics(
            contest['session_checkpoint']['tasks'][0], p['config'].review_required)
        _write(output / 'result.json', result)
        return result
    task = contest['session_checkpoint']['tasks'][0]
    latest = task['versions'][-1]
    current_reviews = [r for r in task['reviews'] if not r['stale']
                       and r['version_hash'] == latest['version_hash']]
    deadline_collected = any(
        e['kind'] == 'deadline_drafts_submitted'
        and e['payload'].get('selected_versions', {}).get('deliverable', {}).get('version_hash') == latest['version_hash']
        for e in contest['memory']['events']
    )
    if (latest['content'] != source or (not deadline_collected and (
            not latest['evidence_refs'] or
            (p['config'].review_required and (any(r['decision'] == 'reject' for r in current_reviews) or
            not any(r['decision'] == 'approve' and r['reviewer'] != latest['author']
                    for r in current_reviews)))))):
        raise ValueError('Submitted artifact lacks current independent approval/render evidence')
    receipt = renderer(None, 'render_pdf', {'content': source})
    rubric = load_rubric(p['rubric'])
    def judge(request):
        return invoke(judge_request, request)
    _write(output / 'evaluation_status.json', {'status': 'started', 'pdf_sha256': receipt['pdf_sha256']})
    try:
        if p['contract'].kind == 'slides':
            evaluated = evaluate_slide_deck(task_pdf=p['task_asset'].path,
                task_pages=f"{p['task_asset'].page_start}-{p['task_asset'].page_end}",
                submission=Path(receipt['pdf']), rubric=rubric, work_dir=output / 'evaluation',
                provider=p['judge_provider'], model=p['judge_model'],
                media='images' if p['judge_provider'] in {'perplexity', 'pplx'} else 'pdf',
                min_slides=p['contract'].min_pages, max_slides=p['contract'].max_pages,
                max_file_size_mb=p['contract'].max_file_size_mb, request_fn=judge)
            evaluation = evaluated.evaluation.to_dict()
        else:
            evaluated = RubricDocumentEvaluator(request_fn=judge, rubric=rubric,
                task_asset=p['task_asset'], submission_pdf=Path(receipt['pdf']),
                media='images' if p['judge_provider'] in {'perplexity', 'pplx'} else 'pdf',
                image_work_dir=output / 'evaluation', task_label=p['card'].competition_id)
            evaluation = evaluated.evaluate().to_dict()
    except Exception as exc:
        _write(output / 'evaluation_status.json', {'status': 'failed', 'error': str(exc)})
        raise
    result = dict(status='complete', graded=True, artifact=receipt, evaluation=evaluation,
                  run_identity=p['identity'], contest_file=str(session_path),
                  comparability=p['card'].comparability,
                  scope='artifact-only proxy; does not score live/physical performance',
                  generation_budget=contest['budget'], judge_budget_separate=True)
    result['evaluation_binding'] = _evaluation_binding(p['identity'], receipt, evaluation)
    _write(output / 'result.json', result)
    _write(output / 'evaluation_status.json', {'status': 'complete'})
    return result
