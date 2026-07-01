import numpy as np
from PyQt6.QtGui import QImage

from src.core.phong import calcular_phong, calcular_phong_array


class Framebuffer:
    def __init__(self, width: int, height: int):
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self.buffer = np.empty((self.height, self.width, 4), dtype=np.uint8)
        self.zbuffer = np.empty((self.height, self.width), dtype=np.float64)
        self.usar_zbuffer = True
        self.clear(transparente=True)

    def clear(self, color=(255, 255, 255), transparente=False):
        if transparente:
            self.buffer[:, :, :] = 0
        else:
            self.buffer[:, :, 0] = int(color[0])
            self.buffer[:, :, 1] = int(color[1])
            self.buffer[:, :, 2] = int(color[2])
            self.buffer[:, :, 3] = 255
        self.zbuffer[:, :] = np.inf

    def draw_pixel(self, x, y, color=(0, 0, 0)):
        xi = int(round(x))
        yi = int(round(y))
        if 0 <= xi < self.width and 0 <= yi < self.height:
            self.buffer[yi, xi, 0] = int(color[0])
            self.buffer[yi, xi, 1] = int(color[1])
            self.buffer[yi, xi, 2] = int(color[2])
            self.buffer[yi, xi, 3] = 255

    def draw_pixel_depth(self, x, y, z, color=(0, 0, 0)):
        xi = int(round(x))
        yi = int(round(y))
        if 0 <= xi < self.width and 0 <= yi < self.height:
            if (not self.usar_zbuffer) or z < self.zbuffer[yi, xi]:
                self.zbuffer[yi, xi] = z
                self.buffer[yi, xi, 0] = int(color[0])
                self.buffer[yi, xi, 1] = int(color[1])
                self.buffer[yi, xi, 2] = int(color[2])
                self.buffer[yi, xi, 3] = 255

    def draw_line(self, x0, y0, x1, y1, color=(0, 0, 0)):
        x0 = int(round(x0)); y0 = int(round(y0))
        x1 = int(round(x1)); y1 = int(round(y1))

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            self.draw_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def draw_trapezoid(self, x0_top, x1_top, y_top,
                       x0_bot, x1_bot, y_bot, color=(0, 0, 0)):
        y_top = int(round(y_top))
        y_bot = int(round(y_bot))
        if y_top == y_bot:
            return
        if y_top > y_bot:
            y_top, y_bot = y_bot, y_top
            x0_top, x0_bot = x0_bot, x0_top
            x1_top, x1_bot = x1_bot, x1_top

        altura = float(y_bot - y_top)
        for y in range(y_top, y_bot + 1):
            t = (y - y_top) / altura
            x_esq = x0_top + (x0_bot - x0_top) * t
            x_dir = x1_top + (x1_bot - x1_top) * t
            xi = int(round(min(x_esq, x_dir)))
            xf = int(round(max(x_esq, x_dir)))
            self.draw_line(xi, y, xf, y, color)

    def _intersecoes_scanline(self, vertices, yv):
        n = len(vertices)
        xs = []
        for i in range(n):
            x0, y0 = vertices[i][0], vertices[i][1]
            x1, y1 = vertices[(i + 1) % n][0], vertices[(i + 1) % n][1]
            if y0 == y1:
                continue
            if min(y0, y1) <= yv < max(y0, y1):
                t = (yv - y0) / (y1 - y0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        return xs

    def draw_polygon(self, vertices, color=(0, 0, 0)):
        if len(vertices) < 3:
            return
        ys = [v[1] for v in vertices]
        y_min = int(np.floor(min(ys)))
        y_max = int(np.ceil(max(ys)))

        for y in range(y_min, y_max):
            topo = self._intersecoes_scanline(vertices, float(y))
            base = self._intersecoes_scanline(vertices, float(y + 1))
            if len(topo) == len(base) and len(topo) % 2 == 0 and topo:
                for k in range(0, len(topo), 2):
                    self.draw_trapezoid(topo[k], topo[k + 1], y,
                                        base[k], base[k + 1], y + 1, color)
            else:
                meio = self._intersecoes_scanline(vertices, y + 0.5)
                for k in range(0, len(meio) - 1, 2):
                    xa = int(np.ceil(meio[k]))
                    xb = int(np.floor(meio[k + 1]))
                    self.draw_line(xa, y, xb, y, color)

    def _preparar_raster(self, x0, y0, x1, y1, x2, y2):
        minx = max(0, int(np.floor(min(x0, x1, x2))))
        maxx = min(self.width - 1, int(np.ceil(max(x0, x1, x2))))
        miny = max(0, int(np.floor(min(y0, y1, y2))))
        maxy = min(self.height - 1, int(np.ceil(max(y0, y1, y2))))
        if minx > maxx or miny > maxy:
            return None

        denom = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(denom) < 1e-9:
            return None

        xs = np.arange(minx, maxx + 1)
        ys = np.arange(miny, maxy + 1)
        gx, gy = np.meshgrid(xs, ys)

        w0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / denom
        w1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / denom
        w2 = 1.0 - w0 - w1
        dentro = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        return minx, miny, maxx, maxy, w0, w1, w2, dentro

    def _mascara_profundidade(self, z, dentro, miny, maxy, minx, maxx):
        sub_z = self.zbuffer[miny:maxy + 1, minx:maxx + 1]
        if self.usar_zbuffer:
            passa = dentro & (z < sub_z)
        else:
            passa = dentro
        return passa, sub_z

    def draw_triangle_3d(self, v0, v1, v2, color=(0, 0, 0)):
        prep = self._preparar_raster(v0[0], v0[1], v1[0], v1[1], v2[0], v2[1])
        if prep is None:
            return
        minx, miny, maxx, maxy, w0, w1, w2, dentro = prep

        z = w0 * v0[2] + w1 * v1[2] + w2 * v2[2]
        passa, sub_z = self._mascara_profundidade(z, dentro, miny, maxy, minx, maxx)
        sub_b = self.buffer[miny:maxy + 1, minx:maxx + 1]

        sub_z[passa] = z[passa]
        sub_b[passa] = np.array([int(color[0]), int(color[1]), int(color[2]), 255],
                                dtype=np.uint8)

    def draw_triangle_phong(self, v0, v1, v2, n0, n1, n2,
                            material, luz, olho, luz_ambiente):
        prep = self._preparar_raster(v0[0], v0[1], v1[0], v1[1], v2[0], v2[1])
        if prep is None:
            return
        minx, miny, maxx, maxy, w0, w1, w2, dentro = prep

        z = w0 * v0[2] + w1 * v1[2] + w2 * v2[2]
        passa, sub_z = self._mascara_profundidade(z, dentro, miny, maxy, minx, maxx)
        if not passa.any():
            return
        sub_b = self.buffer[miny:maxy + 1, minx:maxx + 1]

        b0 = w0[passa]; b1 = w1[passa]; b2 = w2[passa]

        px = b0 * v0[3] + b1 * v1[3] + b2 * v2[3]
        py = b0 * v0[4] + b1 * v1[4] + b2 * v2[4]
        pz = b0 * v0[5] + b1 * v1[5] + b2 * v2[5]
        nx = b0 * n0[0] + b1 * n1[0] + b2 * n2[0]
        ny = b0 * n0[1] + b1 * n1[1] + b2 * n2[1]
        nz = b0 * n0[2] + b1 * n1[2] + b2 * n2[2]

        pontos = np.stack([px, py, pz], axis=1)
        normais = np.stack([nx, ny, nz], axis=1)
        cores = calcular_phong_array(pontos, normais, olho, luz,
                                     material, luz_ambiente)

        rgba = np.empty((cores.shape[0], 4), dtype=np.uint8)
        rgba[:, :3] = (cores * 255).astype(np.uint8)
        rgba[:, 3] = 255

        sub_z[passa] = z[passa]
        sub_b[passa] = rgba

    def to_qimage(self) -> QImage:
        dados = self.buffer.tobytes()
        imagem = QImage(dados, self.width, self.height,
                        self.width * 4, QImage.Format.Format_RGBA8888)
        return imagem.copy()
