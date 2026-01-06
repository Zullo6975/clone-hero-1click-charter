.PHONY: venv deps install help run test lint clean

PY := python3
VENV := .venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
PYTHON := $(BIN)/python
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

venv:
	$(PY) -m venv $(VENV)

deps: venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

install: deps

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

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .

clean:
	rm -rf $(VENV) output .pytest_cache .ruff_cache .cache
