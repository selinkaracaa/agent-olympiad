# Paper draft

This directory is the Phase 5 paper skeleton. Its
`agentolympiad_iclr_standin.sty` is a self-contained, temporary ICLR-like
layout aid. It is **not the official ICLR template** and must be replaced after
the target venue and year are fixed.

## Validate without LaTeX

From the repository root:

```bash
python tests/test_paper_structure.py
python -m unittest discover -s tests -v
```

The static validator checks required files, `\input` targets, citation keys,
balanced braces, the temporary-style warning, and required research-document
headings. It does not replace a real TeX compilation.

## Build locally

With `latexmk` and a TeX Live distribution installed:

```bash
cd paper
make pdf
```

## Build with an existing Docker image

The Makefile checks that the image already exists before running it, so this
path does not automatically download anything:

```bash
cd paper
docker pull texlive/texlive:latest  # explicit, optional one-time user action
make docker
```

Override the image with `make docker IMAGE=<locally-installed-image>`. The
container mounts only `paper/` at `/work`; generated LaTeX outputs remain in
that directory. No LaTeX toolchain was available when this skeleton was
created, so only static validation was run.
