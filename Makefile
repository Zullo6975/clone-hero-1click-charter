.PHONY: venv deps install reinstall help run run-real run-dummy gui doctor test lint clean clean-all build distcheck pipx-install package icons run-dist full

# -----------------------------------------------------------------------------
# 1. PROJECT CONFIGURATION
# -----------------------------------------------------------------------------
APP_NAME     := 1ClickCharter
ENTRY_SCRIPT := wrapper.py
ASSETS_DIR   := assets
SCRIPTS_DIR  := scripts
BIN_DIR      := bin

# Python Environment
PY           ?= python3
VENV         := .venv
VENV_BIN     := $(VENV)/bin
PIP          := $(VENV_BIN)/pip
PYTHON       := $(VENV_BIN)/python

# OS Detection for Path Separators (Win uses ';', Unix uses ':')
SEP := $(if $(filter Windows_NT,$(OS)),;,:)

# -----------------------------------------------------------------------------
# 2. CLI DEFAULT ARGUMENTS
# -----------------------------------------------------------------------------
AUDIO          ?= samples/test.mp3
OUT            ?= output/TestSong
TITLE          ?= Test Song
ARTIST         ?= Me
ALBUM          ?=
GENRE          ?=
YEAR           ?=
CHARTER        ?= Zullo7569
DELAY_MS       ?= 0
MODE           ?= real
MIN_GAP_MS     ?= 140
MAX_NPS        ?= 2.8
SEED           ?= 42
FETCH_METADATA ?= 1
USER_AGENT     ?= 1clickcharter/0.1 (Zullo7569)

# -----------------------------------------------------------------------------
# 3. ENVIRONMENT & DEPENDENCIES
# -----------------------------------------------------------------------------
venv:
	$(PY) -m venv $(VENV)

deps: venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev,gui]"
	$(PIP) install pyinstaller Pillow

install: deps

reinstall: clean-all install

doctor:
	@echo "PY (builder):     $(PY)"
	@echo "VENV python:      $$($(PYTHON) -c 'import sys; print(sys.executable)')"
	@echo "VENV version:     $$($(PYTHON) -V)"
	@echo "Qt (PySide6):     $$($(PYTHON) -c 'import PySide6; print(\"✅ PySide6 OK\")' 2>/dev/null || echo '❌ PySide6 missing')"
	@echo "FFmpeg (Bin):     $$(ls $(BIN_DIR)/ffmpeg >/dev/null 2>&1 && echo '✅ Found in $(BIN_DIR)' || echo '❌ Missing')"

# -----------------------------------------------------------------------------
# 4. RUNNING (CLI & GUI)
# -----------------------------------------------------------------------------
# Main CLI Help
help:
	$(VENV_BIN)/1clickcharter --help

# Run CLI with arguments
run:
	PATH="$(CURDIR)/$(BIN_DIR):$$PATH" $(VENV_BIN)/1clickcharter \
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
	  $(if $(filter 1,$(FETCH_METADATA)),--fetch-metadata,) \
	  --user-agent "$(USER_AGENT)"

run-real:
	$(MAKE) run MODE=real

run-dummy:
	$(MAKE) run MODE=dummy

# Run GUI
gui: install
	PATH="$(CURDIR)/$(BIN_DIR):$$PATH" $(VENV_BIN)/1clickcharter-gui

# -----------------------------------------------------------------------------
# 5. DEVELOPMENT TOOLS
# -----------------------------------------------------------------------------
test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

# Opens the output folder on macOS/Linux
open-out:
	open "$(dir $(OUT))" 2>/dev/null || xdg-open "$(dir $(OUT))" 2>/dev/null || true

# -----------------------------------------------------------------------------
# 6. BUILDING & PACKAGING
# -----------------------------------------------------------------------------
# Build Python Wheel / Source Dist
build: install
	$(PYTHON) -m build

distcheck: build
	$(PYTHON) -m twine check dist/*

# Generate Icons using the script
icons:
	@chmod +x $(SCRIPTS_DIR)/make_icons.sh
	@echo "🎨 Generating icons..."
	@./$(SCRIPTS_DIR)/make_icons.sh

# Build Standalone Application (PyInstaller)
# Note: Maps 'assets' folder to 'assets' in bundle
package: install icons
	@echo "🚀 Packaging $(APP_NAME)..."
	@rm -rf dist build
	@$(VENV_BIN)/pyinstaller --noconfirm --clean \
		--name "$(APP_NAME)" \
		--windowed \
		--icon "$(ASSETS_DIR)/icons/AppIcon.icns" \
		--add-data "$(ASSETS_DIR)$(SEP)$(ASSETS_DIR)" \
		--add-binary "$(BIN_DIR)/ffmpeg$(SEP)." \
		--add-binary "$(BIN_DIR)/ffprobe$(SEP)." \
		--paths "." \
		--hidden-import "charter.cli" \
		--hidden-import "gui.qt_app" \
		--collect-all "charter" \
		$(ENTRY_SCRIPT)
	@echo "✅ Build complete! App is in dist/$(APP_NAME).app"

# Run the packaged app (macOS specific path)
run-dist:
	@dist/$(APP_NAME).app/Contents/MacOS/$(APP_NAME)

# Full loop: Package then Run
app: package run-dist

# -----------------------------------------------------------------------------
# 7. CLEANUP
# -----------------------------------------------------------------------------
# Standard clean: Removes build artifacts but keeps virtual env
clean:
	rm -rf dist build output *.spec *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

# Deep clean: Removes everything including venv
clean-all: clean
	rm -rf $(VENV)
