from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

# Import the main window from our new module
from gui.main_window import MainWindow
from gui.utils import repo_root

def main() -> None:
    if "--internal-cli" in sys.argv:
        sys.argv.remove("--internal-cli")
        from charter import cli
        sys.exit(cli.main())

    app = QApplication(sys.argv)

    # FIX: Load and set the application icon globally
    icon_path = repo_root() / "assets" / "icons" / "icon_og.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    font = QApplication.font()
    font.setPointSize(10)
    app.setFont(font)

    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
