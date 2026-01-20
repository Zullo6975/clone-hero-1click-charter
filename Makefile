.PHONY: venv deps install reinstall help run run-real run-dummy gui doctor test lint clean clean-all build distcheck package icons run-dist

# -----------------------------------------------------------------------------
# 1. PLATFORM DETECTION & CONFIG
# -----------------------------------------------------------------------------
APP_NAME     := 1ClickCharter
ENTRY_SCRIPT := wrapper.py
ASSETS_DIR   := assets
SCRIPTS_DIR  := scripts
BIN_DIR      := bin

# Detect Windows vs Unix
ifeq ($(OS),Windows_NT)
    # Windows Configuration
    SEP        := ;
    VENV_DIR   := Scripts
    PYTHON_EXE := python.exe
    # Windows usually installs as 'python', not 'python3'
    PY         ?= python
else
    # macOS/Linux Configuration
    SEP        := :
    VENV_DIR   := bin
    PYTHON_EXE := python
    PY         ?= python3
endif

# Python Environment
VENV         := .venv
# Dynamically set bin/ or Scripts/ based on OS
VENV_BIN     := $(VENV)/$(VENV_DIR)
# Path to the python executable INSIDE the venv
PYTHON       := $(VENV_BIN)/$(PYTHON_EXE)
PIP          := $(VENV_BIN)/pip

# -----------------------------------------------------------------------------
# 2. CLI DEFAULT ARGUMENTS
# -----------------------------------------------------------------------------
AUDIO          ?= samples/test.mp3
OUT            ?= output/TestSong
TITLE          ?= Test Song
ARTIST         ?= Me
CHARTER        ?= Zullo7569
MODE           ?= real
MAX_NPS        ?= 2.8
SEED           ?= 42

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
	@echo "OS Detected:      $(if $(filter Windows_NT,$(OS)),Windows,Unix/Mac)"
	@echo "System Python:    $(PY)"
	@echo "VENV Dir:         $(VENV_BIN)"
	@echo "VENV Python:      $(PYTHON)"
	@echo "Checking PySide6..."
	@$(PYTHON) -c "import PySide6; print('✅ PySide6 OK')"
	@echo "Checking FFmpeg..."
	@$(PYTHON) -c "import sys, pathlib; p = pathlib.Path('$(BIN_DIR)') / ('ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg'); print('✅ Found local ffmpeg' if p.exists() else '❌ Missing local ffmpeg (Extract to /bin for dev)')"

# -----------------------------------------------------------------------------
# 4. RUNNING (CLI & GUI)
# -----------------------------------------------------------------------------
help:
	$(PYTHON) -m charter.cli --help

run:
	$(PYTHON) wrapper.py

gui: install
	$(PYTHON) wrapper.py

# -----------------------------------------------------------------------------
# 5. UTILS & BUILD
# -----------------------------------------------------------------------------
test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

# Cross-platform icon generation using Python (We will create this script next)
icons:
	@echo "🎨 Generating icons..."
	$(PYTHON) $(SCRIPTS_DIR)/make_icons.py

# Build Standalone (Cross Platform)
package: install icons
	@echo "🚀 Packaging $(APP_NAME)..."
	@$(PYTHON) -c "import shutil; shutil.rmtree('dist', ignore_errors=True); shutil.rmtree('build', ignore_errors=True)"
	$(VENV_BIN)/pyinstaller --noconfirm --clean \
		--name "$(APP_NAME)" \
		--windowed \
		--icon "$(ASSETS_DIR)/icons/AppIcon.icns" \
		--add-data "$(ASSETS_DIR)$(SEP)$(ASSETS_DIR)" \
		--add-binary "$(BIN_DIR)/ffmpeg$(if $(filter Windows_NT,$(OS)),.exe,)$(SEP)." \
		--add-binary "$(BIN_DIR)/ffprobe$(if $(filter Windows_NT,$(OS)),.exe,)$(SEP)." \
		--paths "." \
		--hidden-import "charter.cli" \
		--hidden-import "gui.qt_app" \
		--collect-all "charter" \
		$(ENTRY_SCRIPT)
	@echo "✅ Build complete!"

# -----------------------------------------------------------------------------
# 6. CLEANUP
# -----------------------------------------------------------------------------
# Use Python for cross-platform cleanup to avoid 'rm -rf' failures on Windows
clean:
	$(PY) -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').glob('dist')]; [shutil.rmtree(p) for p in pathlib.Path('.').glob('build')]; [shutil.rmtree(p) for p in pathlib.Path('.').glob('output')];"

clean-all: clean
	$(PY) -c "import shutil; shutil.rmtree('$(VENV)', ignore_errors=True)"
