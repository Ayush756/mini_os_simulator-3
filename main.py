"""
main.py  —  Mini OS Simulator Dashboard
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QScrollArea,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette

from cpu_scheduling import CPUSchedulingWidget
from memory_management import MemoryManagementWidget
from comparison import ComparisonWidget

PALETTE = {
    "bg":      "#0F1117",
    "surface": "#1A1D27",
    "border":  "#2A2D3E",
    "accent":  "#6C63FF",
    "green":   "#4ECDC4",
    "yellow":  "#FFE66D",
    "text":    "#E8E8F0",
    "muted":   "#6B7280",
}

TAB_DEFS = [
    ("⚙️   CPU Scheduling",    CPUSchedulingWidget),
    ("📊  Comparison",          ComparisonWidget),
    ("🧠  Memory Management",   MemoryManagementWidget),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini OS Simulator")
        self.resize(1300, 880)
        self._apply_theme()
        self._build_ui()

    def _apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background: {PALETTE['bg']}; }}
            QScrollBar:vertical {{
                background: {PALETTE['surface']}; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {PALETTE['border']}; border-radius: 4px; min-height: 24px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar:horizontal {{
                background: {PALETTE['surface']}; height: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: {PALETTE['border']}; border-radius: 4px; min-width: 24px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        """)

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet(f"background: {PALETTE['bg']};")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        root.addWidget(self._make_header())

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none; background: {PALETTE['bg']};
            }}
            QTabBar::tab {{
                background: {PALETTE['surface']}; color: {PALETTE['muted']};
                padding: 14px 32px; font-size: 14px; font-weight: 600;
                border: none; border-bottom: 3px solid transparent; margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                color: {PALETTE['text']};
                border-bottom: 3px solid {PALETTE['accent']};
                background: {PALETTE['bg']};
            }}
            QTabBar::tab:hover:!selected {{
                color: {PALETTE['text']}; background: {PALETTE['border']};
            }}
        """)

        for tab_name, WidgetClass in TAB_DEFS:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet(f"background: {PALETTE['bg']}; border: none;")
            scroll.setWidget(WidgetClass())
            tabs.addTab(scroll, tab_name)

        root.addWidget(tabs)
        root.addWidget(self._make_footer())

    def _make_header(self):
        bar = QWidget()
        bar.setFixedHeight(68)
        bar.setStyleSheet(
            f"background: {PALETTE['surface']}; border-bottom: 1px solid {PALETTE['border']};"
        )
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(28, 0, 28, 0)

        logo = QLabel("🖥   Mini OS Simulator")
        logo.setFont(QFont("Segoe UI", 17, QFont.Bold))
        logo.setStyleSheet(f"color: {PALETTE['text']};")

        sub = QLabel("Educational OS Concepts Visualizer")
        sub.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 13px;")
        sub.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        lay.addWidget(logo)
        lay.addStretch()
        lay.addWidget(sub)
        return bar

    def _make_footer(self):
        bar = QWidget()
        bar.setFixedHeight(32)
        bar.setStyleSheet(
            f"background: {PALETTE['surface']}; border-top: 1px solid {PALETTE['border']};"
        )
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)

        for label, color in [
            ("● CPU Scheduling",  PALETTE["accent"]),
            ("● Comparison",      PALETTE["yellow"]),
            ("● Memory",          PALETTE["green"]),
        ]:
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {color}; font-size: 12px;")
            lay.addWidget(lbl)
            lay.addSpacing(20)

        lay.addStretch()
        lay.addWidget(QLabel("v1.2.0  |  Python + PyQt5"))
        return bar


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor(15, 17, 23))
    pal.setColor(QPalette.WindowText,      QColor(232, 232, 240))
    pal.setColor(QPalette.Base,            QColor(26, 29, 39))
    pal.setColor(QPalette.Text,            QColor(232, 232, 240))
    pal.setColor(QPalette.Button,          QColor(26, 29, 39))
    pal.setColor(QPalette.ButtonText,      QColor(232, 232, 240))
    pal.setColor(QPalette.Highlight,       QColor(108, 99, 255))
    pal.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(pal)

    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
