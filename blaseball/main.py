import sys

from PySide2.QtWidgets import QApplication
import qdarkstyle

from blaseball import mainwindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside2'))
    main_window = mainwindow.MainWindow()
    sys.exit(app.exec_())