"""
A prototype for the main management window, which uses MDI to handle
nice looking transitions, tooltips, reference windows, etc.

Needs the following features:
tab control with window changes
hover-tooltips

"""

import sys

from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtWidgets import (QApplication, QMainWindow,
    QPushButton, QLabel, QMdiArea, QMdiSubWindow)
import qdarkstyle

class SubWindow(QMdiSubWindow):
    """A single pane on the mainwindow"""
    counter = 0

    def __init__(self, mdi_area):
        super().__init__()
        self.mdi_area = mdi_area
        SubWindow.counter += 1
        self.label = QLabel(f"subwindow {SubWindow.counter}", parent=self)
        self.setWidget(self.label)
        self.setWindowFlags(self.windowFlags() |
                            Qt.FramelessWindowHint)
        self.setFixedSize(MainWindow.resolution[0], MainWindow.resolution[1])
        self.mdi_area.addSubWindow(self)
        self.move(-MainWindow.resolution[0], 0)


class MdiArea(QMdiArea):
    """The manager for all of the primary windows"""
    def __init__(self):
        super().__init__()


class MainWindow(QMainWindow):
    """The main application window. Once a game is loaded, this
    instantiates UI elements on itself directly - use modal windows
    to draw new views if necessary."""
    load_game_and_ui = Signal(str)  # should pass a savegame; maybe a path??
    start_new_game = Signal()

    resolution = (1024, 768)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MDI window test window")
        self.setFixedSize(MainWindow.resolution[0], MainWindow.resolution[1])
        self.setWindowFlags(self.windowFlags())

        self.setCentralWidget(MdiArea())

        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside2'))
    main_window = MainWindow()
    sys.exit(app.exec_())
