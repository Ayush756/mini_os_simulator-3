"""
comparison.py
Run all 4 CPU scheduling algorithms on the same process set.
Shows: 4 stacked Gantt charts + avg waiting time bar chart.
"""

import random

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QMessageBox,
)
# pyrefly: ignore [missing-import]
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

import matplotlib
matplotlib.use("Agg")
# pyrefly: ignore [missing-import]
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from cpu_scheduling import (
    run_fcfs, run_sjf, run_priority, run_rr, compute_metrics,
    PALETTE, PROCESS_COLORS, TABLE_STYLE, _btn,
)

ALGOS = [
    ("FCFS",               lambda p, q: run_fcfs(p)),
    ("SJF",                lambda p, q: run_sjf(p)),
    ("Priority",           lambda p, q: run_priority(p)),
    ("Round Robin",        lambda p, q: run_rr(p, q)),
]

ALGO_COLORS = ["#6C63FF", "#4ECDC4", "#FF6B6B", "#FFE66D"]


class ComparisonWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.pid_counter = 1
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background: {PALETTE['bg']}; color: {PALETTE['text']};")
        root = QVBoxLayout(self)
        root.setSpacing(18)
        root.setContentsMargins(24, 24, 24, 24)

        hdr = QLabel("Algorithm Comparison")
        hdr.setFont(QFont("Segoe UI", 20, QFont.Bold))
        hdr.setStyleSheet(f"color: {PALETTE['accent']};")
        root.addWidget(hdr)

        sub = QLabel("Same process set · All 4 algorithms · Side-by-side results")
        sub.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 13px;")
        root.addWidget(sub)

        # ── Quantum row
        q_row = QHBoxLayout()
        q_lbl = QLabel("Round Robin Quantum:")
        q_lbl.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 14px;")
        from PyQt5.QtWidgets import QSpinBox
        self.quantum = QSpinBox()
        self.quantum.setRange(1, 20)
        self.quantum.setValue(2)
        self.quantum.setStyleSheet(f"""
            QSpinBox {{
                background: {PALETTE['surface']}; color: {PALETTE['text']};
                border: 1px solid {PALETTE['border']}; border-radius: 6px;
                padding: 7px 10px; font-size: 14px; min-width: 70px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{ width: 18px; }}
        """)

        run_btn   = _btn("▶  Compare All")
        clear_btn = _btn("✕  Clear", PALETTE["red"])
        run_btn.clicked.connect(self._run)
        clear_btn.clicked.connect(self._clear)
        add_btn = _btn("+ Process", PALETTE["green"])
        add_btn.clicked.connect(self._add_row)

        for w in [q_lbl, self.quantum]:
            q_row.addWidget(w)
        q_row.addStretch()
        for b in [add_btn, run_btn, clear_btn]:
            q_row.addWidget(b)
        root.addLayout(q_row)

        # ── Process input table
        self.proc_table = QTableWidget(0, 4)
        self.proc_table.setHorizontalHeaderLabels(["PID", "Arrival Time", "Burst Time", "Priority"])
        self.proc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.proc_table.verticalHeader().setVisible(False)
        self.proc_table.verticalHeader().setDefaultSectionSize(40)
        self.proc_table.setStyleSheet(TABLE_STYLE)
        self.proc_table.setMinimumHeight(160)
        self.proc_table.setMaximumHeight(200)
        root.addWidget(self.proc_table)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background: {PALETTE['border']}; max-height: 1px;")
        root.addWidget(div)

        self.output_area = QVBoxLayout()
        self.output_area.setSpacing(14)
        self._show_placeholder()
        root.addLayout(self.output_area)

        self._load_defaults()

    # ── Helpers ─────────────────────────────────────────────────────────

    def _load_defaults(self):
        for pid, arr, burst, prio in [("P1",0,8,3),("P2",1,4,1),("P3",2,9,4),("P4",3,5,2)]:
            self._insert_row(pid, arr, burst, prio)
        self.pid_counter = 5

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

    def _add_row(self):
        arrivals = [
            int(self.proc_table.item(r, 1).text())
            for r in range(self.proc_table.rowCount())
            if self.proc_table.item(r, 1) is not None
        ]
        base = max(arrivals) if arrivals else 0
        arrival = base + random.randint(0, 4) if arrivals else random.randint(0, 6)
        burst   = random.randint(2, 12)
        priority = random.randint(1, 5)
        self._insert_row(f"P{self.pid_counter}", arrival, burst, priority)
        self.pid_counter += 1

    def _clear(self):
        self.proc_table.setRowCount(0)
        self.pid_counter = 1
        self._clear_output()
        self._show_placeholder()

    def _show_placeholder(self):
        lbl = QLabel("Add processes and click Compare All to see results.")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 15px; padding: 48px;")
        self.output_area.addWidget(lbl)

    def _clear_output(self):
        while self.output_area.count():
            item = self.output_area.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _read_processes(self):
        processes = []
        for row in range(self.proc_table.rowCount()):
            try:
                pid     = self.proc_table.item(row, 0).text()
                arrival = int(self.proc_table.item(row, 1).text())
                burst   = int(self.proc_table.item(row, 2).text())
                priority = int(self.proc_table.item(row, 3).text())
                if burst <= 0:
                    raise ValueError("Burst must be > 0")
                processes.append({"pid": pid, "arrival": arrival,
                                   "burst": burst, "priority": priority})
            except (AttributeError, ValueError) as e:
                QMessageBox.warning(self, "Input Error", f"Row {row+1}: {e}")
                return None
        if not processes:
            QMessageBox.warning(self, "Input Error", "Add at least one process.")
            return None
        return processes

    # ── Run ─────────────────────────────────────────────────────────────

    def _run(self):
        processes = self._read_processes()
        if not processes:
            return

        q = self.quantum.value()
        results = []
        for name, fn in ALGOS:
            display_name = f"Round Robin (q={q})" if name == "Round Robin" else name
            tl = fn(processes, q)
            m  = compute_metrics(processes, tl)
            avg_wt  = sum(x["wt"]  for x in m) / len(m)
            avg_tat = sum(x["tat"] for x in m) / len(m)
            results.append({"name": display_name, "timeline": tl, "metrics": m,
                             "avg_wt": avg_wt, "avg_tat": avg_tat})

        self._clear_output()
        self._draw_gantt_grid(results, processes)
        self._draw_bar_chart(results)
        self._draw_summary_table(results)

    # ── 4 Gantt charts stacked ───────────────────────────────────────────

    def _draw_gantt_grid(self, results, processes):
        color_map = {
            p["pid"]: PROCESS_COLORS[i % len(PROCESS_COLORS)]
            for i, p in enumerate(processes)
        }

        fig, axes = plt.subplots(4, 1, figsize=(11, 7.5))
        fig.patch.set_facecolor(PALETTE["surface"])

        global_max = max(
            seg["end"] for r in results for seg in r["timeline"]
        )

        for ax, result, algo_color in zip(axes, results, ALGO_COLORS):
            ax.set_facecolor(PALETTE["bg"])
            tl = result["timeline"]

            for seg in tl:
                w = seg["end"] - seg["start"]
                ax.barh(0, w, left=seg["start"], height=0.62,
                        color=color_map[seg["pid"]],
                        edgecolor=PALETTE["bg"], linewidth=1.8)
                if w >= 1:
                    ax.text(seg["start"] + w / 2, 0, seg["pid"],
                            ha="center", va="center",
                            color="white", fontsize=9, fontweight="bold")

            all_times = sorted(set(
                [s["start"] for s in tl] + [s["end"] for s in tl]
            ))
            for t in all_times:
                ax.axvline(x=t, color=PALETTE["bg"], linewidth=1.2, zorder=2)

            ax.set_xlim(-0.2, global_max + 0.5)
            ax.set_ylim(-0.6, 0.6)
            ax.set_yticks([])
            ax.set_xticks(all_times)
            ax.tick_params(axis="x", colors=PALETTE["muted"], labelsize=8, length=4)

            # Algorithm label on left with its accent color
            ax.set_ylabel(result["name"], color=algo_color,
                          fontsize=10, fontweight="bold",
                          rotation=0, labelpad=8, va="center")
            ax.yaxis.set_label_position("left")

            # Avg WT badge on right
            ax.text(1.002, 0.5, f"Avg WT: {result['avg_wt']:.1f}",
                    transform=ax.transAxes,
                    color=PALETTE["yellow"], fontsize=9, fontweight="bold",
                    va="center", ha="left")

            for spine in ax.spines.values():
                spine.set_edgecolor(PALETTE["border"])
                spine.set_linewidth(1)

        # Shared legend
        patches = [mpatches.Patch(color=color_map[p["pid"]], label=p["pid"])
                   for p in processes]
        fig.legend(handles=patches, loc="upper center", ncol=len(processes),
                   framealpha=0.4, facecolor=PALETTE["bg"],
                   edgecolor=PALETTE["border"], labelcolor=PALETTE["text"],
                   fontsize=10, bbox_to_anchor=(0.5, 0.94))

        fig.suptitle("Gantt Charts — All Algorithms",
                     color=PALETTE["text"], fontsize=14, fontweight="bold", y=0.99)
        fig.tight_layout(pad=0.8, h_pad=0.6, rect=[0, 0, 1, 0.88])

        canvas = FigureCanvas(fig)
        canvas.setStyleSheet(f"background: {PALETTE['surface']}; border-radius: 8px;")
        canvas.setMinimumHeight(480)
        self.output_area.addWidget(canvas)
        plt.close(fig)

    # ── Avg WT bar chart ─────────────────────────────────────────────────

    def _draw_bar_chart(self, results):
        fig, ax = plt.subplots(figsize=(11, 3.0))
        fig.patch.set_facecolor(PALETTE["surface"])
        ax.set_facecolor(PALETTE["bg"])

        names   = [r["name"] for r in results]
        wt_vals = [r["avg_wt"]  for r in results]
        tat_vals= [r["avg_tat"] for r in results]

        x = range(len(names))
        w = 0.36

        bars_wt  = ax.bar([i - w/2 for i in x], wt_vals,  width=w,
                           color=PALETTE["yellow"], label="Avg Waiting Time",
                           edgecolor=PALETTE["bg"], linewidth=1.5)
        bars_tat = ax.bar([i + w/2 for i in x], tat_vals, width=w,
                           color=PALETTE["accent"], label="Avg Turnaround Time",
                           edgecolor=PALETTE["bg"], linewidth=1.5)

        # Value labels on top
        for bar in list(bars_wt) + list(bars_tat):
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.3,
                    f"{h:.1f}", ha="center", va="bottom",
                    color=PALETTE["text"], fontsize=10, fontweight="bold")

        # Highlight the best (lowest) WT
        min_idx = wt_vals.index(min(wt_vals))
        bars_wt[min_idx].set_edgecolor(PALETTE["green"])
        bars_wt[min_idx].set_linewidth(3)
        ax.text(min_idx - w/2, wt_vals[min_idx] + 1.2, "★ Best",
                ha="center", color=PALETTE["green"], fontsize=9, fontweight="bold")

        ax.set_xticks(list(x))
        ax.set_xticklabels(names, color=PALETTE["text"], fontsize=12)
        ax.tick_params(axis="y", colors=PALETTE["muted"], labelsize=10)
        ax.set_ylabel("Time units", color=PALETTE["muted"], fontsize=11)
        ax.set_title("Avg Waiting & Turnaround Time Comparison",
                     color=PALETTE["text"], fontsize=13, fontweight="bold", pad=10)
        ax.legend(framealpha=0.4, facecolor=PALETTE["bg"],
                  edgecolor=PALETTE["border"], labelcolor=PALETTE["text"], fontsize=10)

        ax.set_ylim(0, max(tat_vals) * 1.28)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for spine in ax.spines.values():
            spine.set_edgecolor(PALETTE["border"])

        fig.tight_layout(pad=1.0)
        canvas = FigureCanvas(fig)
        canvas.setStyleSheet(f"background: {PALETTE['surface']}; border-radius: 8px;")
        canvas.setMinimumHeight(220)
        self.output_area.addWidget(canvas)
        plt.close(fig)

    # ── Summary table ────────────────────────────────────────────────────

    def _draw_summary_table(self, results):
        lbl = QLabel("Summary")
        lbl.setFont(QFont("Segoe UI", 15, QFont.Bold))
        lbl.setStyleSheet(f"color: {PALETTE['text']};")
        self.output_area.addWidget(lbl)

        tbl = QTableWidget(len(results), 3)
        tbl.setHorizontalHeaderLabels(["Algorithm", "Avg Waiting Time", "Avg Turnaround Time"])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.verticalHeader().setDefaultSectionSize(44)
        tbl.setStyleSheet(TABLE_STYLE)

        best_wt = min(r["avg_wt"] for r in results)
        for row, (r, ac) in enumerate(zip(results, ALGO_COLORS)):
            is_best = abs(r["avg_wt"] - best_wt) < 0.01
            for col, val in enumerate([r["name"], f"{r['avg_wt']:.2f}", f"{r['avg_tat']:.2f}"]):
                item = QTableWidgetItem(("★ " if is_best and col == 0 else "") + val)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setFont(QFont("Segoe UI", 13, QFont.Bold if is_best else QFont.Normal))
                if col == 0:
                    item.setForeground(QColor(PALETTE["green"] if is_best else ac))
                elif col == 1:
                    item.setForeground(QColor(PALETTE["green"] if is_best else PALETTE["yellow"]))
                else:
                    item.setForeground(QColor(PALETTE["muted"]))
                tbl.setItem(row, col, item)

        tbl.setFixedHeight(len(results) * 44 + 46)
        self.output_area.addWidget(tbl)
