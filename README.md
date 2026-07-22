# Mini OS Simulator

An educational, GUI-based desktop application that visualizes core Operating System algorithms.
We try to visualoze the cpu_scheduling , memory camparisons.

## Requirements

- Python 3.8+
- PyQt5
- matplotlib

## Installation

```bash
pip install PyQt5 matplotlib
```

## Running

```bash
python main.py
```

## Modules

| Module | Algorithms |
|--------|-----------|
| CPU Scheduling | FCFS, SJF (Non-Preemptive), Priority, Round Robin |
| Memory Management | First Fit, Best Fit, Worst Fit |
| File System | Create / Delete files & folders, directory tree |
| Disk Scheduling | FCFS, SSTF, SCAN (Left/Right), LOOK (Left/Right) |

## Project Structure

```
mini_os_simulator/
├── main.py               # Dashboard + tab container
├── cpu_scheduling.py     # CPU algorithms + Gantt chart
├── memory_management.py  # Memory allocation + block visualization
├── file_management.py    # In-memory file system explorer
├── disk_scheduling.py    # Disk head movement graph
└── README.md
```

## Extending the Project

Each module is self-contained. To add a new algorithm:
1. Implement the function in the relevant `*.py` file
2. Add the algorithm name to the `QComboBox` in that module's `_build_ui()`
3. Add the dispatch case in the `_run()` method

To add a new OS domain (e.g., Page Replacement / Banker's Algorithm):
1. Create a new `page_replacement.py` following the same widget pattern
2. Import and add it as a new tab in `main.py`'s `TAB_DEFS` list
