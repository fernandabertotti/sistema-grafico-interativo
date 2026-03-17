from typing import List, Tuple

class ObjetoGrafico:
    """Classe base para todos os objetos do sistema"""
    def __init__(self, nome, pontos, tipo):
        self.nome: str = nome
        self.pontos: List[Tuple[int, int]] = pontos # Lista de tuplas [(x,y), ]
        self.tipo: str = tipo

class Ponto(ObjetoGrafico):
    # Um ponto tem apenas um par de coordenadas
    def __init__(self, nome, pontos):
        super().__init__(nome, pontos, "Ponto")

class Reta(ObjetoGrafico):
    # Uma reta tem apenas dois pontos
    def __init__(self, nome, pontos):
        super().__init__(nome, pontos, "Reta")

class Wireframe(ObjetoGrafico):
    # Um poligono (wireframe) tem N pontos interconectados
    def __init__(self, nome, pontos):
        super().__init__(nome, pontos, "Wireframe")
        

    