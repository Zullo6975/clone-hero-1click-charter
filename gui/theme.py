from __future__ import annotations
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtCore import Qt
from gui.utils import get_base_font_size

class ThemeManager:
    @staticmethod
    def apply_style(app: QApplication, dark_mode: bool):
        app.setStyle("Fusion")

        font = QFont()
        font.setPointSize(get_base_font_size())
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

        base_pt = get_base_font_size()
        grp_pt = base_pt - 1  # GroupBox titles slightly smaller

        # Stylesheet overrides
        app.setStyleSheet(f"""
            QWidget {{
                outline: none;
            }}

            /* --- GROUP BOXES (Compact Modern) --- */
            QGroupBox {{
                border: 1px solid {line_color};
                border-radius: 8px;
                margin-top: 1.2em; /* Reduced top margin */
                padding: 12px;     /* Reduced internal padding (was 15) */
                font-weight: bold;
                font-size: {grp_pt}pt;
                background-color: transparent;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: palette(highlight);
            }}

            /* --- INPUT FIELDS --- */
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QListWidget {{
                padding: 6px; /* Reduced from 8px */
                border-radius: 6px;
                border: 1px solid palette(mid);
                background-color: palette(base);
                color: palette(text);
                font-size: {base_pt}pt;
                selection-background-color: palette(highlight);
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
                border: 2px solid palette(highlight);
                padding: 5px;
            }}

            /* --- BUTTONS --- */
            QPushButton {{
                padding: 6px 16px; /* Reduced vertical padding */
                border-radius: 6px;
                border: 1px solid palette(mid);
                background-color: palette(button);
                color: palette(text);
                font-size: {base_pt}pt;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: palette(midlight);
                border-color: palette(dark);
            }}
            QPushButton:pressed {{
                background-color: palette(dark);
            }}

            /* PRIMARY BUTTON (GENERATE) */
            QPushButton#Primary {{
                background-color: palette(highlight);
                color: white;
                border: 1px solid palette(highlight);
                font-weight: bold;
                padding: 8px 24px;
            }}
            QPushButton#Primary:hover {{
                background-color: #3a86ff;
            }}

            /* --- SCROLL BARS (Fix Visibility) --- */
            QScrollBar:vertical {{
                border: none;
                background: {line_color}; /* Subtle background track */
                width: 12px; /* Slightly wider */
                margin: 0;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: palette(mid); /* Ensure this contrasts */
                min-height: 20px;
                border-radius: 6px;
                border: 2px solid transparent; /* Creates padding effect */
                background-clip: content-box;
            }}
            QScrollBar::handle:vertical:hover {{
                background: palette(text);
                border: 2px solid transparent;
                background-clip: content-box;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            /* --- TABS --- */
            QTabWidget::pane {{
                border: 1px solid palette(mid);
                border-radius: 6px;
                background: palette(base);
            }}
            QTabBar::tab {{
                background: transparent;
                padding: 6px 16px;
                margin-bottom: -1px;
                border-bottom: 2px solid transparent;
                color: palette(disabled-text);
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                color: palette(highlight);
                border-bottom: 2px solid palette(highlight);
            }}

            /* --- STATUS BAR --- */
            QStatusBar {{
                background: palette(window);
                border-top: 1px solid palette(mid);
            }}
            QProgressBar {{
                border: none;
                background-color: palette(mid);
                border-radius: 4px;
                height: 8px;
            }}
            QProgressBar::chunk {{
                background-color: palette(highlight);
                border-radius: 4px;
            }}
        """)
