.PHONY: venv deps install run help test lint clean

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
BARS ?= 20
DENSITY ?= 0.55


venv:
	$(PY) -m venv $(VENV)

deps: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

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
	  --bpm "$(BPM)" \
	  --bars "$(BARS)" \
	  --density "$(DENSITY)"

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .

clean:
	rm -rf $(VENV) output .pytest_cache .ruff_cache
