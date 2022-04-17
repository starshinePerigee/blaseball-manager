"""
This holds global settings.

In the future this will handle reading/writing settings, as well as sending out
notifications when they get updated. But for now, it's just globals.
"""

from blaseball.util.qthelper import EasyDialog


class Settings:
    resolution = (1024, 768)
    animate_window_transition = True
    players_per_team = 25
    min_lineup = 9


class SettingsWindow(EasyDialog):
    """the main settings window"""

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window

        self.add_button("Disable window transition effects",
                        self.toggle_animate_window)
        self.add_button("Back", main_window.go_back_window.emit)

        self.finish()

    def toggle_animate_window(self):
        if Settings.animate_window_transition:
            Settings.animate_window_transition = False
            self.buttons[0].setText("Enable window transition effects")
        else:
            Settings.animate_window_transition = True
            self.buttons[0].setText("Disable window transition effects")
