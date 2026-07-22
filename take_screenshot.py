import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap
from main import MainWindow
from PyQt5.QtCore import QTimer

app = QApplication(sys.argv)
w = MainWindow()
w.show()

def capture():
    # Switch to comparison tab
    w.findChild(QTabWidget).setCurrentIndex(1)
    # Run the comparison
    w.findChild(QTabWidget).currentWidget().widget()._run()
    
    # Take screenshot
    pixmap = w.grab()
    pixmap.save("screenshot_comparison.png")
    
    # Switch to CPU scheduling tab
    w.findChild(QTabWidget).setCurrentIndex(0)
    w.findChild(QTabWidget).currentWidget().widget()._run()
    pixmap = w.grab()
    pixmap.save("screenshot_cpu.png")
    
    app.quit()

QTimer.singleShot(1000, capture)
sys.exit(app.exec_())
