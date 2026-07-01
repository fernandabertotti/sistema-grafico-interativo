"""Superficies bicubicas B-Spline por Forward Differences."""
import numpy as np

from src.core.bspline import MATRIZ_BS
from src.core.geometry import Ponto3D


def _coeficientes_segmento_3d(p0, p1, p2, p3):
    G = np.array([
        [p0.x, p0.y, p0.z],
        [p1.x, p1.y, p1.z],
        [p2.x, p2.y, p2.z],
        [p3.x, p3.y, p3.z],
    ], dtype=float)
    return MATRIZ_BS @ G


def _forward_diff_inicial(a, b, c, d, delta):
    d3 = delta ** 3
    d2 = delta ** 2
    f0 = d
    df0 = a * d3 + b * d2 + c * delta
    d2f0 = 6 * a * d3 + 2 * b * d2
    d3f0 = 6 * a * d3
    return f0, df0, d2f0, d3f0


def gerar_pontos_segmento_bspline_3d(p0, p1, p2, p3, passos):
    """Gera pontos de um segmento B-Spline 3D usando Forward Differences."""
    if passos <= 0:
        raise ValueError("A quantidade de passos deve ser maior que zero.")

    C = _coeficientes_segmento_3d(p0, p1, p2, p3)
    delta = 1.0 / passos

    f, df, d2f, d3f = [], [], [], []
    for eixo in range(3):
        valores = _forward_diff_inicial(
            C[0, eixo], C[1, eixo], C[2, eixo], C[3, eixo], delta)
        f.append(valores[0])
        df.append(valores[1])
        d2f.append(valores[2])
        d3f.append(valores[3])

    pontos = [Ponto3D(f[0], f[1], f[2])]
    for _ in range(passos):
        for eixo in range(3):
            f[eixo] += df[eixo]
            df[eixo] += d2f[eixo]
            d2f[eixo] += d3f[eixo]
        pontos.append(Ponto3D(f[0], f[1], f[2]))

    return pontos


def validar_matriz_controle(matriz):
    linhas = len(matriz)
    if linhas < 4 or linhas > 20:
        raise ValueError("A matriz deve ter entre 4 e 20 linhas.")

    colunas = len(matriz[0]) if linhas else 0
    if colunas < 4 or colunas > 20:
        raise ValueError("A matriz deve ter entre 4 e 20 colunas.")

    for linha in matriz:
        if len(linha) != colunas:
            raise ValueError("Todas as linhas da matriz devem ter a mesma quantidade de pontos.")
        for ponto in linha:
            if not isinstance(ponto, Ponto3D):
                raise ValueError("A matriz deve conter apenas pontos 3D.")

    return linhas, colunas


def gerar_linhas_superficie_bspline(matriz_controle, passos=10):
    """Subdivide uma grade mxn em patches 4x4 e retorna polilinhas da superficie.

    Cada patch bicubico usa uma janela 4x4 da matriz de controle. As curvas
    isoparametricas sao geradas em duas passagens de Forward Differences.
    """
    linhas_count, colunas_count = validar_matriz_controle(matriz_controle)

    polilinhas = []
    for i in range(linhas_count - 3):
        for j in range(colunas_count - 3):
            patch = [linha[j:j + 4] for linha in matriz_controle[i:i + 4]]

            curvas_v_por_linha = [
                gerar_pontos_segmento_bspline_3d(*patch[linha], passos)
                for linha in range(4)
            ]
            for v_idx in range(passos + 1):
                controle_u = [curvas_v_por_linha[linha][v_idx] for linha in range(4)]
                polilinhas.append(gerar_pontos_segmento_bspline_3d(*controle_u, passos))

            curvas_u_por_coluna = [
                gerar_pontos_segmento_bspline_3d(
                    patch[0][col], patch[1][col], patch[2][col], patch[3][col], passos)
                for col in range(4)
            ]
            for u_idx in range(passos + 1):
                controle_v = [curvas_u_por_coluna[col][u_idx] for col in range(4)]
                polilinhas.append(gerar_pontos_segmento_bspline_3d(*controle_v, passos))

    return polilinhas


def polilinhas_para_segmentos(polilinhas):
    segmentos = []
    for linha in polilinhas:
        for idx in range(len(linha) - 1):
            segmentos.append((linha[idx], linha[idx + 1]))
    return segmentos


def gerar_segmentos_superficie_bspline(matriz_controle, passos=10):
    return polilinhas_para_segmentos(
        gerar_linhas_superficie_bspline(matriz_controle, passos))


def _gerar_grade_patch(patch, passos):
    curvas_v = [gerar_pontos_segmento_bspline_3d(*patch[linha], passos)
                for linha in range(4)]
    grade = [[None] * (passos + 1) for _ in range(passos + 1)]
    for v_idx in range(passos + 1):
        controle_u = [curvas_v[linha][v_idx] for linha in range(4)]
        curva_u = gerar_pontos_segmento_bspline_3d(*controle_u, passos)
        for u_idx in range(passos + 1):
            grade[u_idx][v_idx] = curva_u[u_idx]
    return grade


def gerar_triangulos_superficie_bspline(matriz_controle, passos=10):
    linhas_count, colunas_count = validar_matriz_controle(matriz_controle)
    triangulos = []

    for i in range(linhas_count - 3):
        for j in range(colunas_count - 3):
            patch = [linha[j:j + 4] for linha in matriz_controle[i:i + 4]]
            grade = _gerar_grade_patch(patch, passos)

            n_u = len(grade)
            n_v = len(grade[0])
            pts = np.array([[[p.x, p.y, p.z] for p in linha] for linha in grade])

            normais = np.zeros_like(pts)
            for a in range(n_u):
                for b in range(n_v):
                    du = pts[min(a + 1, n_u - 1), b] - pts[max(a - 1, 0), b]
                    dv = pts[a, min(b + 1, n_v - 1)] - pts[a, max(b - 1, 0)]
                    nrm = np.cross(du, dv)
                    norma = np.linalg.norm(nrm)
                    normais[a, b] = nrm / norma if norma > 1e-9 else (0.0, 0.0, 1.0)

            for a in range(n_u - 1):
                for b in range(n_v - 1):
                    v00 = tuple(pts[a, b]);       n00 = tuple(normais[a, b])
                    v10 = tuple(pts[a + 1, b]);   n10 = tuple(normais[a + 1, b])
                    v11 = tuple(pts[a + 1, b + 1]); n11 = tuple(normais[a + 1, b + 1])
                    v01 = tuple(pts[a, b + 1]);   n01 = tuple(normais[a, b + 1])
                    triangulos.append({'v': [v00, v10, v11], 'n': [n00, n10, n11]})
                    triangulos.append({'v': [v00, v11, v01], 'n': [n00, n11, n01]})

    return triangulos
