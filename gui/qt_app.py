from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication

# Import the main window from our new module
from gui.main_window import MainWindow

def main() -> None:
    if "--internal-cli" in sys.argv:
        sys.argv.remove("--internal-cli")
        from charter import cli
        sys.exit(cli.main())

    app = QApplication(sys.argv)
    font = QApplication.font()
    font.setPointSize(10)
    app.setFont(font)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
