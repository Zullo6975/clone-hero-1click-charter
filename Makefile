.PHONY: venv deps install run help test lint clean

PY := python3
VENV := .venv
BIN := $(VENV)/bin
PIP := $(BIN)/pip
PYTHON := $(BIN)/python

venv:
	$(PY) -m venv $(VENV)

deps: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

install: deps

help:
	$(BIN)/1clickcharter --help

run:
	$(BIN)/1clickcharter --audio samples/your_song.mp3 --out output/YourSong

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .

clean:
	rm -rf $(VENV) output .pytest_cache .ruff_cache
