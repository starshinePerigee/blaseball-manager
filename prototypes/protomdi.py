import sys
import os
from time import sleep
from functools import partial

from PySide2.QtCore import Qt, Signal, Slot, QPropertyAnimation
from PySide2.QtWidgets import (QApplication, QMainWindow, QDialog, QVBoxLayout,
    QPushButton, QLabel, QMdiArea, QMdiSubWindow)
import qdarkstyle


from blaseball.startgame import startmenu


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


class MainWindow(QMainWindow):
    """The main application window. Once a game is loaded, this
    instantiates UI elements on itself directly - use modal windows
    to draw new views if necessary."""
    load_game_and_ui = Signal(str)  # should pass a savegame; maybe a path??
    start_new_game = Signal()

    resolution = (1024, 768)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EXTREEM BLASEBALL MANAGER '99")
        self.setFixedSize(MainWindow.resolution[0], MainWindow.resolution[1])
        self.setWindowFlags(self.windowFlags())

        self.main_ui = QMdiArea()
        self.setCentralWidget(self.main_ui)

        # self.main_ui.addSubWindow(startmenu.StartMenu(self))
        self.subwindow1 = SubWindow(self.main_ui)
        self.subwindow2 = SubWindow(self.main_ui)
        self.subwindow3 = SubWindow(self.main_ui)

        self.show()

        self.subwindow1.move(0, 0)
        self.subwindow2.move(0, 0)
        self.subwindow3.move(0, 0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside2'))
    main_window = MainWindow()
    sys.exit(app.exec_())
