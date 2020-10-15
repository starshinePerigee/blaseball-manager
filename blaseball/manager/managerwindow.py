"""
contains the window controls for the main manager window.
the manager window uses the following hierarchy:
ManagerWindow is a QMdiArea, to allow drawing things like tooltips and
pop-up windows, while keeping them constrained to the app area

the main window in this is another MainWindow, which holds a tab control

"""

from PySide2.QtWidgets import (QWidget, QMdiArea, QMdiSubWindow, QTabBar,
                               QVBoxLayout, QFrame, QStatusBar)
from PySide2.QtCore import (Qt, QPoint, QTimer, QPropertyAnimation)

from blaseball.util.qthelper import TestWindow
from blaseball.settings import Settings


PLACEHOLDER_WINDOWS = [
    "News",
    "Management",
    "Players",
    "Team",
    "Intel",
    "Politics",
    "Games"
]


class SubWindow(QMdiSubWindow):
    """This is a single subwindow displayed in the manager area"""
    def __init__(self, widget, manager, geometry, pos_x, pos_y):
        """
        Create a new subwindow as position x, y z:
        X: position in the horizontal window stack
        Y: vertical position relative to the centerline (0 is for main windows)
        Z: z-order. leave as 0 to let the manager handle it.
        """
        super().__init__()
        self.setWidget(widget)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setFixedSize(geometry)

        self.location = {"x":pos_x,
                         "y":pos_y
                         }

        self.manager = manager
        self.manager.addSubWindow(self)
        self.show()
        # self.showMaximized()


class StatusBar(QStatusBar):
    def __init__(self, parent):
        super().__init__(parent)


class ManagerWindow(QWidget):
    WINDOW_TRANS_SPEED = 100

    """This is the central widget for the standard management window."""
    def __init__(self, main_window, game=None):
        super().__init__()
        self.main_window = main_window

        if game is None:
            game = "LA Tostadas: Day 1"

        self.mda = self._init_mda()
        self.bar = self._init_bar()
        self.status = self._init_status()
        self._init_layout()

        self.status.showMessage(game)

        self.windows = []
        self.animations = []
        self.geometry = QPoint(0, 0)
        QTimer.singleShot(0, self._init_windows)
        self.bar.currentChanged.connect(self.view_pos)

        self.current_coords = {'x': -1, 'y':0}

    def _init_mda(self):
        mda = QMdiArea(self)
        mda.setFrameStyle(QFrame.NoFrame)
        mda.setStyleSheet("QMdaArea { border: None; }"
                        "QAbstractScrollArea { border: None; padding: 0px }")
        return mda

    def _init_bar(self):
        bar = QTabBar(self)
        bar.setShape(QTabBar.RoundedSouth)
        bar.setStyleSheet('QTabBar { padding: 0px; }')
        bar.setStyleSheet('QTabBar::tab:bottom { margin-top: 0px; margin-left: 1px;'
                          'margin-right: 1px; padding-bottom: 0px; height: 20px}')
        return bar

    def _init_status(self):
        return StatusBar(self)

    def _init_layout(self):
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self.status)
        layout.addWidget(self.mda, stretch=80)
        layout.addWidget(self.bar, stretch=20)
        self.setLayout(layout)

    def _init_windows(self):
        """everything that needs to be drawn after the first draw loop
        execution"""
        self.geometry = self.mda.size()
        for i in range(0, len(PLACEHOLDER_WINDOWS)):
            new_window = SubWindow(TestWindow(), self.mda, self.geometry,
                                   i, 0)
            # new_window.move(self.geometry.width(), 0)
            new_window.move(self.geometry.width(), 0)
            self.windows.append(new_window)
            self.bar.addTab(PLACEHOLDER_WINDOWS[i])
        self.windows[0].move(0, 0)

    def view_pos(self, new_pos):
        old_pos = self.current_coords['x']
        self.current_coords['x'] = new_pos
        for window in self.windows:
            if window.location['x'] == new_pos:
                # we want to show this window
                self._move_center(window, old_pos)
            elif window.location['x'] == old_pos:
                # this window needs to leave
                self._store_window(window, new_pos, True)

    def _get_animation_slot(self, window, animation_property):
        # clear expired slots
        self.animations[:] = [x for x in self.animations if x is not None]
        if len(self.animations) > 100:
            raise MemoryError("Animation stack overflow?")
        # finish any move animations that affect the current window:
        for animation in self.animations:
            if animation.targetObject() == window:
                endpoint = animation.endValue()
                animation.stop()
                window.move(endpoint)
        self.animations.append(QPropertyAnimation(window, animation_property))
        return self.animations[len(self.animations)-1]

    def _animate_window_slide(self, window, startpoint, endpoint,
                              speed=WINDOW_TRANS_SPEED):
        animation = self._get_animation_slot(window, b'pos')
        animation.setDuration(speed)
        animation.setStartValue(startpoint)
        animation.setEndValue(endpoint)
        animation.DeleteWhenStopped = True
        animation.start()

    def _store_window(self, window, new_pos, animate=False):
        if window is None:
            return
        # if desired loc (win.loc) is less than new pos, we want the window
        # to move left; ie: negative
        move_polarity = -1 if window.location["x"] < new_pos else 1
        store_point = QPoint(move_polarity*self.geometry.width(),
                             window.pos().y())
        if animate and Settings.animate_window_transition:
            self._animate_window_slide(window, window.pos(), store_point)
        else:
            window.move(store_point)

    def _move_center(self, window, old_pos):
        if Settings.animate_window_transition:
            # if old location is less than new location (win.loc),
            # we're moving the viewport right, so this window needs to start
            # to the right of frame (positive) and slide in leftways
            move_polarity = 1 if old_pos < window.location['x'] else -1
            startpoint = QPoint(self.geometry.width() * move_polarity,
                                window.pos().y())
            self._animate_window_slide(window, startpoint, QPoint(0, 0))
        else:
            window.move(0, window.pos().y())


if __name__ == "__main__":
    import sys
    from PySide2.QtWidgets import QApplication
    import qdarkstyle
    from blaseball import mainwindow

    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside2'))
    main_window = mainwindow.MainWindow()
    main_window.add_window('manager', ManagerWindow(main_window))
    main_window.switch_window('manager')
    sys.exit(app.exec_())
