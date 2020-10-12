"""
This contains some classes to wrap QT objects to make my life a little easier.
Try to only use these in debugging and placeholder classes?
"""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QWidget, QDialog, QPushButton, QVBoxLayout,
                               QLabel)
from PySide2.QtGui import QColor


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

    def keyPressEvent(self, event):
        if not event.key() == Qt.Key_Escape:
            super().keyPressEvent(event)


class TestWindow(QWidget):
    """This is a window-filling area of unique shade and ID designed to
    fill space"""
    id_num = 1000
    # to cycle colors, pick a min and max and then cycle through RGB space
    # within those bounds.
    # we're going to use 100 - 200
    # red is 200, 100, 100, orange is 200, 150, 100,
    # yellow-green is 200, 200, 100, next is 150, 200, 100
    # for a cycle of 12 colors.
    color_cycle = (1, 1, 1, 0.5, 0, 0, 0, 0, 0, 0.5, 1, 1)

    @staticmethod
    def get_color(seed):
        r = TestWindow.color_cycle[seed*5 % 12]
        g = TestWindow.color_cycle[(seed*5 + 4) % 12]
        b = TestWindow.color_cycle[(seed*5 + 8) % 12]
        return 100+100*r, 100+100*g, 100+100*b

    @staticmethod
    def get_id():
        new_id = TestWindow.id_num
        TestWindow.id_num += 1
        return new_id

    def __init__(self):
        super().__init__()

        self.id = TestWindow.get_id()

        self.setStyleSheet(f"background-color: "
                           f"rgb{str(self.get_color(self.id))}")

        # self.autoFillBackground = True
        # p = self.palette()
        # p.setColor(self.backgroundRole(), TestWindow.get_color(self.id))
        # self.setPalette(p)

        text = f"{self.id} {self.size().toTuple()}"
        self.label = QLabel(text, parent=self)
        self.label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.resizeEvent = self.update_text

        self.show()

    def update_text(self, event=None):
        text = f"{self.id} {self.size().toTuple()}"
        self.label.resize(self.size())
        self.label.setText(text)
