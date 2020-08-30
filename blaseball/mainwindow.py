from functools import partial

from PySide2.QtCore import Signal, Slot
from PySide2.QtWidgets import QMainWindow

from blaseball.startgame import startmenu
from blaseball.util.qthelper import EasyDialog

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
        self.setCentralWidget(startmenu.StartMenu(self))

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