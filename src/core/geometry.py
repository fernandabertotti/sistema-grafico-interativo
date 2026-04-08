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