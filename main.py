# main.py
import sys
from PyQt6.QtWidgets import QApplication
from src.core.display_file import DisplayFile
from src.core.window import Window
from src.core.viewport import Viewport
from src.core.window3d import Window3D
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    display_file = DisplayFile()
    window = Window()
    viewport = Viewport()
    window3d = Window3D()

    tela = MainWindow(display_file, window, viewport, window3d)
    tela.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
