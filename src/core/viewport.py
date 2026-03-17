# src/core/transform.py

from src.utils.utils import VP_X_MIN, VP_Y_MIN, VP_X_MAX, VP_Y_MAX
from geometry import Ponto

class Viewport():
    def __init__(self, xmin = VP_X_MIN, ymin = VP_Y_MIN, xmax = VP_X_MAX, ymax = VP_Y_MAX):
        self.xmin = xmin
        self.ymin = ymin 
        self.xmax = xmax
        self.ymax = ymax

    def viewport_transform(self, point, window):
        # Realiza a transformada de Viewport sobre um ponto
        x_w, y_w = point

        # coordenadaViewport = (Proporção_no_Mundo) * (Largura_da_Tela) + (coordenada_minimo_da_Tela)
        x_vp = ((x_w - window.xmin) / (window.xmax - window.xmin)) * (self.xmax - self.xmin) + self.xmin
        y_vp = (1 - (y_w - window.ymin) / (window.ymax - window.ymin)) * (self.ymax - self.ymin) + self.ymin

        return x_vp, y_vp