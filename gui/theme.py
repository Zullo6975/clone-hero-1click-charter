from __future__ import annotations
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtCore import Qt

class ThemeManager:
    @staticmethod
    def apply_style(app: QApplication, dark_mode: bool):
        app.setStyle("Fusion")

        font = QFont()
        font.setPointSize(11)
        app.setFont(font)
        palette = QPalette()

        if dark_mode:
            # Dark Theme
            base = QColor(30, 35, 40)
            mid = QColor(45, 50, 55)
            text = QColor(220, 220, 220)
            highlight = QColor(50, 120, 210)

            palette.setColor(QPalette.Window, base)
            palette.setColor(QPalette.WindowText, text)
            palette.setColor(QPalette.Base, mid)
            palette.setColor(QPalette.AlternateBase, base)
            palette.setColor(QPalette.Text, text)
            palette.setColor(QPalette.Button, mid)
            palette.setColor(QPalette.ButtonText, text)
            palette.setColor(QPalette.Highlight, highlight)
            palette.setColor(QPalette.HighlightedText, Qt.white)

            palette.setColor(QPalette.Light, QColor(60, 65, 70))
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(100, 100, 100))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100, 100, 100))
            palette.setColor(QPalette.PlaceholderText, QColor(120, 130, 140))

            line_color = "rgba(255, 255, 255, 0.15)"

        else:
            # Light Theme
            base = QColor(245, 245, 250)
            white = QColor(255, 255, 255)
            text = QColor(30, 30, 40)
            highlight = QColor(0, 100, 200)
            btn_bg = QColor(255, 255, 255)

            palette.setColor(QPalette.Window, base)
            palette.setColor(QPalette.WindowText, text)
            palette.setColor(QPalette.Base, white)
            palette.setColor(QPalette.AlternateBase, base)
            palette.setColor(QPalette.Text, text)
            palette.setColor(QPalette.Button, btn_bg)
            palette.setColor(QPalette.ButtonText, text)
            palette.setColor(QPalette.Highlight, highlight)
            palette.setColor(QPalette.HighlightedText, white)

            palette.setColor(QPalette.Light, QColor(255, 255, 255))
            palette.setColor(QPalette.Midlight, QColor(230, 230, 240))
            palette.setColor(QPalette.Dark, QColor(200, 200, 210))
            palette.setColor(QPalette.Mid, QColor(210, 210, 220))
            palette.setColor(QPalette.Shadow, QColor(150, 150, 160))

            disabled_text = QColor(160, 160, 170)
            palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)
            palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
            palette.setColor(QPalette.PlaceholderText, QColor(150, 150, 160))

            line_color = "rgba(0, 0, 0, 0.12)"

        app.setPalette(palette)

        # Stylesheet overrides
        app.setStyleSheet(f"""
            QFrame#HeaderLine {{
                background-color: {line_color};
            }}

            QGroupBox {{
                border: 1px solid palette(mid);
                border-radius: 6px;
                margin-top: 24px;
                padding-top: 12px;
                font-weight: bold;
                font-size: 11pt;
                max-width: 550px;
            }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}

            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QListWidget {{
                padding: 5px;
                border-radius: 4px;
                border: 1px solid palette(mid);
                background-color: palette(base);
                color: palette(text);
                min-height: 18px;
                max-width: 425px;
                font-size: 11pt;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus, QListWidget:focus, QSlider:focus {{
                border: 1px solid palette(highlight);
            }}

            /* Disabled Inputs */
            QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
                background-color: palette(window);
                color: palette(disabled-text);
                border: 1px dashed palette(mid);
            }}

            QComboBox QAbstractItemView {{
                background-color: palette(base);
                color: palette(text);
                selection-background-color: palette(highlight);
                selection-color: palette(highlighted-text);
            }}

            /* STANDARD BUTTONS - SCALED DOWN */
            QPushButton {{
                padding: 5px 10px;
                border-radius: 5px;
                border: 1px solid palette(mid);
                background-color: palette(button);
                color: palette(text);
                font-size: 11pt; /* Slightly smaller font */
            }}
            QPushButton:hover {{
                background-color: palette(midlight);
                border: 1px solid palette(dark);
            }}
            QPushButton:disabled {{
                background-color: palette(window);
                color: palette(disabled-text);
                border: 1px solid palette(mid);
            }}

            /* PRIMARY BUTTON (GENERATE) */
            QPushButton#Primary {{
                padding: 6px 12px;
                border-radius: 5px;
                border: 1px solid palette(mid);
                background-color: palette(button);
                color: palette(text);
                font-size: 11pt; /* Slightly smaller font */
                min-width: 75px;
                max-width: 75px;
            }}
            QPushButton#Primary:hover {{
                border: 1px solid palette(text);
                background-color: palette(highlight);
            }}
            QPushButton#Primary:disabled {{
                background-color: palette(mid);
                color: palette(disabled-text);
                border: 1px solid palette(mid);
            }}

            QCheckBox {{ spacing: 8px; }}

            /* STATUS BAR */
            QStatusBar {{
                background: palette(window);
                border-top: 1px solid palette(mid);
                min-height: 50px;
                max-height: 50px;
            }}
            QStatusBar::item {{ border: none; }}

            QProgressBar {{
                border: 1px solid palette(mid);
                border-radius: 4px;
                text-align: center;
                color: palette(text);
                background: palette(base);
            }}
            QProgressBar::chunk {{
                background-color: palette(highlight);
            }}

            /* TABS */
            QTabWidget::pane {{
                border: 1px solid palette(mid);
                border-radius: 4px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: palette(button);
                border: 1px solid palette(mid);
                border-bottom-color: palette(mid);
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 6px 12px;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background: palette(base);
                border-bottom-color: palette(base);
                font-weight: bold;
            }}
        """)
