import sys
import os
from pathlib import Path


def setup_frozen_env():
    """Add bundled bin directory to PATH so FFmpeg is discoverable."""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
        os.environ["PATH"] += os.pathsep + str(base_path)


setup_frozen_env()

from gui import qt_app  # noqa: E402

if __name__ == "__main__":
    qt_app.main()
