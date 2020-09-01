"""
This contains some classes to wrap QT objects to make my life a little easier.
"""

from PySide2.QtCore import Qt
<<<<<<< HEAD
from PySide2.QtWidgets import (QDialog, QPushButton, QVBoxLayout, QLabel)
=======
from PySide2.QtWidgets import (QDialog, QPushButton, QVBoxLayout)
>>>>>>> da3d81f47aa8175d1fed7048a3015567999fabf4


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
<<<<<<< HEAD
        self.show()

    def keyPressEvent(self, event):
        if not event.key() == Qt.Key_Escape:
            super().keyPressEvent(event)
=======
        self.show()
>>>>>>> da3d81f47aa8175d1fed7048a3015567999fabf4
