.PHONY: venv deps install reinstall help run run-real run-dummy gui doctor test lint clean clean-all build distcheck pipx-install package icons run-dist full

# -----------------------------------------------------------------------------
# 1. CROSS-PLATFORM CONFIGURATION
# -----------------------------------------------------------------------------
APP_NAME     := 1ClickCharter
ENTRY_SCRIPT := wrapper.py
ASSETS_DIR   := assets
SCRIPTS_DIR  := scripts
BIN_DIR      := bin

# --- OS DETECTION & VARIABLE ASSIGNMENT ---
ifeq ($(OS),Windows_NT)
    # Windows Settings
    DETECTED_OS  := Windows
    VENV_DIR     := .venv
    # Windows uses 'Scripts' folder
    VENV_BIN     := $(VENV_DIR)\Scripts

    # Executable names (Windows needs .exe)
    PYTHON_EXEC  := $(VENV_BIN)\python.exe
    PIP_EXEC     := $(VENV_BIN)\pip.exe
    GUI_EXEC     := $(VENV_BIN)\1clickcharter-gui.exe
    CLI_EXEC     := $(VENV_BIN)\1clickcharter.exe

    # Path Separator
    SEP          := ;

    # Cleaning via Python to handle permission errors gracefully on Windows
    CLEAN_CMD    := python -c "import shutil, glob, time; [shutil.rmtree(p, ignore_errors=True) for p in ['dist', 'build', 'output', '$(VENV_DIR)']]"

    # Execution Preamble (Cmd.exe style)
    # We use 'call' to ensure environment variables persist for the command duration
    EXEC_PRE     := set "PATH=$(CURDIR)\$(BIN_DIR);%PATH%" &&

    # Extensions
    EXE_EXT      := .exe
    ICON_EXT     := .ico

else
    # macOS / Linux Settings
    DETECTED_OS  := macOS
    VENV_DIR     := .venv
    VENV_BIN     := $(VENV_DIR)/bin

    # Executable names
    PYTHON_EXEC  := $(VENV_BIN)/python3
    PIP_EXEC     := $(VENV_BIN)/pip3
    # On Unix, we execute the script directly (it has the shebang)
    GUI_EXEC     := $(VENV_BIN)/1clickcharter-gui
    CLI_EXEC     := $(VENV_BIN)/1clickcharter

    # Path Separator
    SEP          := :

    # Unix file deletion
    CLEAN_CMD    := rm -rf dist build output *.spec *.egg-info $(VENV_DIR)

    # Execution Preamble (Shell style)
    EXEC_PRE     := PATH="$(CURDIR)/$(BIN_DIR):$$PATH"

    # Extensions
    EXE_EXT      :=
    ICON_EXT     := .icns
endif

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
	@echo "Creating venv for $(DETECTED_OS)..."
ifeq ($(DETECTED_OS),Windows)
	py -m venv $(VENV_DIR)
else
	python3 -m venv $(VENV_DIR)
endif

deps: venv
	$(PIP_EXEC) install --upgrade pip
	$(PIP_EXEC) install -e ".[dev,gui]"
	$(PIP_EXEC) install pyinstaller Pillow

install: deps

reinstall: clean-all install

doctor:
	@echo "OS:             $(DETECTED_OS)"
	@echo "VENV Python:    $(PYTHON_EXEC)"
	@echo "GUI Executable: $(GUI_EXEC)"
	@echo "PySide6:        $$($(PYTHON_EXEC) -c 'import PySide6; print("✅ PySide6 OK")' 2>/dev/null || echo '❌ PySide6 missing')"
	@$(PYTHON_EXEC) -c "import os; print('✅ Found ffmpeg' if os.path.exists('$(BIN_DIR)/ffmpeg$(EXE_EXT)') else '❌ ffmpeg missing')"

# -----------------------------------------------------------------------------
# 4. RUNNING (CLI & GUI)
# -----------------------------------------------------------------------------
help:
	$(CLI_EXEC) --help

run:
	$(EXEC_PRE) $(CLI_EXEC) \
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

gui: install
	@echo "Starting GUI..."
	$(EXEC_PRE) $(GUI_EXEC)

# -----------------------------------------------------------------------------
# 5. DEVELOPMENT TOOLS
# -----------------------------------------------------------------------------
test:
	$(PYTHON_EXEC) -m pytest

lint:
	$(PYTHON_EXEC) -m ruff check .

# -----------------------------------------------------------------------------
# 6. BUILDING & PACKAGING
# -----------------------------------------------------------------------------
package: install
	@echo "🚀 Packaging $(APP_NAME) for $(DETECTED_OS)..."
	$(PYTHON_EXEC) -m PyInstaller --noconfirm --clean \
	    --name "$(APP_NAME)" \
	    --windowed \
	    --icon "$(ASSETS_DIR)/icons/AppIcon$(ICON_EXT)" \
	    --add-data "$(ASSETS_DIR)$(SEP)$(ASSETS_DIR)" \
	    --add-binary "$(BIN_DIR)/ffmpeg$(EXE_EXT)$(SEP)." \
	    --add-binary "$(BIN_DIR)/ffprobe$(EXE_EXT)$(SEP)." \
	    --paths "." \
	    --hidden-import "charter.cli" \
	    --hidden-import "gui.qt_app" \
	    --collect-all "charter" \
	    $(ENTRY_SCRIPT)
	@echo "✅ Build complete!"

# -----------------------------------------------------------------------------
# 7. CLEANUP
# -----------------------------------------------------------------------------
clean:
	@echo "Cleaning build artifacts..."
	$(PYTHON_EXEC) -c "import shutil, glob, os; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('dist') + glob.glob('build') + glob.glob('*.egg-info')]"

clean-all: clean
	@echo "Removing Virtual Environment..."
	$(CLEAN_CMD)
