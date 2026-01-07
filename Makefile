.PHONY: venv deps install reinstall help run run-real run-dummy gui doctor test lint clean open-out

# ---- Python selection (macOS-friendly) ----
# Prefer Homebrew Python (often has Tk). Fallback to python3.
PY ?= /opt/homebrew/bin/python3
VENV := .venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
PYTHON := $(BIN)/python

# ---- Defaults for CLI ----
AUDIO ?= samples/test.mp3
OUT ?= output/TestSong
TITLE ?= Test Song
ARTIST ?= Me
ALBUM ?=
GENRE ?=
YEAR ?=
CHARTER ?= Zullo7569
DELAY_MS ?= 0

BPM ?= 115
BARS ?= 24
DENSITY ?= 0.58

MODE ?= dummy
MIN_GAP_MS ?= 140
MAX_NPS ?= 3.8
SEED ?= 42

FETCH_METADATA ?= 1
USER_AGENT ?= 1clickcharter/0.1 (Zullo7569)

# ---- venv / deps ----
venv:
	$(PY) -m venv $(VENV)

deps: venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

install: deps

reinstall:
	rm -rf $(VENV)
	$(MAKE) install

# ---- sanity checks ----
doctor:
	@echo "PY (builder):     $(PY)"
	@echo "VENV python:      $$($(PYTHON) -c 'import sys; print(sys.executable)')"
	@echo "VENV version:     $$($(PYTHON) -V)"
	@echo "VENV pip:         $$($(PIP) -V)"
	@echo "Tkinter check:    (attempting import...)"
	@$(PYTHON) -c "import tkinter; print('✅ tkinter OK')" || (echo "❌ tkinter import failed"; exit 1)
	@echo "1clickcharter:    $$($(BIN)/1clickcharter --help >/dev/null 2>&1 && echo '✅ installed' || echo '❌ not installed')"

# ---- CLI ----
help:
	$(BIN)/1clickcharter --help

run:
	$(BIN)/1clickcharter \
	  --audio "$(AUDIO)" \
	  --out "$(OUT)" \
	  --title "$(TITLE)" \
	  --artist "$(ARTIST)" \
	  --album "$(ALBUM)" \
	  --genre "$(GENRE)" \
	  --year "$(YEAR)" \
	  --charter "$(CHARTER)" \
	  --delay-ms "$(DELAY_MS)" \
	  --mode "$(MODE)" \
	  --min-gap-ms "$(MIN_GAP_MS)" \
	  --max-nps "$(MAX_NPS)" \
	  --seed "$(SEED)" \
	  --bpm "$(BPM)" \
	  --bars "$(BARS)" \
	  --density "$(DENSITY)" \
	  $(if $(filter 1,$(FETCH_METADATA)),--fetch-metadata,) \
	  --user-agent "$(USER_AGENT)"

run-real:
	$(MAKE) run MODE=real

run-dummy:
	$(MAKE) run MODE=dummy

# ---- GUI ----
gui: install
	$(PYTHON) gui/app.py

# ---- dev ----
test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .

# ---- convenience ----
open-out:
	open "$(dir $(OUT))" 2>/dev/null || true

clean:
	rm -rf $(VENV) output .pytest_cache .ruff_cache .cache
