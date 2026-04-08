from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF
from PyQt6.QtCore import QPointF


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
        """Ajusta a viewport para manter o conteúdo centralizado e com a proporção correta."""
        canvas_width = self.width()
        canvas_height = self.height()

        # Verifica se o canvas tem dimensões válidas
        if canvas_width <= 0 or canvas_height <= 0:
            return

        # Calcula a proporção do canvas atual
        canvas_aspect = canvas_width / canvas_height

        # Caso 1: Canvas é mais largo que a viewport, então limitamos pela hight
        if canvas_aspect > self.viewport_aspect:
            vp_height = float(canvas_height)
            vp_width = vp_height * self.viewport_aspect
            x_offset = (canvas_width - vp_width) / 2
            y_offset = 0.0
        # Caso 2: Canvas é mais alto que ou igual a viewport, então limitamos pela width
        else:
            vp_width = float(canvas_width)
            vp_height = vp_width / self.viewport_aspect
            x_offset = 0.0
            y_offset = (canvas_height - vp_height) / 2

        self.viewport.xmin = x_offset
        self.viewport.ymin = y_offset
        self.viewport.xmax = x_offset + vp_width
        self.viewport.ymax = y_offset + vp_height

    def _transformar_ponto(self, ponto_mundo):
        """Converte ponto do mundo -> SCN -> Viewport."""
        ponto_scn = self.window.generate_scn(ponto_mundo)
        return self.viewport.viewport_transform_scn(ponto_scn)

    def paintEvent(self, event):
        """Desenha todos os objetos do Display File."""
        painter = QPainter(self)

        for obj in self.display_file.objetos:
            pen = QPen(QColor(obj.cor), 3)
            painter.setPen(pen)

            # Transforma coordenadas do mundo -> SCN -> Viewport
            coords_vp = [self._transformar_ponto(pt) for pt in obj.pontos]

            if obj.tipo == "Ponto":
                x, y = coords_vp[0]
                painter.drawPoint(int(x), int(y))

            elif obj.tipo == "Reta":
                x1, y1 = coords_vp[0]
                x2, y2 = coords_vp[1]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            elif obj.tipo == "Wireframe":
                if getattr(obj, 'preenchido', False):
                    poligono = QPolygonF([QPointF(x, y) for x, y in coords_vp])
                    painter.setBrush(QBrush(QColor(obj.cor)))
                    painter.drawPolygon(poligono)
                    painter.setBrush(QBrush())
                else:
                    for i in range(len(coords_vp) - 1):
                        x1, y1 = coords_vp[i]
                        x2, y2 = coords_vp[i + 1]
                        painter.drawLine(int(x1), int(y1), int(x2), int(y2))
                    x_inicio, y_inicio = coords_vp[0]
                    x_fim, y_fim = coords_vp[-1]
                    painter.drawLine(int(x_fim), int(y_fim), int(x_inicio), int(y_inicio))