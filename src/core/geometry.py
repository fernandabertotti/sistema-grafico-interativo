# src/core/geometry.py
from typing import List, Tuple

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
    def __init__(self, nome: str, segmentos: List[Tuple["Ponto3D", "Ponto3D"]], cor: str = "#000000"):
        self.nome = nome
        self.segmentos = segmentos  # List[Tuple[Ponto3D, Ponto3D]]
        self.tipo = "Objeto3D"
        self.cor = cor


class SuperficieBSpline3D:
    """Superficie bicubica B-Spline uniforme definida por matriz de pontos 3D."""
    def __init__(self, nome: str, matriz_controle: List[List[Ponto3D]], cor: str = "#000000", passos: int = 10):
        self.nome = nome
        self.matriz_controle = matriz_controle
        self.tipo = "SuperficieBSpline3D"
        self.cor = cor
        self.passos = int(passos)
