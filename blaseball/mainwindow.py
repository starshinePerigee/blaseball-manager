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

from blaseball.settings import Settings, SettingsWindow
from blaseball.startgame import startmenu, newgame
from blaseball.manager import managerwindow


class MainWindow(QMainWindow):
    """The main application window. Once a game is loaded, this
    instantiates UI elements on itself directly - use modal windows
    to draw new views if necessary."""
    load_game_and_ui = Signal(str)  # should pass a savegame; maybe a path??
    foreground_window = Signal(str)
    go_back_window = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EXTREEM BLASEBALL MANAGER '99")
        self.setFixedSize(Settings.resolution[0], Settings.resolution[1])
        self.setWindowFlags(self.windowFlags())

        self.stack_dir = []
        self.stack_history = []
        self.main_stack = QStackedWidget()
        self.setCentralWidget(self.main_stack)

        self.load_game_and_ui.connect(self.start_game)
        self.foreground_window.connect(self.switch_window)
        self.go_back_window.connect(self.window_back)

        self.add_window('start', startmenu.StartMenu(self))
        self.add_window('new game', newgame.NewGame(self))
        self.add_window('settings', SettingsWindow(self))
        self.switch_window('start')

        self.show()

    def add_window(self, name, widget):
        self.stack_dir.append(name)
        self.main_stack.addWidget(widget)

    def drop_window(self, name):
        window_index = self.stack_dir.index(name)
        dropped_widget = self.main_stack.widget(window_index)
        self.main_stack.removeWidget(dropped_widget)
        dropped_widget.destroy()
        self.stack_dir.remove(name)

    def switch_window(self, name):
        window_index = self.stack_dir.index(name)
        self.main_stack.setCurrentIndex(window_index)
        self.stack_history.insert(0, name)

    def window_back(self):
        self.stack_history.pop(0)
        self.switch_window(self.stack_history.pop(0))

    def start_game(self, game):
        self.add_window('manager', managerwindow.ManagerWindow(self, game))
        self.switch_window('manager')
        self.drop_window('start')
        self.drop_window('new game')

    def new_game(self):
        self.switch_window('new game')

    def exit_application(self):
        QCoreApplication.instance().quit()
