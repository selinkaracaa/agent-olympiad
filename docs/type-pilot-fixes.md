# Representative pilot fixes

These changes do not rewrite old run identities, checkpoints or results and do
not launch new model calls. Use fresh output directories for future runs.

## QANTA

The native contest grader now removes answerline brace emphasis only for QANTA
and compares case/whitespace-normalized exact text against gold and explicit
aliases. It does not infer surnames or fuzzy spelling aliases. Other competition
grading is unchanged. This is not a full quizbowl answerline parser.

Offline replay of the same seven preserved submissions changes the score from
2/7 to 5/7. The three recovered matches are Margaret Sanger, Betelgeuse and
estuary. Gustav Kirchhoff versus stored Gustav Kirchoff remains unresolved;
the other unmatched question was unsubmitted. The original 2/7 is untouched;
5/7 is a current-grader diagnostic, not a new team run or baseline improvement.

## IEO

The renderer previously banned every meta element. It now permits UTF-8 charset
and passive named metadata (viewport, description, author, keywords). Unknown,
duplicate or active metadata, including http-equiv refresh, remains rejected.
Existing script, event-handler and resource-loading restrictions remain active.

All six original work attempts now render successfully to temporary PDFs. This
proves compatibility for the observed failure; it does not supply peer approval
or judge scores for the stopped experiment.

## IOL

The final version has a non-stale rejection identifying unresolved kinship
constraints. This was not an approval-state deadlock. The mandatory OTC review
contract remains intact; rejected answers are not automatically submitted.
Unsubmitted artifact results now include version-specific diagnostics separating
no rendered draft, missing render evidence, current rejection, missing independent
approval, and an eligible but unsubmitted draft. Rejection bodies are retained.
This improves diagnosis, not the team's ability to solve the puzzle.

## Reproduce without model calls

```powershell
..\.venv\Scripts\python.exe scripts/audit_type_pilot_fixes.py
$env:PYTHONPATH='src;tests;scripts'
..\.venv\Scripts\python.exe -m unittest discover -s tests -q
```

The audit reads the preserved pilot inputs and deletes only its own temporary
render directory on exit. It never writes into the original run directories.
