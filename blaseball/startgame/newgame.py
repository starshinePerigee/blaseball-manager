"""
Handles the new game configuration settings, etc.
"""

from functools import partial

from blaseball.util.qthelper import EasyDialog

from data import teams

class NewGame(EasyDialog):
    """The first dialog that greets users when the application is opened."""

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window

        menu_items = []
        for team in teams.TEAMS_99:
            team_fn = partial(self.load_game_and_ui.emit,
                              team + ": Day 1")
            menu_items.append((team, team_fn))
        new_game_menu = EasyDialog(menu_items)
        self.setCentralWidget(new_game_menu)
        new_game_menu.finish()
