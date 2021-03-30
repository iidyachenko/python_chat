import sys

from PyQt5.QtWidgets import QMainWindow, QApplication
from main_window_template import Ui_MainWindow


class ClientMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Загружаем конфигурацию окна из дизайнера
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ClientMainWindow()

    app.exec_()
