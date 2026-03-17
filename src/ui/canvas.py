# src/ui/canvas.py
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import Qt


class Canvas(QWidget):
    def __init__(self, display_file, window, viewport):
        super().__init__()
        self.display_file = display_file
        self.window = window
        self.viewport = viewport
        self.setStyleSheet("background-color: white; border: 1px solid black;")

    def paintEvent(self, event):
        """Função é chamada automaticamente pelo PyQt sempre que a tela precisa ser atualizada."""
        painter = QPainter(self)
        pen = QPen(Qt.GlobalColor.black, 5)  # Caneta preta, espessura 2
        painter.setPen(pen)

        # Atualiza o tamanho da viewport de acordo com o tamanho real do widget na tela
        self.viewport.xmax = self.width()
        self.viewport.ymax = self.height()

        # Desenha todos os objetos do Display File
        for obj in self.display_file.objetos:
            # 1. Transforma todas as coordenadas do objeto (Window -> Viewport)
            coords_vp = [self.viewport.viewport_transform(pt, self.window) for pt in obj.pontos]
            # 2. Desenha o objeto de acordo com o seu tipo
            if obj.tipo == "Ponto":
                x, y = coords_vp[0]
                painter.drawPoint(int(x), int(y))

            elif obj.tipo == "Reta":
                # Desenha uma linha ligando as duas coordenadas
                x1, y1 = coords_vp[0]
                x2, y2 = coords_vp[1]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            elif obj.tipo == "Wireframe":
                # Desenha linhas conectando os pontos dois a dois
                for i in range(len(coords_vp) - 1):
                    x1, y1 = coords_vp[i]
                    x2, y2 = coords_vp[i + 1]
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))
                x_inicio, y_inicio = coords_vp[0]
                x_fim, y_fim = coords_vp[-1]
                painter.drawLine(int(x_fim), int(y_fim), int(x_inicio), int(y_inicio))