# src/core/window3d.py
import numpy as np
from src.utils.utils import STEP, PERCENTAGE


class Window3D:
    """Câmera para projeção paralela ortogonal.

    VRP: View Reference Point (primeiro ponto do algoritmo — ponto no plano de visão).
    VPN: View Plane Normal (ao fim do algoritmo é (0,0,1)).
    VUP: View Up Vector (define orientação vertical da câmera).
    """

    def __init__(self):
        self.vrp = [0.0, 0.0, 0.0]
        self.vpn = [0.0, 0.0, 1.0]
        self.vup = [0.0, 1.0, 0.0]
        self.umin = -400.0
        self.umax =  400.0
        self.vmin = -300.0
        self.vmax =  300.0
        self.min_size = 1.0

    def _axes(self):
        """Retorna (u, v, n) — eixos de visão normalizados."""
        n = np.array(self.vpn, dtype=float)
        n = n / np.linalg.norm(n)

        vup = np.array(self.vup, dtype=float)
        u = np.cross(vup, n)
        u_norm = np.linalg.norm(u)
        if u_norm < 1e-10:
            u = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
            u = u - np.dot(u, n) * n
        u = u / np.linalg.norm(u)

        v = np.cross(n, u)
        return u, v, n

    def generate_scn_3d(self, ponto_mundo):
        """Converte ponto 3D do mundo para SCN [-1,1] x [-1,1].

        Pipeline:
          1. T(-VRP): translada VRP para a origem
          2. R: rotaciona para alinhar eixos de visão com X,Y,Z (VPN → Z)
          3. Projeção ortogonal: descarta Z
          4. Normaliza para [-1,1]
        """
        x, y, z = ponto_mundo
        u, v, n = self._axes()
        vrp = np.array(self.vrp, dtype=float)

        p = np.array([x, y, z], dtype=float) - vrp
        x_vc = float(np.dot(p, u))
        y_vc = float(np.dot(p, v))

        half_u = (self.umax - self.umin) / 2.0
        half_v = (self.vmax - self.vmin) / 2.0
        return (x_vc / half_u, y_vc / half_v)

    def move_u(self, step=STEP):
        u, _, _ = self._axes()
        self.vrp = list(np.array(self.vrp) + u * step)

    def move_v(self, step=STEP):
        _, v, _ = self._axes()
        self.vrp = list(np.array(self.vrp) + v * step)

    def move_n(self, step=STEP):
        _, _, n = self._axes()
        self.vrp = list(np.array(self.vrp) + n * step)

    def zoom_in(self, percentage=PERCENTAGE):
        factor = percentage / 100.0
        new_u = (self.umax - self.umin) * (1 - factor)
        new_v = (self.vmax - self.vmin) * (1 - factor)
        if new_u <= self.min_size or new_v <= self.min_size:
            return
        du = (self.umax - self.umin) * factor / 2
        dv = (self.vmax - self.vmin) * factor / 2
        self.umin += du; self.umax -= du
        self.vmin += dv; self.vmax -= dv

    def zoom_out(self, percentage=PERCENTAGE):
        factor = percentage / 100.0
        du = (self.umax - self.umin) * factor / 2
        dv = (self.vmax - self.vmin) * factor / 2
        self.umin -= du; self.umax += du
        self.vmin -= dv; self.vmax += dv

    def _rotate_vector(self, vec, axis, angle_deg):
        """Rodrigues: rotaciona 'vec' em torno de 'axis' por 'angle_deg'."""
        k = np.array(axis, dtype=float)
        k = k / np.linalg.norm(k)
        v = np.array(vec, dtype=float)
        cos_a = np.cos(np.radians(angle_deg))
        sin_a = np.sin(np.radians(angle_deg))
        rotated = v * cos_a + np.cross(k, v) * sin_a + k * np.dot(k, v) * (1 - cos_a)
        return rotated / np.linalg.norm(rotated)

    def rotate_u(self, angulo_graus: float):
        u, _, _ = self._axes()
        self.vpn = list(self._rotate_vector(self.vpn, u, angulo_graus))
        self.vup = list(self._rotate_vector(self.vup, u, angulo_graus))

    def rotate_v(self, angulo_graus: float):
        _, v, _ = self._axes()
        self.vpn = list(self._rotate_vector(self.vpn, v, angulo_graus))
        self.vup = list(self._rotate_vector(self.vup, v, angulo_graus))

    def rotate_n(self, angulo_graus: float):
        _, _, n = self._axes()
        self.vup = list(self._rotate_vector(self.vup, n, angulo_graus))
