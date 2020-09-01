"""
This holds global settings.

In the future this will handle reading/writing settings, as well as sending out
notifications when they get updated. But for now, it's just globals.
"""

from blaseball.util.qthelper import EasyDialog

class Settings():
    resolution = (1024, 768)


class SettingsWindow(EasyDialog):
    """the main settings window"""

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window

        self.add_button("Back", main_window.go_back_window.emit)

        self.finish()
