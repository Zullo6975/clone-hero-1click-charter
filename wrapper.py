import sys
import os
import multiprocessing

from gui.qt_app import main as gui_main
from charter import cli as cli_module 

def setup_path():
    """
    If running as a frozen PyInstaller bundle, add the internal extraction
    directory to the PATH so pydub can find the bundled ffmpeg/ffprobe.
    """
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        # Append the bundle directory to the system PATH
        os.environ["PATH"] += os.pathsep + bundle_dir

def run():
    multiprocessing.freeze_support()
    setup_path()

    # TRAFFIC COP: Did the subprocess call us with the secret flag?
    if "--internal-cli" in sys.argv:
        sys.argv.remove("--internal-cli")
        cli_module.main()
    else:
        gui_main()

if __name__ == "__main__":
    run()