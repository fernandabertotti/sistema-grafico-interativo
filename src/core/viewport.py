# src/core/viewport.py
from src.utils.utils import VP_X_MIN, VP_Y_MIN, VP_X_MAX, VP_Y_MAX


class Viewport():
    def __init__(self, xmin=VP_X_MIN, ymin=VP_Y_MIN, xmax=VP_X_MAX, ymax=VP_Y_MAX):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

    def viewport_transform_scn(self, ponto_scn):
        """Transforma um ponto em coordenadas SCN (normalizadas, [-1,1]) para viewport.

        SCN: x em [-1, 1], y em [-1, 1]
        Viewport: x em [xmin, xmax], y em [ymin, ymax] (y invertido para tela)
        """
        x_scn, y_scn = ponto_scn

        x_vp = ((x_scn + 1) / 2) * (self.xmax - self.xmin) + self.xmin
        y_vp = (1 - (y_scn + 1) / 2) * (self.ymax - self.ymin) + self.ymin

        return x_vp, y_vp