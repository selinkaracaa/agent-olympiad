# OTC v6 implementation and verification — 2026-09-10

This implements the user's current OTC, not Selin's retired OTC. The protocol is
`contest_session_v6`; all 13 shipped OTC cards declare `otc_turn0_review_v1`.

## Implemented behavior

- Coach makes exactly one problem-blind brief at turn 0, costing one API call
  but no contest time. No opening summary or Coach assignment follows. Resume
  restores the brief instead of calling Coach again.
- Independent approval of the current answer hash is mandatory. Self-review
  is invalid, a current rejection blocks submission, and revisions invalidate
  older reviews. The default has no redundant whole-contest final-review pass.
- Math deadline collection includes approved current answers only. Programming
  deadline submission additionally requires recorded sample evidence; it cannot
  waive approval. The user's private think, memory and discussion mechanisms stay.
- Cards, CLI and validation scripts agree on one Coach call and the action bundles.
  The shared action normalizer handles aliases while preserving per-turn schemas.
  `allowed_actions` on the card is the core bundle, not the entire action registry.
- ARML Local defaults to the competition card's 45 minutes / 9 rounds. National
  team remains 20 minutes / 4 rounds; no shipped OTC card has min_turns > max_turns.
- ICPC has one team-wide workstation lease, including across problem switches.
  A source-production gate cannot force an action forbidden by that lease.
- Actual judge verdicts stay controller-private until the configured delivery
  round: score, lock, penalty and reopen are also delayed. Pending source is
  frozen, but analysis remains available. Queue delivery is checkpoint-safe and
  idempotent; final settlement flushes pending verdicts. Ranking retains the
  original submission turn, not the later verdict-delivery turn.
- Historical result files are untouched; the existing identity guard rejects
  v5/v6 reuse. Old aliases resolve to the one canonical `otc` implementation.

## Verification

Command: `python -m unittest discover -s tests -q`, with
`PYTHONPATH=src;tests;scripts`: **454 tests passed**.

The new `test_otc_v6_contract.py` covers independent/current approval, rejection,
deadline gates, global lease, private and exactly-once verdict delivery, resume,
all 13 cards, and dynamic action schema preservation. OTC replay fingerprints
were intentionally migrated. All eight original Vanilla/Centralized fresh/resume
fingerprints remain identical after normalizing only the protocol-version label.

Two CLI test classes now restore environment variables after loading `.env`,
preventing remote VJudge settings from contaminating later local judge tests.

2012 paired prepare-only preflight passed:

| Contest | Tasks | Team | Rounds | API ceiling per variant |
|---|---:|---:|---:|---:|
| ARML Local 2012 | 9 | 6 | 9 | 109 |
| ICPC WF 2012 | 12 | 3 | 60 | 361 |

No new paid evaluation was started. These tests establish implementation
correctness, not a score improvement. Fresh matched evaluations are required;
the older ARML runs used different clock/review settings.
