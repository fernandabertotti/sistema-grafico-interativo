# src/core/framebuffer.py
"""Framebuffer proprio para rasterizacao (Trabalhos 2.1, 2.2 e 2.3).

Armazena a cor em um buffer RGB (linha-major, 3 bytes por pixel) e a
profundidade em um Z-buffer de ponto flutuante. Oferece rasterizacao de
linhas (Bresenham), trapezios, poligonos (scan-line), triangulos com
Z-buffer e triangulos com iluminacao de Phong por pixel.
"""
import numpy as np
from PyQt6.QtGui import QImage

from src.core.phong import calcular_phong, calcular_phong_array


class Framebuffer:
    def __init__(self, width: int, height: int):
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        # Buffer de cor: (height, width, 3) uint8 em ordem RGB, linha-major.
        self.buffer = np.empty((self.height, self.width, 3), dtype=np.uint8)
        # Z-buffer: (height, width) float, inicializado com +infinito.
        self.zbuffer = np.empty((self.height, self.width), dtype=np.float64)
        # Quando False, draw_pixel_depth ignora a checagem de profundidade.
        self.usar_zbuffer = True
        self.clear()

    # ------------------------------------------------------------------
    # Operacoes basicas
    # ------------------------------------------------------------------
    def clear(self, color=(255, 255, 255)):
        """Limpa a cor de fundo e reseta o Z-buffer para +infinito."""
        self.buffer[:, :, 0] = int(color[0])
        self.buffer[:, :, 1] = int(color[1])
        self.buffer[:, :, 2] = int(color[2])
        self.zbuffer[:, :] = np.inf

    def draw_pixel(self, x, y, color=(0, 0, 0)):
        """Desenha um pixel sem checar profundidade."""
        xi = int(round(x))
        yi = int(round(y))
        if 0 <= xi < self.width and 0 <= yi < self.height:
            self.buffer[yi, xi, 0] = int(color[0])
            self.buffer[yi, xi, 1] = int(color[1])
            self.buffer[yi, xi, 2] = int(color[2])

    def draw_pixel_depth(self, x, y, z, color=(0, 0, 0)):
        """Desenha um pixel usando o Z-buffer (so pinta se z estiver mais proximo)."""
        xi = int(round(x))
        yi = int(round(y))
        if 0 <= xi < self.width and 0 <= yi < self.height:
            if (not self.usar_zbuffer) or z < self.zbuffer[yi, xi]:
                self.zbuffer[yi, xi] = z
                self.buffer[yi, xi, 0] = int(color[0])
                self.buffer[yi, xi, 1] = int(color[1])
                self.buffer[yi, xi, 2] = int(color[2])

    # ------------------------------------------------------------------
    # Trabalho 2.1 - Bresenham, trapezio e poligono
    # ------------------------------------------------------------------
    def draw_line(self, x0, y0, x1, y1, color=(0, 0, 0)):
        """Rasteriza uma linha pelo algoritmo de Bresenham (inteiro)."""
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
        """Rasteriza um trapezio alinhado ao eixo X, varrendo por scanlines.

        (x0_top, x1_top) sao os limites esquerdo/direito no topo (y_top);
        (x0_bot, x1_bot) sao os limites na base (y_bot). As arestas laterais
        sao interpoladas linearmente ao longo de Y.
        """
        y_top = int(round(y_top))
        y_bot = int(round(y_bot))
        if y_top == y_bot:
            return
        # Garante y_top acima de y_bot.
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
            for x in range(xi, xf + 1):
                self.draw_pixel(x, y, color)

    def draw_polygon(self, vertices, color=(0, 0, 0)):
        """Preenche um poligono por varredura de scan-line (Active Edge Table).

        Suporta poligonos convexos e concavos simples. `vertices` e uma lista
        de tuplas (x, y).
        """
        if len(vertices) < 3:
            return
        n = len(vertices)
        ys = [v[1] for v in vertices]
        y_min = int(np.floor(min(ys)))
        y_max = int(np.ceil(max(ys)))

        for y in range(y_min, y_max + 1):
            yc = y + 0.5  # centro do scanline
            intersecoes = []
            for i in range(n):
                x0, y0 = vertices[i][0], vertices[i][1]
                x1, y1 = vertices[(i + 1) % n][0], vertices[(i + 1) % n][1]
                if y0 == y1:
                    continue  # aresta horizontal nao gera intersecao
                if min(y0, y1) <= yc < max(y0, y1):
                    t = (yc - y0) / (y1 - y0)
                    intersecoes.append(x0 + t * (x1 - x0))
            intersecoes.sort()
            # Preenche entre pares de intersecoes (regra par/impar).
            for k in range(0, len(intersecoes) - 1, 2):
                xa = int(np.ceil(intersecoes[k]))
                xb = int(np.floor(intersecoes[k + 1]))
                for x in range(xa, xb + 1):
                    self.draw_pixel(x, y, color)

    # ------------------------------------------------------------------
    # Rasterizador vetorizado de triangulo (barycentric por bounding box)
    # ------------------------------------------------------------------
    def _preparar_raster(self, x0, y0, x1, y1, x2, y2):
        """Prepara a rasterizacao vetorizada de um triangulo.

        Retorna (minx, miny, maxx, maxy, w0, w1, w2, dentro) onde w0/w1/w2 sao
        as coordenadas baricentricas de cada pixel da bounding box e `dentro` e
        a mascara booleana dos pixels internos ao triangulo. Retorna None se o
        triangulo estiver fora da tela ou for degenerado.
        """
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
        gx, gy = np.meshgrid(xs, ys)  # (H, W)

        w0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / denom
        w1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / denom
        w2 = 1.0 - w0 - w1
        dentro = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        return minx, miny, maxx, maxy, w0, w1, w2, dentro

    def _mascara_profundidade(self, z, dentro, miny, maxy, minx, maxx):
        """Combina a mascara interna com o teste de Z-buffer e retorna a fatia."""
        sub_z = self.zbuffer[miny:maxy + 1, minx:maxx + 1]
        if self.usar_zbuffer:
            passa = dentro & (z < sub_z)
        else:
            passa = dentro
        return passa, sub_z

    # ------------------------------------------------------------------
    # Trabalho 2.2 - Triangulo com Z-buffer (cor plana)
    # ------------------------------------------------------------------
    def draw_triangle_3d(self, v0, v1, v2, color=(0, 0, 0)):
        """Rasteriza um triangulo com interpolacao linear de Z e Z-buffer.

        v0/v1/v2 = (x_vp, y_vp, z_view), coordenadas ja em espaco de viewport
        (XY em pixels) e Z em espaco de camera.
        """
        prep = self._preparar_raster(v0[0], v0[1], v1[0], v1[1], v2[0], v2[1])
        if prep is None:
            return
        minx, miny, maxx, maxy, w0, w1, w2, dentro = prep

        z = w0 * v0[2] + w1 * v1[2] + w2 * v2[2]
        passa, sub_z = self._mascara_profundidade(z, dentro, miny, maxy, minx, maxx)
        sub_b = self.buffer[miny:maxy + 1, minx:maxx + 1]

        sub_z[passa] = z[passa]
        sub_b[passa] = np.array([int(color[0]), int(color[1]), int(color[2])],
                                dtype=np.uint8)

    # ------------------------------------------------------------------
    # Trabalho 2.3 - Triangulo com iluminacao de Phong por pixel
    # ------------------------------------------------------------------
    def draw_triangle_phong(self, v0, v1, v2, n0, n1, n2,
                            material, luz, olho, luz_ambiente):
        """Rasteriza um triangulo calculando Phong por pixel (vetorizado).

        Interpola posicao no mundo, profundidade e a normal por vertice; calcula
        a cor de Phong para todos os pixels validos de uma vez e aplica Z-buffer.

        v0/v1/v2 = (x_vp, y_vp, z_view, x_world, y_world, z_world)
        n0/n1/n2 = normais por vertice (mesmo espaco de `olho`/`luz`).
        """
        prep = self._preparar_raster(v0[0], v0[1], v1[0], v1[1], v2[0], v2[1])
        if prep is None:
            return
        minx, miny, maxx, maxy, w0, w1, w2, dentro = prep

        z = w0 * v0[2] + w1 * v1[2] + w2 * v2[2]
        passa, sub_z = self._mascara_profundidade(z, dentro, miny, maxy, minx, maxx)
        if not passa.any():
            return
        sub_b = self.buffer[miny:maxy + 1, minx:maxx + 1]

        # Pesos baricentricos apenas dos pixels que passam.
        b0 = w0[passa]; b1 = w1[passa]; b2 = w2[passa]

        # Interpola posicao no mundo e normal por pixel.
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

        sub_z[passa] = z[passa]
        sub_b[passa] = (cores * 255).astype(np.uint8)

    # ------------------------------------------------------------------
    # Exibicao
    # ------------------------------------------------------------------
    def to_qimage(self) -> QImage:
        """Converte o buffer de cor para um QImage exibivel."""
        dados = self.buffer.tobytes()
        imagem = QImage(dados, self.width, self.height,
                        self.width * 3, QImage.Format.Format_RGB888)
        # .copy() desvincula o QImage do buffer temporario (evita dangling).
        return imagem.copy()
