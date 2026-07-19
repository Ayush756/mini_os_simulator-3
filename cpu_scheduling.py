"""
cpu_scheduling.py
FCFS, SJF (non-preemptive), Priority (non-preemptive), Round Robin.
Outputs: Gantt chart + metrics table.
"""

import random

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
    QHeaderView, QFrame, QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

PALETTE = {
    "bg":      "#0F1117",
    "surface": "#1A1D27",
    "border":  "#2A2D3E",
    "accent":  "#6C63FF",
    "green":   "#4ECDC4",
    "red":     "#FF6B6B",
    "yellow":  "#FFE66D",
    "text":    "#E8E8F0",
    "muted":   "#6B7280",
}

PROCESS_COLORS = [
    "#6C63FF", "#4ECDC4", "#FF6B6B", "#FFE66D",
    "#A8E6CF", "#FF8B94", "#B8B5FF", "#FFC3A0",
]

TABLE_STYLE = f"""
    QTableWidget {{
        background: {PALETTE['surface']}; color: {PALETTE['text']};
        gridline-color: {PALETTE['border']};
        border: 1px solid {PALETTE['border']}; border-radius: 8px;
        font-size: 14px;
    }}
    QHeaderView::section {{
        background: {PALETTE['bg']}; color: {PALETTE['muted']};
        padding: 10px 8px; border: none;
        border-bottom: 1px solid {PALETTE['border']};
        font-size: 12px; font-weight: 700; letter-spacing: 0.5px;
    }}
    QTableWidget::item {{ padding: 6px; }}
    QTableWidget::item:selected {{ background: {PALETTE['accent']}44; }}
"""


def _btn(text, color=None):
    c = color or PALETTE["accent"]
    b = QPushButton(text)
    b.setStyleSheet(f"""
        QPushButton {{
            background: {c}; color: #fff; border: none;
            border-radius: 6px; padding: 9px 22px;
            font-size: 13px; font-weight: 700;
        }}
        QPushButton:hover   {{ background: {c}cc; }}
        QPushButton:pressed {{ background: {c}88; }}
    """)
    return b


# ── Algorithms ─────────────────────────────────────────────────────────────

def run_fcfs(processes):
    procs = sorted(processes, key=lambda p: (p["arrival"], p["pid"]))
    timeline, t = [], 0
    for p in procs:
        s = max(t, p["arrival"])
        e = s + p["burst"]
        timeline.append({"pid": p["pid"], "start": s, "end": e})
        t = e
    return timeline


def run_sjf(processes):
    remaining = [p.copy() for p in processes]
    timeline, t = [], 0
    while remaining:
        avail = [p for p in remaining if p["arrival"] <= t]
        if not avail:
            t = min(p["arrival"] for p in remaining)
            avail = [p for p in remaining if p["arrival"] <= t]
        chosen = min(avail, key=lambda p: (p["burst"], p["arrival"]))
        e = t + chosen["burst"]
        timeline.append({"pid": chosen["pid"], "start": t, "end": e})
        t = e
        remaining.remove(chosen)
    return timeline


def run_priority(processes):
    remaining = [p.copy() for p in processes]
    timeline, t = [], 0
    while remaining:
        avail = [p for p in remaining if p["arrival"] <= t]
        if not avail:
            t = min(p["arrival"] for p in remaining)
            avail = [p for p in remaining if p["arrival"] <= t]
        chosen = min(avail, key=lambda p: (p["priority"], p["arrival"]))
        e = t + chosen["burst"]
        timeline.append({"pid": chosen["pid"], "start": t, "end": e})
        t = e
        remaining.remove(chosen)
    return timeline


def run_rr(processes, quantum):
    from collections import deque
    procs = [p.copy() for p in processes]
    for p in procs:
        p["remaining"] = p["burst"]
    procs.sort(key=lambda p: p["arrival"])

    timeline, t = [], 0
    queue, enqueued = deque(), set()
    remaining = list(procs)

    def enqueue():
        for p in remaining:
            if p["arrival"] <= t and p["pid"] not in enqueued and p["remaining"] > 0:
                queue.append(p)
                enqueued.add(p["pid"])

    enqueue()
    if not queue and remaining:
        t = remaining[0]["arrival"]
        enqueue()

    while queue or remaining:
        if not queue:
            t = min(p["arrival"] for p in remaining if p["remaining"] > 0)
            enqueue()
        if not queue:
            break
        p = queue.popleft()
        run = min(quantum, p["remaining"])
        timeline.append({"pid": p["pid"], "start": t, "end": t + run})
        t += run
        p["remaining"] -= run
        enqueue()
        if p["remaining"] > 0:
            queue.append(p)
        else:
            remaining = [r for r in remaining if r["pid"] != p["pid"]]
    return timeline


def compute_metrics(processes, timeline):
    result = []
    for p in processes:
        segs = [e for e in timeline if e["pid"] == p["pid"]]
        if not segs:
            continue
        ct  = segs[-1]["end"]
        tat = ct - p["arrival"]
        wt  = tat - p["burst"]
        result.append({"pid": p["pid"], "arrival": p["arrival"],
                        "burst": p["burst"], "ct": ct, "tat": tat, "wt": wt})
    return result


# ── Widget ──────────────────────────────────────────────────────────────────

class CPUSchedulingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.pid_counter = 1
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background: {PALETTE['bg']}; color: {PALETTE['text']};")
        root = QVBoxLayout(self)
        root.setSpacing(18)
        root.setContentsMargins(24, 24, 24, 24)

        # ── Header
        hdr = QLabel("CPU Scheduling Simulator")
        hdr.setFont(QFont("Segoe UI", 20, QFont.Bold))
        hdr.setStyleSheet(f"color: {PALETTE['accent']};")
        root.addWidget(hdr)

        # ── Controls row
        ctrl = QHBoxLayout()
        ctrl.setSpacing(14)

        algo_lbl = QLabel("Algorithm:")
        algo_lbl.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 14px;")

        self.algo_box = QComboBox()
        self.algo_box.addItems([
            "FCFS",
            "SJF (Non-Preemptive)",
            "Priority (Non-Preemptive)",
            "Round Robin",
        ])
        self.algo_box.setStyleSheet(f"""
            QComboBox {{
                background: {PALETTE['surface']}; color: {PALETTE['text']};
                border: 1px solid {PALETTE['border']}; border-radius: 6px;
                padding: 8px 14px; font-size: 14px; min-width: 220px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background: {PALETTE['surface']}; color: {PALETTE['text']};
                selection-background-color: {PALETTE['accent']};
                font-size: 14px;
            }}
        """)
        self.algo_box.currentIndexChanged.connect(self._on_algo_change)

        self.quantum_lbl = QLabel("Quantum:")
        self.quantum_lbl.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 14px;")

        self.quantum_spin = QSpinBox()
        self.quantum_spin.setRange(1, 20)
        self.quantum_spin.setValue(2)
        self.quantum_spin.setStyleSheet(f"""
            QSpinBox {{
                background: {PALETTE['surface']}; color: {PALETTE['text']};
                border: 1px solid {PALETTE['border']}; border-radius: 6px;
                padding: 8px 10px; font-size: 14px; min-width: 70px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{ width: 18px; }}
        """)

        add_btn   = _btn("+ Add Process", PALETTE["green"])
        run_btn   = _btn("▶  Run")
        clear_btn = _btn("✕ Clear", PALETTE["red"])

        add_btn.clicked.connect(self._add_row)
        run_btn.clicked.connect(self._run)
        clear_btn.clicked.connect(self._clear)

        for w in [algo_lbl, self.algo_box, self.quantum_lbl, self.quantum_spin]:
            ctrl.addWidget(w)
        ctrl.addStretch()
        for b in [add_btn, run_btn, clear_btn]:
            ctrl.addWidget(b)
        root.addLayout(ctrl)

        # ── Process input table
        self.proc_table = QTableWidget(0, 4)
        self.proc_table.setHorizontalHeaderLabels(
            ["PID", "Arrival Time", "Burst Time", "Priority"]
        )
        self.proc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.setStyleSheet(TABLE_STYLE)
        self.proc_table.verticalHeader().setDefaultSectionSize(40)
        self.proc_table.setMinimumHeight(160)
        self.proc_table.setMaximumHeight(220)
        root.addWidget(self.proc_table)

        # ── Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background: {PALETTE['border']}; max-height: 1px;")
        root.addWidget(div)

        # ── Output area
        self.output_area = QVBoxLayout()
        self.output_area.setSpacing(16)
        self._show_placeholder("Run an algorithm to see the Gantt chart and metrics.")
        root.addLayout(self.output_area)

        self._on_algo_change(0)
        self._load_defaults()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _on_algo_change(self, _):
        is_rr   = self.algo_box.currentText() == "Round Robin"
        is_prio = "Priority" in self.algo_box.currentText()
        self.quantum_lbl.setVisible(is_rr)
        self.quantum_spin.setVisible(is_rr)
        self.proc_table.setColumnHidden(3, not is_prio)

    def _load_defaults(self):
        for pid, arr, burst, prio in [
            ("P1", 0, 8, 3), ("P2", 1, 4, 1),
            ("P3", 2, 9, 4), ("P4", 3, 5, 2),
        ]:
            self._insert_row(pid, arr, burst, prio)
        self.pid_counter = 5

    def _add_row(self):
        # Keep arrival in the same neighborhood as the existing processes
        # instead of always dropping a new one at t=0 — a few units past
        # the latest arrival so far, or 0-6 if the table is still empty.
        arrivals = [
            int(self.proc_table.item(r, 1).text())
            for r in range(self.proc_table.rowCount())
            if self.proc_table.item(r, 1) is not None
        ]
        base = max(arrivals) if arrivals else 0
        arrival  = base + random.randint(0, 4) if arrivals else random.randint(0, 6)
        burst    = random.randint(2, 12)
        priority = random.randint(1, 5)
        self._insert_row(f"P{self.pid_counter}", arrival, burst, priority)
        self.pid_counter += 1

    def _insert_row(self, pid, arrival, burst, priority):
        row = self.proc_table.rowCount()
        self.proc_table.insertRow(row)

        pid_item = QTableWidgetItem(pid)
        pid_item.setFlags(pid_item.flags() & ~Qt.ItemIsEditable)
        pid_item.setTextAlignment(Qt.AlignCenter)
        pid_item.setForeground(QColor(PROCESS_COLORS[row % len(PROCESS_COLORS)]))
        pid_item.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.proc_table.setItem(row, 0, pid_item)

        for col, val in enumerate([arrival, burst, priority], start=1):
            item = QTableWidgetItem(str(val))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(QFont("Segoe UI", 13))
            self.proc_table.setItem(row, col, item)

    def _clear(self):
        self.proc_table.setRowCount(0)
        self.pid_counter = 1
        self._clear_output()
        self._show_placeholder("Run an algorithm to see the Gantt chart and metrics.")

    def _clear_output(self):
        while self.output_area.count():
            item = self.output_area.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_placeholder(self, text):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"color: {PALETTE['muted']}; font-size: 15px; padding: 48px;"
        )
        self.output_area.addWidget(lbl)

    def _read_processes(self):
        processes = []
        is_prio = "Priority" in self.algo_box.currentText()
        for row in range(self.proc_table.rowCount()):
            try:
                pid     = self.proc_table.item(row, 0).text()
                arrival = int(self.proc_table.item(row, 1).text())
                burst   = int(self.proc_table.item(row, 2).text())
                prio_item = self.proc_table.item(row, 3)
                priority = int(prio_item.text()) if is_prio and prio_item else 0
                if burst <= 0:
                    raise ValueError("Burst must be > 0")
                processes.append({
                    "pid": pid, "arrival": arrival,
                    "burst": burst, "priority": priority,
                })
            except (AttributeError, ValueError) as e:
                QMessageBox.warning(self, "Input Error", f"Row {row + 1}: {e}")
                return None
        if not processes:
            QMessageBox.warning(self, "Input Error", "Add at least one process.")
            return None
        return processes

    # ── Run ────────────────────────────────────────────────────────────────

    def _run(self):
        processes = self._read_processes()
        if not processes:
            return

        algo = self.algo_box.currentText()
        if   algo == "FCFS":                      tl = run_fcfs(processes)
        elif algo == "SJF (Non-Preemptive)":      tl = run_sjf(processes)
        elif algo == "Priority (Non-Preemptive)": tl = run_priority(processes)
        else:                                      tl = run_rr(processes, self.quantum_spin.value())

        metrics = compute_metrics(processes, tl)
        self._clear_output()
        self._draw_gantt(tl, processes)
        self._draw_metrics(metrics)

    # ── Gantt ──────────────────────────────────────────────────────────────

    def _draw_gantt(self, timeline, processes):
        color_map = {
            p["pid"]: PROCESS_COLORS[i % len(PROCESS_COLORS)]
            for i, p in enumerate(processes)
        }

        fig, ax = plt.subplots(figsize=(11, 3.2))
        fig.patch.set_facecolor(PALETTE["surface"])
        ax.set_facecolor(PALETTE["surface"])

        for seg in timeline:
            width = seg["end"] - seg["start"]
            ax.barh(
                0, width, left=seg["start"], height=0.72,
                color=color_map[seg["pid"]],
                edgecolor=PALETTE["bg"], linewidth=2,
            )
            if width >= 0.8:
                ax.text(
                    seg["start"] + width / 2, 0,
                    seg["pid"],
                    ha="center", va="center",
                    color="white", fontsize=11, fontweight="bold",
                )

        all_times = sorted(
            set([s["start"] for s in timeline] + [s["end"] for s in timeline])
        )
        for t in all_times:
            ax.axvline(x=t, color=PALETTE["bg"], linewidth=1.5, zorder=2)

        max_end = max(s["end"] for s in timeline)
        ax.set_xlim(-0.2, max_end + 0.4)
        ax.set_ylim(-0.65, 0.65)
        ax.set_yticks([])
        ax.set_xticks(all_times)
        ax.tick_params(axis="x", colors=PALETTE["text"], labelsize=11, length=5)
        ax.set_xlabel("Time units", color=PALETTE["muted"], fontsize=12, labelpad=8)
        ax.set_title(
            f"Gantt Chart  —  {self.algo_box.currentText()}",
            color=PALETTE["text"], fontsize=14, fontweight="bold", pad=12,
        )

        for spine in ax.spines.values():
            spine.set_edgecolor(PALETTE["border"])

        patches = [
            mpatches.Patch(color=color_map[p["pid"]], label=p["pid"])
            for p in processes
        ]
        # Figure-level legend placed outside the axes (to the right) so it
        # never sits on top of the chart itself — an axes-level legend with
        # loc="lower right" draws inside the plot bounds and was covering
        # the tail of the timeline.
        fig.legend(
            handles=patches, loc="center left", bbox_to_anchor=(1.0, 0.5),
            framealpha=0.5, facecolor=PALETTE["bg"],
            edgecolor=PALETTE["border"], labelcolor=PALETTE["text"],
            fontsize=11, handlelength=1.4,
        )

        fig.tight_layout(pad=1.2, rect=[0, 0, 0.90, 1])
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet(
            f"background: {PALETTE['surface']}; border-radius: 8px;"
        )
        canvas.setMinimumHeight(220)
        self.output_area.addWidget(canvas)
        plt.close(fig)

    # ── Metrics table ──────────────────────────────────────────────────────

    def _draw_metrics(self, metrics):
        lbl = QLabel("Performance Metrics")
        lbl.setFont(QFont("Segoe UI", 15, QFont.Bold))
        lbl.setStyleSheet(f"color: {PALETTE['text']};")
        self.output_area.addWidget(lbl)

        n_rows = len(metrics) + 1          # +1 for average row
        tbl = QTableWidget(n_rows, 6)
        tbl.setHorizontalHeaderLabels(
            ["PID", "Arrival", "Burst", "Completion", "Turnaround (TAT)", "Waiting (WT)"]
        )
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.verticalHeader().setDefaultSectionSize(44)
        tbl.setStyleSheet(TABLE_STYLE)

        avg_tat = avg_wt = 0
        for row, m in enumerate(metrics):
            avg_tat += m["tat"]
            avg_wt  += m["wt"]
            for col, val in enumerate(
                [m["pid"], m["arrival"], m["burst"], m["ct"], m["tat"], m["wt"]]
            ):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setFont(QFont("Segoe UI", 13))
                if col == 0:
                    item.setForeground(
                        QColor(PROCESS_COLORS[row % len(PROCESS_COLORS)])
                    )
                    item.setFont(QFont("Segoe UI", 13, QFont.Bold))
                elif col == 4:
                    item.setForeground(QColor(PALETTE["green"]))
                    item.setFont(QFont("Segoe UI", 13, QFont.Bold))
                elif col == 5:
                    item.setForeground(QColor(PALETTE["yellow"]))
                    item.setFont(QFont("Segoe UI", 13, QFont.Bold))
                tbl.setItem(row, col, item)

        n = len(metrics)
        for col, val in enumerate(
            ["Average", "—", "—", "—",
             f"{avg_tat / n:.2f}", f"{avg_wt / n:.2f}"]
        ):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setFont(QFont("Segoe UI", 13, QFont.Bold))
            item.setForeground(QColor(PALETTE["accent"]))
            tbl.setItem(n, col, item)

        tbl.setFixedHeight(n_rows * 44 + 46)
        self.output_area.addWidget(tbl)
