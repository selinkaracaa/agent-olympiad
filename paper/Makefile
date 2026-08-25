TEX := main.tex
IMAGE ?= texlive/texlive:latest

.PHONY: all pdf static docker clean

all: static

static:
	python ../tests/test_paper_structure.py

pdf:
	latexmk -pdf -interaction=nonstopmode -halt-on-error $(TEX)

# Uses an image already present locally. Docker may otherwise offer to pull it;
# cancel that prompt and install/pull the image explicitly if desired.
docker:
	docker image inspect $(IMAGE) >/dev/null
	docker run --rm -v "$(CURDIR):/work" -w /work $(IMAGE) \
		latexmk -pdf -interaction=nonstopmode -halt-on-error $(TEX)

clean:
	latexmk -C
