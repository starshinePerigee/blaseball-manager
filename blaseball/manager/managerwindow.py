"""
contains the window controls for the main manager window.
the manager window uses the following hierarchy:
ManagerWindow is a QMdiArea, to allow drawing things like tooltips and
pop-up windows, while keeping them constrained to the app area

the main window in this is another MainWindow, which holds a tab control

"""

from PySide2.QtWidgets import QMdiArea

class ManagerWindow(QMdiArea):
    def __init__(self, main_window, game=None):
        super().__init__()
        self.main_window = main_window

        if game is None:
            game = "LA Tostadas: Day 1"


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