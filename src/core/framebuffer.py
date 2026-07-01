# src/core/framebuffer.py
"""Framebuffer proprio para rasterizacao (Trabalhos 2.1, 2.2 e 2.3).

Armazena a cor em um buffer RGB (linha-major, 3 bytes por pixel) e a
profundidade em um Z-buffer de ponto flutuante. Oferece rasterizacao de
linhas (Bresenham), trapezios, poligonos (scan-line), triangulos com
Z-buffer e triangulos com iluminacao de Phong por pixel.
"""
import numpy as np
from PyQt6.QtGui import QImage

from src.core.phong import calcular_phong


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
    # Rasterizador generico de triangulo com interpolacao de atributos
    # ------------------------------------------------------------------
    def _rasterizar_triangulo(self, p0, p1, p2, pixel_fn):
        """Varre um triangulo por scan-line interpolando atributos linearmente.

        Cada p_i e a tupla (x, y, atributos) onde `atributos` e um np.array.
        Para cada pixel interno chama pixel_fn(x_int, y_int, atributos_interp).
        """
        # Ordena os vertices por Y (A no topo, C na base).
        a, b, c = sorted([p0, p1, p2], key=lambda p: p[1])
        ya, yb, yc = a[1], b[1], c[1]

        def interp_aresta(y, topo, base):
            """Interpola (x, atributos) na altura y ao longo de topo->base."""
            x_t, y_t, at_t = topo
            x_b, y_b, at_b = base
            if y_b == y_t:
                t = 0.0
            else:
                t = (y - y_t) / (y_b - y_t)
            x = x_t + (x_b - x_t) * t
            at = at_t + (at_b - at_t) * t
            return x, at

        y_ini = int(np.ceil(ya))
        y_fim = int(np.floor(yc))
        for y in range(y_ini, y_fim + 1):
            if y < 0 or y >= self.height:
                continue
            # Aresta longa A->C sempre presente.
            x_long, at_long = interp_aresta(y, a, c)
            # Aresta curta: A->B na parte de cima, B->C na parte de baixo.
            if y < yb:
                x_curt, at_curt = interp_aresta(y, a, b)
            else:
                x_curt, at_curt = interp_aresta(y, b, c)

            # Ordena esquerda/direita.
            x_esq, at_esq = x_long, at_long
            x_dir, at_dir = x_curt, at_curt
            if x_esq > x_dir:
                x_esq, x_dir = x_dir, x_esq
                at_esq, at_dir = at_dir, at_esq

            largura = x_dir - x_esq
            x_ini = int(np.ceil(x_esq))
            x_fim = int(np.floor(x_dir))
            for x in range(x_ini, x_fim + 1):
                if x < 0 or x >= self.width:
                    continue
                if largura <= 1e-9:
                    t = 0.0
                else:
                    t = (x - x_esq) / largura
                atributos = at_esq + (at_dir - at_esq) * t
                pixel_fn(x, y, atributos)

    # ------------------------------------------------------------------
    # Trabalho 2.2 - Triangulo com Z-buffer
    # ------------------------------------------------------------------
    def draw_triangle_3d(self, v0, v1, v2, color=(0, 0, 0)):
        """Rasteriza um triangulo com interpolacao linear de Z e Z-buffer.

        v0/v1/v2 = (x_vp, y_vp, z_view), coordenadas ja em espaco de viewport
        (XY em pixels) e Z em espaco de camera.
        """
        def pixel_fn(x, y, atributos):
            self.draw_pixel_depth(x, y, atributos[0], color)

        p0 = (v0[0], v0[1], np.array([v0[2]], dtype=float))
        p1 = (v1[0], v1[1], np.array([v1[2]], dtype=float))
        p2 = (v2[0], v2[1], np.array([v2[2]], dtype=float))
        self._rasterizar_triangulo(p0, p1, p2, pixel_fn)

    # ------------------------------------------------------------------
    # Trabalho 2.3 - Triangulo com iluminacao de Phong por pixel
    # ------------------------------------------------------------------
    def draw_triangle_phong(self, v0, v1, v2, n0, n1, n2,
                            material, luz, olho, luz_ambiente):
        """Rasteriza um triangulo calculando Phong por pixel.

        Interpola posicao no mundo, profundidade e a normal por vertice; para
        cada pixel calcula a cor com o modelo de Phong e aplica o Z-buffer.

        v0/v1/v2 = (x_vp, y_vp, z_view, x_world, y_world, z_world)
        n0/n1/n2 = normais por vertice (mesmo espaco de `olho`/`luz`).
        """
        def montar(v, nrm):
            # atributos = [z_view, xw, yw, zw, nx, ny, nz]
            at = np.array([v[2], v[3], v[4], v[5],
                           nrm[0], nrm[1], nrm[2]], dtype=float)
            return (v[0], v[1], at)

        def pixel_fn(x, y, atributos):
            z_view = atributos[0]
            ponto = (atributos[1], atributos[2], atributos[3])
            normal = (atributos[4], atributos[5], atributos[6])
            cor = calcular_phong(ponto, normal, olho, luz, material, luz_ambiente)
            cor255 = (int(cor[0] * 255), int(cor[1] * 255), int(cor[2] * 255))
            self.draw_pixel_depth(x, y, z_view, cor255)

        self._rasterizar_triangulo(montar(v0, n0), montar(v1, n1),
                                   montar(v2, n2), pixel_fn)

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
