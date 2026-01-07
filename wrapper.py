import sys
import multiprocessing

from gui.qt_app import main as gui_main
from charter import cli as cli_module 

def run():
    multiprocessing.freeze_support()

    # TRAFFIC COP: Did the subprocess call us with the secret flag?
    if "--internal-cli" in sys.argv:
        sys.argv.remove("--internal-cli")
        cli_module.main()
    else:
        gui_main()

if __name__ == "__main__":
    run()