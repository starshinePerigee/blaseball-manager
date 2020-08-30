"""
Handles the start menu, initial options, etc.
"""


from blaseball.util.qthelper import EasyDialog


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
        self.add_button("Options", self.start_options)

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

    def start_options(self):
        print("Starting options menu.")