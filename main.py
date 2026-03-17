# main.py
import sys
from PyQt6.QtWidgets import QApplication
from src.core.display_file import DisplayFile
from src.core.window import Window
from src.core.viewport import Viewport
from src.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    # Cria as estruturas principais do sistema gráfico
    display_file = DisplayFile()
    window = Window()
    viewport = Viewport()

    # Inicializa e exibe a interface gráfica
    tela = MainWindow(display_file, window, viewport)
    tela.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()