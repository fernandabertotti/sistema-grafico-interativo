from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class Canvas(QWidget):
    def __init__(self, display_file, window, viewport):
        super().__init__()
        self.display_file = display_file
        self.window = window
        self.viewport = viewport
        vp_width = self.viewport.xmax - self.viewport.xmin
        vp_height = self.viewport.ymax - self.viewport.ymin
        # Calcula a proporção da viewport
        self.viewport_aspect = vp_width / vp_height if vp_height != 0 else 1.0
        self.setStyleSheet("background-color: white; border: 1px solid black;")

    def resizeEvent(self, event):
        self._sync_viewport_to_canvas_center()
        super().resizeEvent(event)

    def _sync_viewport_to_canvas_center(self):
        """Ajusta a viewport para manter o conteúdo centralizado e com a proporção correta ao redimensionar o canvas."""
        # Leitura do tamanho atual do canvas
        canvas_width = self.width()
        canvas_height = self.height()

        # Verifica se o canvas tem dimensões válidas
        if canvas_width <= 0 or canvas_height <= 0:
            return

        # Calcula a proporção do canvas atual
        canvas_aspect = canvas_width / canvas_height

        # Caso 1: Canvas é mais largo que a viewport, então limitamos pela altura
        if canvas_aspect > self.viewport_aspect:
            vp_height = float(canvas_height)
            vp_width = vp_height * self.viewport_aspect
            x_offset = (canvas_width - vp_width) / 2
            y_offset = 0.0
        # Caso 2: Canvas é mais alto que ou igual a viewport, então limitamos pela largura
        else:
            vp_width = float(canvas_width)
            vp_height = vp_width / self.viewport_aspect
            x_offset = 0.0
            y_offset = (canvas_height - vp_height) / 2

        self.viewport.xmin = x_offset
        self.viewport.ymin = y_offset
        self.viewport.xmax = x_offset + vp_width
        self.viewport.ymax = y_offset + vp_height

    def paintEvent(self, event):
        """Função é chamada automaticamente pelo PyQt sempre que a tela precisa ser atualizada."""
        painter = QPainter(self)
        
        # Desenha todos os objetos do Display File
        for obj in self.display_file.objetos:
            # Configura a caneta com a cor do objeto atual e a espessura adequada
            pen = QPen(QColor(obj.cor), 3)  
            painter.setPen(pen)

            # 1. Transforma todas as coordenadas do objeto (Window -> Viewport)
            coords_vp = [self.viewport.viewport_transform(pt, self.window) for pt in obj.pontos]
            
            # 2. Desenha o objeto de acordo com o seu tipo
            if obj.tipo == "Ponto":
                x, y = coords_vp[0]
                painter.drawPoint(int(x), int(y))

            elif obj.tipo == "Reta":
                x1, y1 = coords_vp[0]
                x2, y2 = coords_vp[1]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            elif obj.tipo == "Wireframe":
                for i in range(len(coords_vp) - 1):
                    x1, y1 = coords_vp[i]
                    x2, y2 = coords_vp[i + 1]
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))
                x_inicio, y_inicio = coords_vp[0]
                x_fim, y_fim = coords_vp[-1]
                painter.drawLine(int(x_fim), int(y_fim), int(x_inicio), int(y_inicio))