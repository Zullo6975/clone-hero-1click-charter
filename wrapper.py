import sys
import os
from pathlib import Path

# --- FIX: Setup Pydub & FFmpeg environment BEFORE imports ---
def setup_ffmpeg_env():
    """
    Ensures pydub can find the bundled ffmpeg/ffprobe binaries.
    """
    if getattr(sys, 'frozen', False):
        # We are running in a bundle
        base_path = Path(sys._MEIPASS)

        # 1. Add bundle dir to PATH (so pydub's subprocess calls find it)
        os.environ["PATH"] += os.pathsep + str(base_path)

        # 2. Explicitly tell pydub where they are
        # (We import inside here to avoid global side effects before setup)
        try:
            from pydub import AudioSegment

            ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
            ffprobe_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"

            ffmpeg_path = base_path / ffmpeg_name
            ffprobe_path = base_path / ffprobe_name

            if ffmpeg_path.exists():
                AudioSegment.converter = str(ffmpeg_path)

            # Pydub doesn't have a direct 'ffprobe' setter in all versions,
            # but adding to PATH above usually fixes it.

        except ImportError:
            pass # Pydub might not be installed yet (unlikely in frozen app)

setup_ffmpeg_env()
# ------------------------------------------------------------

from gui import qt_app_premod

if __name__ == "__main__":
    qt_app_premod.main()
