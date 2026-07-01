# src/core/geometry.py
from typing import List, Tuple
import numpy as np

class ObjetoGrafico:
    """Classe base para todos os objetos do sistema"""
    def __init__(self, nome, pontos, tipo, cor="#000000"):
        self.nome: str = nome
        self.pontos: List[Tuple[int, int]] = pontos # Lista de tuplas [(x,y), ]
        self.tipo: str = tipo
        self.cor: str = cor 

class Ponto(ObjetoGrafico):
    def __init__(self, nome, pontos, cor="#000000"):
        super().__init__(nome, pontos, "Ponto", cor)

class Reta(ObjetoGrafico):
    def __init__(self, nome, pontos, cor="#000000"):
        super().__init__(nome, pontos, "Reta", cor)

class Wireframe(ObjetoGrafico):
    def __init__(self, nome, pontos, cor="#000000", preenchido=False):
        super().__init__(nome, pontos, "Wireframe", cor)
        self.preenchido = preenchido


class Curva2D(ObjetoGrafico):
    """Curva de Bézier cúbica por partes. `pontos` são os pontos de controle (3n+1)."""
    def __init__(self, nome, pontos, cor="#000000"):
        super().__init__(nome, pontos, "Curva2D", cor)

class BSpline2D(ObjetoGrafico):
    """B-Spline cúbica uniforme por Forward Differences. `pontos` são os pontos de controle (>= 4)."""
    def __init__(self, nome, pontos, cor="#000000"):
        super().__init__(nome, pontos, "BSpline2D", cor)


class Ponto3D:
    def __init__(self, x: float, y: float, z: float):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


# Não herda ObjetoGrafico: base usa pontos 2D; Canvas identifica por obj.tipo (string).
class Objeto3D:
    def __init__(self, nome: str, segmentos: List[Tuple["Ponto3D", "Ponto3D"]],
                 cor: str = "#000000", triangulos=None):
        self.nome = nome
        self.segmentos = segmentos
        self.tipo = "Objeto3D"
        self.cor = cor
        self.triangulos = triangulos


def triangulo_flat(p0, p1, p2, centro=None):
    a = np.array(p0, dtype=float)
    b = np.array(p1, dtype=float)
    c = np.array(p2, dtype=float)
    n = np.cross(b - a, c - a)
    norma = np.linalg.norm(n)
    n = np.array([0.0, 0.0, 1.0]) if norma < 1e-9 else n / norma
    if centro is not None:
        meio = (a + b + c) / 3.0
        if np.dot(n, meio - np.array(centro, dtype=float)) < 0:
            n = -n
    nt = (float(n[0]), float(n[1]), float(n[2]))
    vs = [(float(p0[0]), float(p0[1]), float(p0[2])),
          (float(p1[0]), float(p1[1]), float(p1[2])),
          (float(p2[0]), float(p2[1]), float(p2[2]))]
    return {'v': vs, 'n': [nt, nt, nt]}


def arestas_de_triangulos(triangulos):
    vistos = set()
    segmentos = []
    for tri in triangulos:
        vs = tri['v']
        for i, j in ((0, 1), (1, 2), (2, 0)):
            va, vb = vs[i], vs[j]
            ca = tuple(round(c, 4) for c in va)
            cb = tuple(round(c, 4) for c in vb)
            chave = (ca, cb) if ca <= cb else (cb, ca)
            if chave in vistos:
                continue
            vistos.add(chave)
            segmentos.append((Ponto3D(*va), Ponto3D(*vb)))
    return segmentos


class SuperficieBSpline3D:
    """Superficie bicubica B-Spline uniforme definida por matriz de pontos 3D."""
    def __init__(self, nome: str, matriz_controle: List[List[Ponto3D]], cor: str = "#000000", passos: int = 10):
        self.nome = nome
        self.matriz_controle = matriz_controle
        self.tipo = "SuperficieBSpline3D"
        self.cor = cor
        self.passos = int(passos)
