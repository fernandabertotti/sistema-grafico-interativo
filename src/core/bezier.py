"""Geração de pontos amostrados em curvas de Bézier cúbicas (blending functions).

Usa a forma matricial P(t) = T · M · G, onde:
  T = [t³  t²  t  1]
  M = matriz base de Bézier (4x4)
  G = [P1; P2; P3; P4] (pontos de controle, 4x2 em 2D)

Referência: aula 5.2 (Curvas Paramétricas em 2D — Bézier).
"""
import numpy as np

MATRIZ_BEZIER = np.array([
    [-1,  3, -3, 1],
    [ 3, -6,  3, 0],
    [-3,  3,  0, 0],
    [ 1,  0,  0, 0],
], dtype=float)


def gerar_pontos_segmento(p1, p2, p3, p4, passos):
    """Gera (passos+1) pontos amostrados em t ∈ [0,1] para UM segmento cúbico.

    Retorna lista de tuplas (x, y) em coordenadas do mundo.
    """
    G = np.array([p1, p2, p3, p4], dtype=float)  # shape (4, 2)
    MG = MATRIZ_BEZIER @ G                        # shape (4, 2)

    pontos = []
    for i in range(passos + 1):
        t = i / passos
        T = np.array([t ** 3, t ** 2, t, 1.0])
        p = T @ MG  # shape (2,)
        pontos.append((float(p[0]), float(p[1])))
    return pontos


def gerar_pontos_curva(pontos_controle, passos):
    """Gera pontos amostrados para uma curva de Bézier por partes, com continuidade G(0).

    `pontos_controle`: lista de tuplas (x, y) com 3n+1 pontos (n = nº de segmentos).
    Segmentos são formados por janelas de 4 pontos que se sobrepõem em 1:
      segmento 1: [0, 1, 2, 3]
      segmento 2: [3, 4, 5, 6]
      segmento i: [3i, 3i+1, 3i+2, 3i+3]

    Retorna lista de pontos amostrados (sem duplicar o ponto de junção entre segmentos).
    """
    if len(pontos_controle) < 4 or (len(pontos_controle) - 1) % 3 != 0:
        raise ValueError(
            f"Curva de Bézier precisa de 3n+1 pontos (4, 7, 10...); "
            f"recebidos: {len(pontos_controle)}"
        )

    n_segmentos = (len(pontos_controle) - 1) // 3
    resultado = []
    for i in range(n_segmentos):
        base = 3 * i
        p1, p2, p3, p4 = pontos_controle[base:base + 4]
        segmento = gerar_pontos_segmento(p1, p2, p3, p4, passos)
        if i == 0:
            resultado.extend(segmento)
        else:
            resultado.extend(segmento[1:])  # evita duplicar ponto de junção
    return resultado
