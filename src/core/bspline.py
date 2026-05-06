# src/core/bspline.py
"""Geração de pontos de B-Spline cúbica uniforme via Forward Differences.

Matriz base B-Spline (EQ. 5.25 dos slides):
  M_BS = (1/6) * [[-1,  3, -3,  1],
                   [ 3, -6,  3,  0],
                   [-3,  0,  3,  0],
                   [ 1,  4,  1,  0]]

Cada segmento Qi é definido por 4 pontos consecutivos:
  Pi-3, Pi-2, Pi-1, Pi  (janela deslizante de 1 em 1)

Com n pontos de controle (n >= 4), temos n-3 segmentos.

Forward Differences (EQ. 5.38 dos slides), com delta = 1/passos:
  f0      = d
  Δf0     = a*δ³ + b*δ² + c*δ
  Δ²f0    = 6a*δ³ + 2b*δ²
  Δ³f0    = 6a*δ³
"""
import numpy as np

MATRIZ_BS = (1.0 / 6.0) * np.array([
    [-1,  3, -3,  1],
    [ 3, -6,  3,  0],
    [-3,  0,  3,  0],
    [ 1,  4,  1,  0],
], dtype=float)


def _coeficientes_segmento(p0, p1, p2, p3):
    """Retorna os coeficientes (a, b, c, d) para x e y de um segmento B-Spline.

    G = [p0; p1; p2; p3]  →  C = M_BS · G  →  colunas: [a, b, c, d] para cada eixo.
    """
    G = np.array([p0, p1, p2, p3], dtype=float)  # shape (4, 2)
    C = MATRIZ_BS @ G                              # shape (4, 2): linhas = [a, b, c, d]
    return C  # C[0]=a, C[1]=b, C[2]=c, C[3]=d


def _forward_diff_inicial(a, b, c, d, delta):
    """Calcula o vetor de diferenças iniciais D = E(δ) · C  (EQ. 5.38/5.39).

    Retorna (f0, df0, d2f0, d3f0) para um único eixo (x ou y).
    """
    d3 = delta ** 3
    d2 = delta ** 2

    f0   = d
    df0  = a * d3 + b * d2 + c * delta
    d2f0 = 6 * a * d3 + 2 * b * d2
    d3f0 = 6 * a * d3
    return f0, df0, d2f0, d3f0


def gerar_pontos_segmento_bs(p0, p1, p2, p3, passos):
    """Gera (passos+1) pontos de um segmento B-Spline via Forward Differences.

    Algoritmo DesenhaCurvaFwdDiff dos slides (pág. 28):
      x  ← x  + Δx;   Δx  ← Δx  + Δ²x;   Δ²x ← Δ²x + Δ³x
      (idem para y)
    """
    C = _coeficientes_segmento(p0, p1, p2, p3)
    ax, bx, cx, dx = C[0, 0], C[1, 0], C[2, 0], C[3, 0]
    ay, by, cy, dy = C[0, 1], C[1, 1], C[2, 1], C[3, 1]

    delta = 1.0 / passos

    x,  dx_,  d2x, d3x = _forward_diff_inicial(ax, bx, cx, dx, delta)
    y,  dy_,  d2y, d3y = _forward_diff_inicial(ay, by, cy, dy, delta)

    pontos = [(x, y)]

    for _ in range(passos):          # itera passos vezes → passos+1 pontos no total
        x   += dx_;   dx_  += d2x;  d2x += d3x
        y   += dy_;   dy_  += d2y;  d2y += d3y
        pontos.append((x, y))

    return pontos


def gerar_pontos_bspline(pontos_controle, passos=100):
    """Gera todos os pontos amostrados de uma B-Spline cúbica uniforme.

    Janela deslizante de 1: segmento i usa pontos [i, i+1, i+2, i+3].
    Com n pontos de controle, gera n-3 segmentos.
    Requer n >= 4.
    """
    n = len(pontos_controle)
    if n < 4:
        raise ValueError(f"B-Spline precisa de pelo menos 4 pontos; recebidos: {n}")

    resultado = []
    for i in range(n - 3):
        p0, p1, p2, p3 = pontos_controle[i], pontos_controle[i+1], \
                          pontos_controle[i+2], pontos_controle[i+3]
        segmento = gerar_pontos_segmento_bs(p0, p1, p2, p3, passos)
        if i == 0:
            resultado.extend(segmento)
        else:
            resultado.extend(segmento[1:])  # evita duplicar ponto de junção

    return resultado