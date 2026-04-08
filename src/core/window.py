# src/core/window.py
import numpy as np
from src.utils.utils import W_X_MIN, W_Y_MIN, W_Y_MAX, W_X_MAX, STEP, PERCENTAGE


class Window():
    def __init__(self, xmin=W_X_MIN, ymin=W_Y_MIN, xmax=W_X_MAX, ymax=W_Y_MAX):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.angulo = 0.0  # Ângulo de rotação da window (graus)
        self.min_size = 1.0

    @property
    def center(self):
        """Retorna o center da window."""
        return ((self.xmin + self.xmax) / 2, (self.ymin + self.ymax) / 2)

    @property
    def width(self):
        return self.xmax - self.xmin

    @property
    def hight(self):
        return self.ymax - self.ymin

    def _vetor_up(self):
        """Retorna o vetor 'para cima' considerando a rotação da window."""
        rad = np.radians(self.angulo)
        return (-np.sin(rad), np.cos(rad))

    def _vetor_right(self):
        """Retorna o vetor 'para direita' considerando a rotação da window."""
        rad = np.radians(self.angulo)
        return (np.cos(rad), np.sin(rad))

    # --- PANNING (relativo ao "up" do usuário) --- #
    def up(self, step=STEP):
        vx, vy = self._vetor_up()
        self.xmin += vx * step
        self.xmax += vx * step
        self.ymin += vy * step
        self.ymax += vy * step

    def down(self, step=STEP):
        vx, vy = self._vetor_up()
        self.xmin -= vx * step
        self.xmax -= vx * step
        self.ymin -= vy * step
        self.ymax -= vy * step

    def right(self, step=STEP):
        vx, vy = self._vetor_right()
        self.xmin += vx * step
        self.xmax += vx * step
        self.ymin += vy * step
        self.ymax += vy * step

    def left(self, step=STEP):
        vx, vy = self._vetor_right()
        self.xmin -= vx * step
        self.xmax -= vx * step
        self.ymin -= vy * step
        self.ymax -= vy * step

    # --- ZOOM --- #
    def zoom_in(self, percentage=PERCENTAGE):
        factor = percentage / 100
        new_width = self.width * (1 - factor)
        new_height = self.hight * (1 - factor)

        if new_width <= self.min_size or new_height <= self.min_size:
            return

        dx = self.width * factor / 2
        dy = self.hight * factor / 2
        self.xmin += dx
        self.xmax -= dx
        self.ymin += dy
        self.ymax -= dy

    def zoom_out(self, percentage=PERCENTAGE):
        factor = percentage / 100
        dx = self.width * factor / 2
        dy = self.hight * factor / 2
        self.xmin -= dx
        self.xmax += dx
        self.ymin -= dy
        self.ymax += dy

    # --- ROTAÇÃO --- #
    def rotate(self, angulo_graus):
        """Rotaciona a window pelo ângulo dado (acumula)."""
        self.angulo += angulo_graus

    def generate_scn(self, ponto_mundo):
        """Converte um ponto do mundo (WC) para coordenadas SCN (normalizadas)."""
        cx, cy = self.center
        x, y = ponto_mundo

        # 1. Transladar center da window para origem
        x_t = x - cx
        y_t = y - cy

        # 2. Rotacionar na direção inversa (desfazer rotação da window)
        rad = np.radians(-self.angulo)
        cos_a = np.cos(rad)
        sin_a = np.sin(rad)
        x_r = x_t * cos_a - y_t * sin_a
        y_r = x_t * sin_a + y_t * cos_a

        # 3. Normalizar para [-1, 1]
        half_w = self.width / 2
        half_h = self.hight / 2

        x_scn = x_r / half_w
        y_scn = y_r / half_h

        return (x_scn, y_scn)