from __future__ import annotations
from PySide6.QtWidgets import (QComboBox, QSpinBox, QDoubleSpinBox, QSlider, QWidget, QVBoxLayout,
                               QTextEdit, QPushButton, QHBoxLayout, QSizePolicy, QTabWidget)
from PySide6.QtGui import (QFontDatabase, QPainter, QPainterPath, QPen, QLinearGradient, QColor)
from PySide6.QtCore import Qt, QEvent

# --- Custom Widgets ---
class SafeComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

class SafeSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class SafeDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class SafeSlider(QSlider):
    def wheelEvent(self, event):
        event.ignore()

class SafeTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Install event filter to catch wheel events on the tab bar (headers)
        self.tabBar().installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.tabBar() and event.type() == QEvent.Wheel:
            # Ignore the event so it bubbles up to the parent (ScrollArea)
            event.ignore()
            # Return True to indicate we have filtered this event (preventing QTabBar from switching tabs)
            return True
        return super().eventFilter(obj, event)

    def wheelEvent(self, event):
        # Ignore wheel events on the content area too
        event.ignore()

# ---------------- Log Window ----------------
class LogWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logs")
        self.resize(700, 350)
        self.setFixedWidth(700)
        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFixedWidth(676)

        mono_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        mono_font.setPointSize(11)
        self.text_edit.setFont(mono_font)
        layout.addWidget(self.text_edit)

        row_btns = QHBoxLayout()
        btn_clear = QPushButton("Clear Logs")
        btn_clear.clicked.connect(self.text_edit.clear)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.hide)
        row_btns.addStretch()
        row_btns.addWidget(btn_clear)
        row_btns.addWidget(btn_close)
        layout.addLayout(row_btns)

    def append_text(self, text: str):
        self.text_edit.append(text)
        self.text_edit.verticalScrollBar().setValue(self.text_edit.verticalScrollBar().maximum())

    def clear(self):
        self.text_edit.clear()

    def get_text(self) -> str:
        return self.text_edit.toPlainText()

# ---------------- Density Visualizer ----------------
class DensityGraphWidget(QWidget):
    def __init__(self, density_data: list[dict], sections: list[dict], parent=None):
        super().__init__(parent)
        self._density = density_data
        self._sections = sections
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("background-color: #2b2b2b; border: 1px solid #3d3d3d; border-radius: 4px;")

    def set_sections(self, sections: list[dict]):
        self._sections = sections
        self.update() # Trigger repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Fill Background
        painter.fillRect(self.rect(), QColor(43, 43, 43))

        w = self.width()
        h = self.height()

        if not self._density:
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Density Data")
            return

        # Determine Scaling
        max_t = self._density[-1]['t']
        if max_t <= 0:
            max_t = 1.0

        max_nps = 0.0
        for d in self._density:
            if d['nps'] > max_nps:
                max_nps = d['nps']
        if max_nps < 5.0:
            max_nps = 5.0  # Minimum ceiling for visualization

        # Margins
        margin_b = 20
        plot_h = h - margin_b

        # 1. Draw Density Path
        path = QPainterPath()
        path.moveTo(0, plot_h) # Start bottom-left

        for d in self._density:
            x = (d['t'] / max_t) * w
            # nps relative to max, inverted Y
            ratio = d['nps'] / max_nps
            y = plot_h - (ratio * plot_h)
            path.lineTo(x, y)

        path.lineTo(w, plot_h) # Finish bottom-right
        path.closeSubpath()

        # Gradient Fill
        grad = QLinearGradient(0, 0, 0, plot_h)
        grad.setColorAt(0.0, QColor(0, 180, 255, 120))
        grad.setColorAt(1.0, QColor(0, 180, 255, 10))
        painter.fillPath(path, grad)

        # Line Stroke (Redraw line without closing loop)
        painter.setPen(QPen(QColor(0, 200, 255), 2))
        line_path = QPainterPath()
        first = True
        for d in self._density:
            x = (d['t'] / max_t) * w
            ratio = d['nps'] / max_nps
            y = plot_h - (ratio * plot_h)
            if first:
                line_path.moveTo(x, y)
                first = False
            else:
                line_path.lineTo(x, y)
        painter.drawPath(line_path)

        # 2. Draw Section Lines & Names
        painter.setPen(QPen(QColor(255, 255, 255, 120), 1, Qt.DashLine))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)

        for i, s in enumerate(self._sections):
            t = s.get('start', 0.0)
            if t > max_t:
                continue

            x = (t / max_t) * w
            painter.drawLine(int(x), 0, int(x), h)

            name = s.get('name', '')
            # Stagger text height to prevent overlap
            text_y = h - 6 if i % 2 == 0 else h - 18

            # Text shadow for readability
            painter.setPen(QColor(0,0,0, 180))
            painter.drawText(int(x) + 5, text_y + 1, name)

            painter.setPen(QColor(220, 220, 220))
            painter.drawText(int(x) + 4, text_y, name)

            # Reset pen for next line
            painter.setPen(QPen(QColor(255, 255, 255, 120), 1, Qt.DashLine))
