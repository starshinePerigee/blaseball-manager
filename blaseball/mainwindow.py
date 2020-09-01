"""
Contains the UI logic for the main application window, as well as moving between
primary game states.

mainwindow is a QMainWindow, with a QStackedWidget main widget. Menus and such
should implement widgets, that go into the stack.

manager (and other windows that require toolbar / dock / layout functionality)
should impliment as a amainwindow or gridlayout with mdiarea

"""

from PySide2.QtCore import Signal, Slot, QCoreApplication
from PySide2.QtWidgets import QMainWindow, QStackedWidget

from blaseball.settings import Settings
from blaseball.startgame import startmenu, newgame
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
        self.setFixedSize(Settings.resolution[0], Settings.resolution[1])
        self.setWindowFlags(self.windowFlags())

        self.main_stack = QStackedWidget()
        self.setCentralWidget(self.main_stack)

        self.load_game_and_ui.connect(self.start_game)
        self.start_new_game.connect(self.new_game)

        self.start_game_menu = startmenu.StartMenu(self)
        self.main_stack.addWidget(self.start_game_menu)
        self.new_game_menu = newgame.NewGame(self)
        self.main_stack.addWidget(self.new_game_menu)
        self.main_stack.setCurrentIndex(0)

        self.show()

    def start_game(self, game):
        print(f"loading new game {game}")
        self.main_ui = EasyDialog()
        self.main_ui.add_button("Test", self.exit_application)
        self.centralWidget().hide()
        self.setCentralWidget(self.main_ui)
        self.main_ui.finish()

    def new_game(self):


    def exit_application(self):
        QCoreApplication.instance().quit()