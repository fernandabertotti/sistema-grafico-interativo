from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPolygonF
from PyQt6.QtCore import QPointF
from src.utils.utils import VP_MARGIN, BEZIER_STEPS
from src.core.bspline import gerar_pontos_bspline
from src.core.bspline_surface import gerar_segmentos_superficie_bspline
from src.core.clipping import (
    clip_ponto,
    clip_reta_cohen_sutherland,   # ou liang_barsky — escolha uma e use radio button na UI
    clip_reta_liang_barsky,
    clip_poligono_sutherland_hodgman,
)
from src.core.bezier import gerar_pontos_curva
from src.core.framebuffer import Framebuffer
from src.core.phong import LuzPontual, MaterialPhong

class Canvas(QWidget):
    def __init__(self, display_file, window, viewport, window3d):
        super().__init__()
        self.display_file = display_file
        self.window = window
        self.viewport = viewport
        self.window3d = window3d
        self.algoritmo_clip_reta = "CS"
        self.modo_perspectiva = False
        self.distancia_focal = 500.0
        vp_width = self.viewport.xmax - self.viewport.xmin
        vp_height = self.viewport.ymax - self.viewport.ymin
        # Calcula a proporção da viewport
        self.viewport_aspect = vp_width / vp_height if vp_height != 0 else 1.0

        # --- Rasterizacao / Shading (Trabalhos 2.1, 2.2 e 2.3) ---
        self.modo_framebuffer = False   # ativa render via Framebuffer
        self.usar_zbuffer = True        # checagem de profundidade nos triangulos
        self.usar_phong = True          # shading de Phong por pixel
        self.framebuffer = Framebuffer(int(vp_width), int(vp_height))
        # Parametros de iluminacao (ajustaveis pela UI).
        self.luz = LuzPontual([200.0, 200.0, 300.0], (1.0, 1.0, 1.0))
        self.material = MaterialPhong()
        self.luz_ambiente = (0.2, 0.2, 0.2)

        self.setStyleSheet("background-color: white; border: 1px solid black;")

    def resizeEvent(self, event):
        self._sync_viewport_to_canvas_center()
        self._criar_framebuffer()
        super().resizeEvent(event)

    def _criar_framebuffer(self):
        """Recria o framebuffer com as dimensoes atuais da viewport."""
        largura = int(self.viewport.xmax - self.viewport.xmin)
        altura = int(self.viewport.ymax - self.viewport.ymin)
        if largura > 0 and altura > 0:
            self.framebuffer = Framebuffer(largura, altura)

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

        # Aplica margem para criar a moldura de clipping
        margin = VP_MARGIN
        vp_width -= 2 * margin
        vp_height -= 2 * margin
        x_offset = (canvas_width - vp_width) / 2
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

        # Desenha a moldura vermelha da viewport
        vp = self.viewport
        pen_borda = QPen(QColor("red"), 2)
        painter.setPen(pen_borda)
        painter.setBrush(QBrush())
        painter.drawRect(int(vp.xmin), int(vp.ymin),
                         int(vp.xmax - vp.xmin), int(vp.ymax - vp.ymin))

        # No modo framebuffer, limpa o buffer proprio antes de rasterizar 3D.
        if self.modo_framebuffer:
            self.framebuffer.usar_zbuffer = self.usar_zbuffer
            self.framebuffer.clear()

        for obj in self.display_file.objetos:
            pen = QPen(QColor(obj.cor), 3)
            painter.setPen(pen)

            if obj.tipo == "Objeto3D":
                if self.modo_framebuffer:
                    self._desenhar_objeto3d_framebuffer(obj)
                    continue
                fn_clip = (clip_reta_cohen_sutherland
                           if self.algoritmo_clip_reta == "CS"
                           else clip_reta_liang_barsky)
                for p1, p2 in obj.segmentos:
                    if self.modo_perspectiva:
                        scn1 = self.window3d.generate_scn_3d_perspective(
                            (p1.x, p1.y, p1.z), self.distancia_focal)
                        scn2 = self.window3d.generate_scn_3d_perspective(
                            (p2.x, p2.y, p2.z), self.distancia_focal)
                    else:
                        scn1 = self.window3d.generate_scn_3d((p1.x, p1.y, p1.z))
                        scn2 = self.window3d.generate_scn_3d((p2.x, p2.y, p2.z))
                    resultado = fn_clip(scn1, scn2)
                    if resultado:
                        vp1 = self.viewport.viewport_transform_scn(resultado[0])
                        vp2 = self.viewport.viewport_transform_scn(resultado[1])
                        painter.drawLine(int(vp1[0]), int(vp1[1]),
                                         int(vp2[0]), int(vp2[1]))
                continue

            if obj.tipo == "Objeto3DPhong":
                if self.modo_framebuffer:
                    self._desenhar_phong_framebuffer(obj)
                continue

            if obj.tipo == "SuperficieBSpline3D":
                fn_clip = (clip_reta_cohen_sutherland
                           if self.algoritmo_clip_reta == "CS"
                           else clip_reta_liang_barsky)
                segmentos = gerar_segmentos_superficie_bspline(
                    obj.matriz_controle, getattr(obj, "passos", 10))
                for p1, p2 in segmentos:
                    if self.modo_perspectiva:
                        scn1 = self.window3d.generate_scn_3d_perspective(
                            (p1.x, p1.y, p1.z), self.distancia_focal)
                        scn2 = self.window3d.generate_scn_3d_perspective(
                            (p2.x, p2.y, p2.z), self.distancia_focal)
                    else:
                        scn1 = self.window3d.generate_scn_3d((p1.x, p1.y, p1.z))
                        scn2 = self.window3d.generate_scn_3d((p2.x, p2.y, p2.z))
                    resultado = fn_clip(scn1, scn2)
                    if resultado:
                        vp1 = self.viewport.viewport_transform_scn(resultado[0])
                        vp2 = self.viewport.viewport_transform_scn(resultado[1])
                        painter.drawLine(int(vp1[0]), int(vp1[1]),
                                         int(vp2[0]), int(vp2[1]))
                continue

            # Converte para SCN (clipping acontece aqui, em [-1,1]x[-1,1])
            coords_scn = [self.window.generate_scn(pt) for pt in obj.pontos]

            if obj.tipo == "Ponto":
                if clip_ponto(coords_scn[0]):
                    x, y = self.viewport.viewport_transform_scn(coords_scn[0])
                    painter.drawPoint(int(x), int(y))

            elif obj.tipo == "Reta":
                fn_clip = (clip_reta_cohen_sutherland
                           if self.algoritmo_clip_reta == "CS"
                           else clip_reta_liang_barsky)
                resultado = fn_clip(coords_scn[0], coords_scn[1])
                if resultado:
                    p1c, p2c = resultado
                    x1, y1 = self.viewport.viewport_transform_scn(p1c)
                    x2, y2 = self.viewport.viewport_transform_scn(p2c)
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            elif obj.tipo == "Wireframe":
                fn_clip = (clip_reta_cohen_sutherland
                           if self.algoritmo_clip_reta == "CS"
                           else clip_reta_liang_barsky)

                if getattr(obj, 'preenchido', False):
                    # Polígono preenchido → Sutherland-Hodgman
                    clipados = clip_poligono_sutherland_hodgman(coords_scn)
                    if len(clipados) >= 3:
                        coords_vp = [self.viewport.viewport_transform_scn(p)
                                     for p in clipados]
                        poligono = QPolygonF([QPointF(x, y) for x, y in coords_vp])
                        painter.setBrush(QBrush(QColor(obj.cor)))
                        painter.drawPolygon(poligono)
                        painter.setBrush(QBrush())
                else:
                    # Wireframe → clipa cada aresta com o algoritmo de reta escolhido
                    n = len(coords_scn)
                    for i in range(n):
                        pa = coords_scn[i]
                        pb = coords_scn[(i + 1) % n]
                        resultado = fn_clip(pa, pb)
                        if resultado:
                            p1c, p2c = resultado
                            x1, y1 = self.viewport.viewport_transform_scn(p1c)
                            x2, y2 = self.viewport.viewport_transform_scn(p2c)
                            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            elif obj.tipo == "Curva2D":
                # 1. Gera pontos amostrados em coordenadas do mundo
                pontos_mundo = gerar_pontos_curva(obj.pontos, BEZIER_STEPS)
                # 2. Converte cada ponto para SCN
                pontos_scn = [self.window.generate_scn(p) for p in pontos_mundo]
                # 3. Clipping por ponto + traço entre pontos visíveis consecutivos.
                #    Quando um ponto é clipado, zera 'anterior' para quebrar o traço.
                anterior_vp = None
                for p_scn in pontos_scn:
                    if clip_ponto(p_scn):
                        x, y = self.viewport.viewport_transform_scn(p_scn)
                        if anterior_vp is not None:
                            ax, ay = anterior_vp
                            painter.drawLine(int(ax), int(ay), int(x), int(y))
                        anterior_vp = (x, y)
                    else:
                        anterior_vp = None

            elif obj.tipo == "BSpline2D":
                pontos_mundo = gerar_pontos_bspline(obj.pontos, BEZIER_STEPS)
                pontos_scn = [self.window.generate_scn(p) for p in pontos_mundo]
                anterior_vp = None
                for p_scn in pontos_scn:
                    if clip_ponto(p_scn):
                        x, y = self.viewport.viewport_transform_scn(p_scn)
                        if anterior_vp is not None:
                            ax, ay = anterior_vp
                            painter.drawLine(int(ax), int(ay), int(x), int(y))
                        anterior_vp = (x, y)
                    else:
                        anterior_vp = None

        # Exibe o framebuffer (com o 3D rasterizado) sobre a viewport.
        if self.modo_framebuffer:
            painter.drawImage(QPointF(self.viewport.xmin, self.viewport.ymin),
                              self.framebuffer.to_qimage())

    # ------------------------------------------------------------------
    # Rasterizacao 3D via Framebuffer (Trabalhos 2.1, 2.2 e 2.3)
    # ------------------------------------------------------------------
    def _cor_rgb(self, cor_hex):
        """Converte '#RRGGBB' em tupla (r, g, b) de inteiros."""
        c = QColor(cor_hex)
        return (c.red(), c.green(), c.blue())

    def _mundo_para_fb(self, ponto_mundo):
        """Projeta um ponto do mundo para (x_fb, y_fb, z_view) no framebuffer."""
        x_scn, y_scn, z_view = self.window3d.generate_scn_3d_with_z(ponto_mundo)
        x_vp, y_vp = self.viewport.viewport_transform_scn((x_scn, y_scn))
        # Coordenadas locais ao framebuffer (origem no canto da viewport).
        return (x_vp - self.viewport.xmin, y_vp - self.viewport.ymin, z_view)

    def _desenhar_objeto3d_framebuffer(self, obj):
        """Rasteriza um Objeto3D (wireframe) no framebuffer com Bresenham."""
        cor = self._cor_rgb(obj.cor)
        for p1, p2 in obj.segmentos:
            x1, y1, _ = self._mundo_para_fb((p1.x, p1.y, p1.z))
            x2, y2, _ = self._mundo_para_fb((p2.x, p2.y, p2.z))
            self.framebuffer.draw_line(x1, y1, x2, y2, cor)

    def _desenhar_phong_framebuffer(self, obj):
        """Rasteriza um Objeto3DPhong no framebuffer (Phong por pixel ou cor plana)."""
        cor_plana = self._cor_rgb(obj.cor)
        olho = tuple(self.window3d.vrp)
        for tri in obj.triangulos:
            (vw0, vw1, vw2) = tri['v']
            (n0, n1, n2) = tri['n']
            f0 = self._mundo_para_fb(vw0)
            f1 = self._mundo_para_fb(vw1)
            f2 = self._mundo_para_fb(vw2)
            if self.usar_phong:
                # Vertice completo: (x_fb, y_fb, z_view, x_world, y_world, z_world)
                v0 = (f0[0], f0[1], f0[2], vw0[0], vw0[1], vw0[2])
                v1 = (f1[0], f1[1], f1[2], vw1[0], vw1[1], vw1[2])
                v2 = (f2[0], f2[1], f2[2], vw2[0], vw2[1], vw2[2])
                self.framebuffer.draw_triangle_phong(
                    v0, v1, v2, n0, n1, n2,
                    self.material, self.luz, olho, self.luz_ambiente)
            else:
                self.framebuffer.draw_triangle_3d(f0, f1, f2, cor_plana)
