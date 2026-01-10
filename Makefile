SHELL = /bin/bash

ifndef VIRTUAL_ENV
WITH_VENV := uv run
else
WITH_VENV :=
endif
PYTHON := $(WITH_VENV) python

UNAME := $(shell uname -s)
ifeq ($(UNAME),Linux)
    date = date
endif
ifeq ($(UNAME),Darwin)
    # brew install coreutils
    date = gdate
endif

export PYTHONPATH := $(shell pwd)

.DEFAULT_GOAL := test

# FORCE make the target always run, https://www.gnu.org/software/make/manual/html_node/Force-Targets.html
FORCE:

#-------------------------------------------------------------------------------
SUNDAY := $(shell $(date) -d "next sunday" +"%Y-%m-%d")

OPT := -v 1

#-------------------------------------------------------------------------------
# online resources

.PHONY: zanmei
zanmei:
	$(PYTHON) -m hymns.zanmei $(OPT)

.PHONY: hoctoga
hoctoga:
	$(PYTHON) -m hymns.hoctoga $(OPT)

.PHONY: hoc5
hoc5:
	$(PYTHON) -m hymns.hoc5 $(OPT)

.PHONY: mvccc
mvccc:
	$(PYTHON) -m hymns.mvccc $(OPT)

.PHONY: stats
stats:
	$(PYTHON) -m hymns.stats $(OPT)

.PHONY: ibibles.net
ibibles.net:
	[ -e download/cut/books.txt ] || (cd download && curl -L -O http://download.ibibles.net/cut.zip && unzip -o cut.zip)

.PHONY: bible.cloud
bible.cloud:
	[ -e download/CMNUNV.epub ] || (cd download && curl -L -O https://bible.cloud/ebooks/epub/CMNUNV.epub)

download: zanmei hoctoga hoc5 mvccc ibibles.net bible.cloud

#-------------------------------------------------------------------------------
.PHONY: pptx
# create slides for sunday service
pptx:
	$(PYTHON) mvccc/slides.py $(OPT) --pptx=$(SUNDAY).pptx --flagfile=services/$(SUNDAY).flags
slides:pptx

.PHONY: pptx_to_text
# extract text from a pptx file
pptx_to_text:
ifdef PPTX
	$(PYTHON) mvccc/slides.py --extract_only --pptx $(PPTX)
else
	echo "make pptx_to_text PPTX=xxx.pptx"
endif

streamlit-slides:
	uv run streamlit run         \
	  --server.port=8501           \
	  mvccc/slidesapp.py           \
	  --server.baseUrlPath=slides  \
	  # END
	  # https://github.com/streamlit/streamlit/issues/521

ipykernel:
	uv run python -m ipykernel install --user --name zanmei --display-name "python(zanmei)"

notebook: ipykernel
	uv run jupyter notebook              \
	  --NotebookApp.open_browser=False       \
	  --NotebookApp.port=8088                \
	  --NotebookApp.base_url='/notebook/'    \
	  --NotebookApp.allow_remote_access=True \
	# END

jupyter:
	uv run jupyter notebook

#-------------------------------------------------------------------------------
VERSES := 約翰福音3:16

.PHONY: scripture
scripture:
ifdef VERSES
	$(PYTHON) -m bible.scripture --bible_citations "$(VERSES)"
else
	$(PYTHON) -m bible.scripture
endif

.PHONY: scripture_compare
scripture_compare:
	$(PYTHON) -m bible.scripture --bible_source=ibibles.net --bible_text=download/cut/books.txt --bible_citations "$(VERSES)"
	$(PYTHON) -m bible.scripture --bible_source=bible.cloud --bible_text=download/CMNUNV.epub --bible_citations "$(VERSES)"

#-------------------------------------------------------------------------------
# development related

#-------------------------------------------------------------------------------
# code quality

.PHONY: format
format:
	$(PYTHON) -m ruff format .

.PHONY: lint
lint:
	$(PYTHON) -m ruff check .

.PHONY: fix
fix:
	$(PYTHON) -m ruff check --fix .

.PHONY: check
check: lint test

test: lint
	$(PYTHON) -m pytest --capture=no --verbose

# Run individual unittest file, e.g.
# 	make tests/bible/test_index.py
test_%.py: FORCE
	$(PYTHON) -m pytest -v --capture=no $@

.PHONY: ipython
ipython:
	uv run ipython

.PHONY: install-uv
install-uv:
	@command -v uv >/dev/null 2>&1 || pip install uv

.PHONY: uv-sync
uv-sync:
	uv sync --extra dev

.PHONY: uv-lock
uv-lock:
	uv lock

init: install-uv uv-sync download

.PHONY: init-fast
init-fast: install-uv uv-sync
