# OTC artifact pipeline

OTC now uses the same contest engine for native answers/code and single-artifact
tasks. The old presentation discussion/synthesis loop has been replaced by a
compatibility entry point into this pipeline. This is a software capability,
not evidence that OTC outperforms a baseline.

## Execution

Rule card + task PDF → one turn-0 Coach intervention → private thinking, shared
memory and legal collaboration actions → complete candidate source via work →
real PDF rendering and validation → another contestant reviews source and PDF →
approved current version submitted unchanged → separate rubric judge.

Rendering occurs before a version becomes reviewable. Rendering failure,
oversized source, rejection, missing approval, or no submission cannot produce a
graded result. No final editor can rewrite a reviewed candidate. Source/PDF
hashes and rendering evidence are stored with the version. Judge failure can be
resumed without rerunning the team; changed run identity or tampered files block
reuse. Rubric configuration is controller/judge-only, not contestant prompt input.

Slides are self-contained HTML rendered by Chrome/Edge to PDF. Active content,
external resources, and local-file references are rejected. Documents are plain
text paginated by ReportLab to PDF; this is not a LaTeX or rich word-processing
renderer. Output includes editable HTML/text and PDF, not an editable PPTX deck.
Peer review receives rendered pages, but a model's approval is not a guarantee of
visual or factual correctness.

## Rule cards and scope

All 38 cards have a valid canonical OTC collaboration configuration. Original
official rules/scoring metadata and existing card storage remain intact; added
delivery limits are explicitly simulation/benchmark settings, not invented
official requirements. Newly configured collaboration does not imply all
official phases, workstations, opponents, or physical actions are implemented.

| Route | Cards | Current scope |
| --- | ---: | --- |
| Native answer/code/etc. | 14 | Existing runner; evaluator readiness still varies |
| Document | 11 | Single text document → PDF; 8 have local rubrics |
| Slides | 2 | HTML → PDF; IEO has a local rubric |
| External environment | 10 | Specialized execution adapters still required |
| Artifact bundle | 1 | CFA report + presentation still needs a bundle adapter |

The nine locally rubric-configured artifact cards are IEO Business Case,
ARML Power, ARML National Power, IJSO Practical, IOAA Group, IOL Team, Jessup,
Vis Moot, and WSC Writing. These are artifact-only benchmark evaluations;
oral defense, physical experiments, and other missing official components are
not graded as though observed. Existing rubric observability/limitations remain
part of the judge output.

GCCH Harvard, EOES, PUMaC Power, and Wharton Investment require a sourced rubric
before grading. The runner fails before contestant calls if it is absent; it
does not invent weights. CFA bundles and live environments are rejected by the
artifact runner. The generic batch runner rejects artifact routes instead of
silently treating their source as a finished text answer.

Page/file limits and format are under simulation.deliverable_pipeline.
Team size and round budget default to the card. Artifact rounds use the card's
simulation.max_turns; no official elapsed-time model is inferred for multi-day
projects (minutes_per_turn = 0). Explicit overrides are recorded in run identity.
The turn-0 Coach call and private-thinking calls are included in the generated
API-call budget. Judge calls are separately recorded, outside the team budget.
Image-mode grading supports at most 20 task and 20 submission pages; use an
explicit task-page selection or PDF judge for larger tasks.

## Commands

From the repository root, with dependencies in requirements.txt installed:

```powershell
$env:PYTHONPATH='src'
..\.venv\Scripts\python.exe -m audit_otc_capabilities
..\.venv\Scripts\python.exe src/run_otc_artifact.py --competition ieo_business_case --task-pdf PATH_TO_TASK.pdf --output results/ieo_otc_artifact --prepare-only
..\.venv\Scripts\python.exe src/run_otc_artifact.py --competition ieo_business_case --task-pdf PATH_TO_TASK.pdf --output results/ieo_otc_artifact --provider perplexity
```

The last command makes paid model calls. Use --model / --judge-provider /
--judge-model explicitly for controlled experiments. --prepare-only validates the
card, rubric, task and rendering dependency without model calls. --resume requires
the same task, card, models, budgets, source identity and existing output.
--rubric supplies an explicit rubric override, fingerprinted for provenance.

The legacy run_presentation_artifact.py entry accepts --benchmark/--problem-id,
--agent-model and --rounds aliases. Direct task-PDF use now requires --competition.
Legacy --min-slides, --max-slides, --max-file-size-mb and --media arguments are not
silently accepted: configure format limits in the card and choose judge provider.

## Verification

Offline integration tests use mocked contestants and judges with real
HTML/document-to-PDF rendering. They check independent review, frozen PDF
identity, no judge-rubric injection, resume, changed identity, tamper detection,
unsubmitted/rejected/oversized drafts, and legacy entry delegation. These are
plumbing tests, not real contest scores or proof of judging quality.
