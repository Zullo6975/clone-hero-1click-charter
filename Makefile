.PHONY: venv deps run test lint clean

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

run:
	$(PYTHON) -m charter.cli --audio samples/your_song.mp3 --out output/YourSong

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .

clean:
	rm -rf $(VENV) output .pytest_cache .ruff_cache
