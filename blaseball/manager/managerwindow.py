"""
contains the window controls for the main manager window.
the manager window uses the following hierarchy:
ManagerWindow is a QMdiArea, to allow drawing things like tooltips and
pop-up windows, while keeping them constrained to the app area

the main window in this is another MainWindow, which holds a tab control

"""

from PySide2.QtWidgets import (QWidget, QMdiArea, QMdiSubWindow, QTabBar,
                               QVBoxLayout, QFrame)
from PySide2.QtCore import (Qt, QPoint, QTimer, QPropertyAnimation,
                            QAbstractAnimation)

from blaseball.util.qthelper import TestWindow
from blaseball.settings import Settings


class SubWindow(QMdiSubWindow):
    """This is a single subwindow displayed in the manager area"""
    def __init__(self, widget, manager, geometry, pos_x, pos_y, pos_z=0):
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
                         "y":pos_y,
                         "z":pos_z
                         }

        self.manager = manager
        self.manager.addSubWindow(self)
        self.show()
        # self.showMaximized()


class ManagerWindow(QWidget):
    TASKBAR_BUTTONS = 10

    """This is the central widget for the standard management window."""
    def __init__(self, main_window, game=None):
        super().__init__()
        self.main_window = main_window

        if game is None:
            game = "LA Tostadas: Day 1"

        self.mda = self._init_mda()
        self.bar = self._init_bar()
        self._init_layout()

        self.windows = []
        self.animations = [None, None]
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
        # bar.setStyleSheet('QTabBar::tab:top { margin-bottom: 0px; margin-left: 1px;'
        #                   'margin-right: 1px; padding-bottom: 0px; }')
        bar.setStyleSheet('QTabBar::tab:bottom { margin-top: 0px; margin-left: 1px;'
                          'margin-right: 1px; padding-bottom: 0px; }')
        return bar

    def _init_layout(self):
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self.mda)
        layout.addWidget(self.bar)
        self.setLayout(layout)

    def _init_windows(self):
        """everything that needs to be drawn after the first draw loop
        execution"""
        self.geometry = self.mda.size()
        for i in range(0, ManagerWindow.TASKBAR_BUTTONS):
            new_window = SubWindow(TestWindow(), self.mda, self.geometry,
                                   i, 0, 0)
            # new_window.move(self.geometry.width(), 0)
            new_window.move(i*100, 0)
            self.windows.append(new_window)
            self.bar.addTab(str(i))
        # self.windows[0].move(0, 0)

    def view_pos(self, pos):
        move_left = pos < self.current_coords['x']
        current_window = None
        current_z = -1000
        new_window = None
        for window in self.windows:
            if window.location['x'] == self.current_coords['x']:
                if window.location['z'] > current_z:
                    if current_window is not None:
                        if move_left:
                            current_window.move(self.geometry.width(),
                                                current_window.pos().y)
                        else:
                            current_window.move(-self.geometry.width(),
                                                current_window.pos().y)
                    current_window = window
                    current_z = window.location["z"]
                    print(f"old window pos {current_window.location['x']}")
                    continue
            if window.location['x'] < pos:
                window.move(-self.geometry.width(), window.pos().y())
            elif window.location['x'] > pos:
                window.move(self.geometry.width(), window.pos().y())
            else:
                new_window = window
                #TODO: handle new window z order??
        self._animate_center(new_window, current_window, move_left)
        self.current_coords['x'] = pos

    def _get_animation_slot(self, window, animation_property):
        index = -1
        for i in range(0, len(self.animations)):
            if self.animations[i] is None:
                index = i
                break
            elif self.animations[i].state() == QAbstractAnimation.Stopped:
                index = i
                break
        if index == -1:
            # TODO: actually close these animations out
            print("Animation stack overflow, halting old animations")
            for animation in self.animations:
                animation.stop()
            self.animations = [None, None]
            index = 0
        self.animations[index] = QPropertyAnimation(window, animation_property)
        print(f"returning ani slot {index}")
        return self.animations[index]

    def _animate_window_slide(self, window, endpoint, speed):
        animation = self._get_animation_slot(window, b'pos')
        animation.setDuration(speed)
        animation.setStartValue(window.pos())
        animation.setEndValue(endpoint)
        animation.DeleteWhenStopped = True
        animation.start()

    def _animate_center(self, window, old_window, move_left):
        # TODO: you have a bug when switching not back and forth :c
        if Settings.animate_window_transition:
            if old_window is not None:
                if move_left:
                    old_window_point = QPoint(-self.geometry.width(),
                                              old_window.pos().y())
                else:
                    old_window_point = QPoint(self.geometry.width(),
                                              old_window.pos().y())
                self._animate_window_slide(old_window,
                                           old_window_point,
                                           10000)
            self._animate_window_slide(window, QPoint(0, 0), 10000)
        else:
            #TODO: also move old window here
            window.move(0, window.pos().y())

    #TODO: refactor all the "move_left" and redundant store inactive window
    #code so it's in one nice function (maybe make dest a function so you
    #just like call .move(storepos(window, pos))

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