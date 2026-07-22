"""
memory_management.py
First Fit, Best Fit, Worst Fit with animated block-by-block allocation.
"""

import random

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QHeaderView,
    QFrame, QMessageBox, QScrollArea,
)
from PyQt5.QtCore import Qt, QTimer
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
    "free":    "#2E3347",
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
        font-size: 12px; font-weight: 700;
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


# ── Algorithms ──────────────────────────────────────────────────────────────

def first_fit(blocks, processes):
    alloc, remaining = [None] * len(processes), list(blocks)
    for i, ps in enumerate(processes):
        for j, bs in enumerate(remaining):
            if bs >= ps:
                alloc[i] = j; remaining[j] -= ps; break
    return alloc, remaining

def best_fit(blocks, processes):
    alloc, remaining = [None] * len(processes), list(blocks)
    for i, ps in enumerate(processes):
        best_j, best_w = None, float("inf")
        for j, bs in enumerate(remaining):
            w = bs - ps
            if 0 <= w < best_w: best_w = w; best_j = j
        if best_j is not None:
            alloc[i] = best_j; remaining[best_j] -= ps
    return alloc, remaining

def worst_fit(blocks, processes):
    alloc, remaining = [None] * len(processes), list(blocks)
    for i, ps in enumerate(processes):
        worst_j, worst_s = None, -1
        for j, bs in enumerate(remaining):
            if bs >= ps and bs > worst_s: worst_s = bs; worst_j = j
        if worst_j is not None:
            alloc[i] = worst_j; remaining[worst_j] -= ps
    return alloc, remaining


# ── Animated canvas ─────────────────────────────────────────────────────────

class MemoryCanvas(FigureCanvas):
    """Redraws the memory block chart, revealing processes one by one."""

    def __init__(self, block_labels, block_sizes, proc_labels, proc_sizes,
                 alloc, final_rem, algo_name):
        self.block_labels = block_labels
        self.block_sizes  = block_sizes
        self.proc_labels  = proc_labels
        self.proc_sizes   = proc_sizes
        self.alloc        = alloc
        self.final_rem    = final_rem
        self.algo_name    = algo_name
        self.n_revealed   = 0          # how many processes have been drawn

        n = len(block_sizes)
        fig_w = max(10, n * 2.2)
        
        n_total_patches = len(proc_labels) + 1
        ncol = min(n_total_patches, 5)
        max_legend_rows = -(-n_total_patches // ncol)
        
        bottom_margin_inches = 0.2 + (0.35 * max_legend_rows)
        fig_h = 5.0 + 0.6 + bottom_margin_inches
        
        self.rect_bottom = bottom_margin_inches / fig_h
        self.rect_top = (bottom_margin_inches + 5.0) / fig_h

        self.fig, self.axes = plt.subplots(1, n, figsize=(fig_w, fig_h))
        if n == 1:
            self.axes = [self.axes]
        self.fig.patch.set_facecolor(PALETTE["surface"])

        super().__init__(self.fig)
        self.setStyleSheet(f"background: {PALETTE['surface']};")
        self.setMinimumHeight(int(fig_h * 100))
        self.setMinimumWidth(int(fig_w * 100))
        self._render()

    def reveal_next(self):
        """Called by QTimer to add one more process to the chart."""
        if self.n_revealed < len(self.proc_labels):
            self.n_revealed += 1
            self._render()
            return True
        return False

    def _render(self):
        n = len(self.block_sizes)

        # block -> processes revealed so far
        b2p = {j: [] for j in range(n)}
        for i in range(self.n_revealed):
            j = self.alloc[i]
            if j is not None:
                b2p[j].append(i)

        for j, ax in enumerate(self.axes):
            ax.clear()
            ax.set_facecolor(PALETTE["bg"])
            total  = self.block_sizes[j]
            bottom = 0

            for i in b2p[j]:
                h     = self.proc_sizes[i]
                color = PROCESS_COLORS[i % len(PROCESS_COLORS)]
                ax.bar(0, h, bottom=bottom, width=0.72,
                       color=color, edgecolor=PALETTE["bg"], linewidth=2)
                # Label density scales with the segment's share of the block —
                # forcing a readable font on a sliver-thin segment is what was
                # causing neighboring labels to overlap, so segments too thin
                # for a full two-line label fall back to a shorter one, and
                # segments too thin for that get no in-bar label at all (they
                # still appear in the legend and results table below).
                frac = h / total
                if frac >= 0.05:
                    fs = max(8, min(14, int(frac * 80)))
                    label = f"{self.proc_labels[i]}\n{h} KB"
                elif frac >= 0.02:
                    fs = 8
                    label = self.proc_labels[i]
                else:
                    label = None
                if label:
                    ax.text(0, bottom + h / 2, label,
                            ha="center", va="center",
                            color="white", fontsize=fs, fontweight="bold",
                            clip_on=True)
                bottom += h

            # remaining free space — always shown as a block, label only if it fits
            # compute current free = total - allocated so far in this block
            used_so_far = sum(self.proc_sizes[i] for i in b2p[j])
            free_so_far = total - used_so_far
            if free_so_far > 0:
                ax.bar(0, free_so_far, bottom=bottom, width=0.72,
                       color=PALETTE["free"],
                       edgecolor=PALETTE["border"], linewidth=1.5,
                       linestyle="--")
                frac = free_so_far / total
                if frac >= 0.05:
                    fs = max(8, min(14, int(frac * 80)))
                    free_label = f"Free\n{free_so_far} KB"
                elif frac >= 0.02:
                    fs = 8
                    free_label = "Free"
                else:
                    free_label = None
                if free_label:
                    ax.text(0, bottom + free_so_far / 2, free_label,
                            ha="center", va="center",
                            color=PALETTE["muted"], fontsize=fs,
                            clip_on=True)

            ax.set_xlim(-0.6, 0.6)
            ax.set_ylim(0, total * 1.06)
            ax.set_xticks([])
            ax.set_yticks([0, total])
            ax.yaxis.set_tick_params(labelsize=9, labelcolor=PALETTE["muted"])
            ax.set_title(f"{self.block_labels[j]}\n{total} KB",
                         color=PALETTE["text"], fontsize=11,
                         pad=8, fontweight="bold")
            for spine in ax.spines.values():
                spine.set_edgecolor(PALETTE["border"])
                spine.set_linewidth(1.2)

        # Legend
        patches = [
            mpatches.Patch(
                color=PROCESS_COLORS[i % len(PROCESS_COLORS)],
                label=f"{self.proc_labels[i]} ({self.proc_sizes[i]} KB)"
            )
            for i in range(self.n_revealed)
        ]
        patches.append(mpatches.Patch(color=PALETTE["free"], label="Free space"))

        ncol = min(len(patches), 5)
        n_legend_rows = -(-len(patches) // ncol)  # ceil division

        # Remove the previous legend before drawing a new one. _render() runs
        # once per animation tick (once per process reveal), and Figure.legend()
        # does not replace an existing legend — it stacks a new artist on top
        # each time, which is what was producing the overlapping/doubled
        # legend text.
        if getattr(self, "_legend_artist", None) is not None:
            self._legend_artist.remove()

        self._legend_artist = self.fig.legend(
            handles=patches,
            loc="lower center", ncol=ncol,
            framealpha=0.4, facecolor=PALETTE["bg"],
            edgecolor=PALETTE["border"], labelcolor=PALETTE["text"],
            fontsize=10, bbox_to_anchor=(0.5, 0.01),
        )

        n_allocated = sum(1 for j in self.alloc[:self.n_revealed] if j is not None)
        n_total     = self.n_revealed
        status = (f"Allocating…  {n_allocated}/{n_total} placed"
                  if self.n_revealed < len(self.proc_labels)
                  else f"Done  ·  {n_allocated}/{len(self.proc_labels)} allocated")

        self.fig.suptitle(
            f"Memory Layout  —  {self.algo_name}    [{status}]",
            color=PALETTE["text"], fontsize=13, fontweight="bold", y=0.99,
        )

        # Ensure the axes maintain exactly 5.0 inches of vertical space regardless
        # of how many legend rows are generated, preventing blocks from squishing.
        self.fig.tight_layout(pad=1.4, rect=[0, self.rect_bottom, 1, self.rect_top])
        self.draw()


# ── Main widget ─────────────────────────────────────────────────────────────

class MemoryManagementWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._timer   = None
        self._canvas  = None
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background: {PALETTE['bg']}; color: {PALETTE['text']};")
        root = QVBoxLayout(self)
        root.setSpacing(18)
        root.setContentsMargins(24, 24, 24, 24)

        hdr = QLabel("Memory Management Simulator")
        hdr.setFont(QFont("Segoe UI", 20, QFont.Bold))
        hdr.setStyleSheet(f"color: {PALETTE['accent']};")
        root.addWidget(hdr)

        # ── Algo + controls
        ctrl = QHBoxLayout()
        ctrl.setSpacing(14)

        algo_lbl = QLabel("Algorithm:")
        algo_lbl.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 14px;")
        self.algo_box = QComboBox()
        self.algo_box.addItems(["First Fit", "Best Fit", "Worst Fit"])
        self.algo_box.setStyleSheet(f"""
            QComboBox {{
                background: {PALETTE['surface']}; color: {PALETTE['text']};
                border: 1px solid {PALETTE['border']}; border-radius: 6px;
                padding: 8px 14px; font-size: 14px; min-width: 170px;
            }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background: {PALETTE['surface']}; color: {PALETTE['text']};
                selection-background-color: {PALETTE['accent']}; font-size: 14px;
            }}
        """)

        self.run_btn   = _btn("▶  Allocate")
        self.reset_btn = _btn("↺  Reset", PALETTE["red"])
        self.run_btn.clicked.connect(self._run)
        self.reset_btn.clicked.connect(self._reset)

        for w in [algo_lbl, self.algo_box]:
            ctrl.addWidget(w)
        ctrl.addStretch()
        for b in [self.run_btn, self.reset_btn]:
            ctrl.addWidget(b)
        root.addLayout(ctrl)

        # ── Input tables
        tables_row = QHBoxLayout()
        tables_row.setSpacing(20)

        blk_col = QVBoxLayout(); blk_col.setSpacing(8)
        blk_hdr = QLabel("Memory Blocks")
        blk_hdr.setFont(QFont("Segoe UI", 14, QFont.Bold))
        blk_hdr.setStyleSheet(f"color: {PALETTE['green']};")
        blk_col.addWidget(blk_hdr)
        self.block_table = self._make_table(["Block", "Size (KB)"])
        blk_col.addWidget(self.block_table)
        add_blk = _btn("+ Block", PALETTE["green"])
        add_blk.clicked.connect(lambda: self._add_row(self.block_table, "B"))
        blk_col.addWidget(add_blk)
        tables_row.addLayout(blk_col)

        proc_col = QVBoxLayout(); proc_col.setSpacing(8)
        proc_hdr = QLabel("Processes")
        proc_hdr.setFont(QFont("Segoe UI", 14, QFont.Bold))
        proc_hdr.setStyleSheet(f"color: {PALETTE['yellow']};")
        proc_col.addWidget(proc_hdr)
        self.proc_table = self._make_table(["Process", "Size (KB)"])
        proc_col.addWidget(self.proc_table)
        add_proc = _btn("+ Process", PALETTE["yellow"])
        add_proc.clicked.connect(lambda: self._add_row(self.proc_table, "P"))
        proc_col.addWidget(add_proc)
        tables_row.addLayout(proc_col)

        root.addLayout(tables_row)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background: {PALETTE['border']}; max-height: 1px;")
        root.addWidget(div)

        # ── Status label
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(f"color: {PALETTE['green']}; font-size: 13px; font-weight: 700;")
        root.addWidget(self.status_lbl)

        self.output_area = QVBoxLayout()
        self.output_area.setSpacing(16)
        self._show_placeholder()
        root.addLayout(self.output_area)

        self._reset()

    def _make_table(self, headers):
        tbl = QTableWidget(0, 2)
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.verticalHeader().setDefaultSectionSize(40)
        tbl.setStyleSheet(TABLE_STYLE)
        tbl.setMinimumHeight(140)
        tbl.setMaximumHeight(210)
        return tbl

    def _add_row(self, tbl, prefix):
        row = tbl.rowCount()
        tbl.insertRow(row)
        # Blocks and processes get different, appropriately-scaled ranges —
        # blocks larger and in round 50 KB steps, processes smaller and in
        # round 10 KB steps — so a freshly added row still looks like a
        # plausible memory size instead of an arbitrary number.
        if prefix == "B":
            size = random.randint(2, 16) * 50   # 100–800 KB
        else:
            size = random.randint(4, 45) * 10   # 40–450 KB
        for col, val in enumerate([f"{prefix}{row+1}", str(size)]):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignCenter)
            item.setFont(QFont("Segoe UI", 13))
            if col == 0:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            tbl.setItem(row, col, item)

    def _reset(self):
        if self._timer:
            self._timer.stop()
        self.block_table.setRowCount(0)
        self.proc_table.setRowCount(0)
        for size in [100, 500, 200, 300, 600]:
            r = self.block_table.rowCount()
            self.block_table.insertRow(r)
            for col, val in enumerate([f"B{r+1}", str(size)]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Segoe UI", 13))
                if col == 0:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.block_table.setItem(r, col, item)
        for size in [212, 417, 112, 426]:
            r = self.proc_table.rowCount()
            self.proc_table.insertRow(r)
            for col, val in enumerate([f"P{r+1}", str(size)]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont("Segoe UI", 13))
                if col == 0:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.proc_table.setItem(r, col, item)
        self._clear_output()
        self.status_lbl.setText("")
        self._show_placeholder()

    def _show_placeholder(self):
        lbl = QLabel("Allocate memory to see the animated block visualization.")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color: {PALETTE['muted']}; font-size: 15px; padding: 48px;")
        self.output_area.addWidget(lbl)

    def _clear_output(self):
        if self._timer:
            self._timer.stop()
        while self.output_area.count():
            item = self.output_area.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._canvas = None

    def _read_table(self, tbl):
        data = []
        for row in range(tbl.rowCount()):
            try:
                label = tbl.item(row, 0).text()
                size  = int(tbl.item(row, 1).text())
                if size <= 0:
                    raise ValueError("Size must be > 0")
                data.append((label, size))
            except Exception as e:
                QMessageBox.warning(self, "Input Error", f"Row {row+1}: {e}")
                return None
        return data

    # ── Run + animation ─────────────────────────────────────────────────────

    def _run(self):
        bd = self._read_table(self.block_table)
        pd = self._read_table(self.proc_table)
        if bd is None or pd is None:
            return

        blabels, bsizes = [x[0] for x in bd], [x[1] for x in bd]
        plabels, psizes = [x[0] for x in pd], [x[1] for x in pd]

        algo = self.algo_box.currentText()
        if   algo == "First Fit": alloc, rem = first_fit(bsizes, psizes)
        elif algo == "Best Fit":  alloc, rem = best_fit(bsizes, psizes)
        else:                     alloc, rem = worst_fit(bsizes, psizes)

        self._clear_output()

        # Build canvas starting with 0 processes revealed
        self._canvas = MemoryCanvas(blabels, bsizes, plabels, psizes,
                                    alloc, rem, algo)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background: {PALETTE['bg']}; border: none;")
        scroll.setWidget(self._canvas)
        scroll.setMinimumHeight(self._canvas.minimumHeight() + 20)
        self.output_area.addWidget(scroll)

        # Results table below (shown immediately)
        self._draw_results_table(blabels, bsizes, plabels, psizes, alloc, rem)

        # Animate: reveal one process every 600 ms
        self.status_lbl.setText("⏳  Allocating processes…")
        self.run_btn.setEnabled(False)

        self._timer = QTimer(self)
        self._timer.setInterval(650)
        self._timer.timeout.connect(lambda: self._tick())
        self._timer.start()

    def _tick(self):
        more = self._canvas.reveal_next()
        if not more:
            self._timer.stop()
            self.status_lbl.setText("✅  Allocation complete.")
            self.run_btn.setEnabled(True)

    def _draw_results_table(self, blabels, bsizes, plabels, psizes, alloc, rem):
        lbl = QLabel("Allocation Results")
        lbl.setFont(QFont("Segoe UI", 15, QFont.Bold))
        lbl.setStyleSheet(f"color: {PALETTE['text']};")
        self.output_area.addWidget(lbl)

        tbl = QTableWidget(len(plabels), 4)
        tbl.setHorizontalHeaderLabels(
            ["Process", "Size (KB)", "Allocated Block", "Fragmentation (KB)"]
        )
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.horizontalHeader().setMinimumSectionSize(160)
        tbl.verticalHeader().setVisible(False)
        tbl.verticalHeader().setDefaultSectionSize(44)
        tbl.setStyleSheet(TABLE_STYLE)

        for i, (pl, ps) in enumerate(zip(plabels, psizes)):
            j          = alloc[i]
            block_name = blabels[j] if j is not None else "Not Allocated"
            frag       = str(rem[j]) if j is not None else "—"
            for col, val in enumerate([pl, str(ps), block_name, frag]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setFont(QFont("Segoe UI", 13))
                if col == 0:
                    item.setForeground(QColor(PROCESS_COLORS[i % len(PROCESS_COLORS)]))
                    item.setFont(QFont("Segoe UI", 13, QFont.Bold))
                elif col == 2:
                    color = PALETTE["green"] if j is not None else PALETTE["red"]
                    item.setForeground(QColor(color))
                    item.setFont(QFont("Segoe UI", 13, QFont.Bold))
                elif col == 3 and j is not None:
                    item.setForeground(QColor(PALETTE["yellow"]))
                tbl.setItem(i, col, item)

        tbl.setFixedHeight(len(plabels) * 44 + 46)
        self.output_area.addWidget(tbl)
