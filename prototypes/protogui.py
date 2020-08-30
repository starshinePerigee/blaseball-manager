import sys
import os
from time import sleep
from functools import partial

from PySide2.QtCore import Qt, Signal, Slot, QRect, QPropertyAnimation
from PySide2.QtWidgets import (QApplication, QMainWindow, QDialog, QVBoxLayout,
    QPushButton, QLabel)
import qdarkstyle


TEAMS_99 = [
    "Chicago EMT",
    "Dallas Meat",
    "San Fransisco Pals",
    "Kansas City Toothpaste",
    "Los Angeles Burritos",
    "Hades Lions",
    "Philly Cakes",
    "Baltimore Crabs",
    "Mexico City Chicken Strips",
    "Moab Sunrise",
    "New York Gen X",
    "Charleston Cobbler Elves",
    "Yellowstone Magicians",
    "Boston Blooms",
    "Hawaii Weekends",
    "Breckenridge Thumbs Up",
    "Canada Toothbrushes",
    "Seattle Smash Mouth",
    "Miami Do It",
    "Houston Infiltration",
]


class EasyDialog(QDialog):
    """QDialog extended with some extra utility functions"""
    def __init__(self, buttons=None):
        super().__init__()

        self.buttons = []
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)

        if buttons is not None:
            for button in buttons:
                self.add_button(button[0], button[1])

    def add_button(self, text, function):
        new_button = QPushButton(text)
        new_button.clicked.connect(function)
        self.layout.addWidget(new_button)
        self.buttons.append(new_button)

    def finish(self):
        self.setLayout(self.layout)
        self.show()


class StartMenu(EasyDialog):
    """The first dialog that greets users when the application is opened."""

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window

        self.add_button("Load Recent Game: [Los Angeles Burritos, Day 199]",
                        self.load_recent_game)
        self.add_button("Load Saved Game", self.load_other_game)
        self.add_button("Start New Game", self.start_new_game)
        self.add_button("Import...", self.start_import)

        self.layout.setSpacing(20)

        self.finish()

    def load_recent_game(self):
        self.main_window.load_game_and_ui.emit(
            "Los Angeles Burritos, Day 199")

    def load_other_game(self):
        self.main_window.load_game_and_ui.emit(
            "Charleston Cobbler Elves, Day 14")

    def start_new_game(self):
        self.main_window.start_new_game.emit()

    def start_import(self):
        print("Starting import menu.")


class MainWindow(QMainWindow):
    """The main application window. Once a game is loaded, this
    instantiates UI elements on itself directly - use modal windows
    to draw new views if necessary."""
    load_game_and_ui = Signal(str)  # should pass a savegame; maybe a path??
    start_new_game = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EXTREEM BLASEBALL MANAGER '99")
        self.resize(800, 600)

        self.main_ui = None
        self.setCentralWidget(StartMenu(self))

        self.load_game_and_ui.connect(self.start_game)
        self.start_new_game.connect(self.new_game)

        self.show()

    def start_game(self, game):
        print(f"loading new game {game}")
        self.main_ui = EasyDialog()
        self.main_ui.add_button("Test", self.nah)
        self.centralWidget().hide()
        self.setCentralWidget(self.main_ui)
        self.main_ui.finish()

    def new_game(self):
        menu_items = []
        for team in TEAMS_99:
            team_fn = partial(self.load_game_and_ui.emit,
                              team + ": Day 1")
            menu_items.append((team, team_fn))
        new_game_menu = EasyDialog(menu_items)
        self.setCentralWidget(new_game_menu)
        new_game_menu.finish()

    def nah(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside2'))
    main_window = MainWindow()
    sys.exit(app.exec_())
