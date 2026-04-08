# src/core/transform.py
import numpy as np
from typing import List, Tuple


class Transform:
    """Classe responsável por transformações 2D usando coordenadas homogêneas."""

    @staticmethod
    def translation_matrix(dx: float, dy: float) -> np.ndarray:
        """Retorna a matriz de translação em coordenadas homogêneas."""
        return np.array([[1,  0,  0],
                         [0,  1,  0],
                         [dx, dy, 1]])

    @staticmethod
    def scaling_matrix(sx: float, sy: float) -> np.ndarray:
        """Retorna a matriz de escalonamento em coordenadas homogêneas."""
        return np.array([[sx, 0,  0],
                         [0,  sy, 0],
                         [0,  0,  1]])

    @staticmethod
    def rotation_matrix(angle_degrees: float) -> np.ndarray:
        """Retorna a matriz de rotação em coordenadas homogêneas (em torno da origem)."""
        angle_rad = np.radians(angle_degrees)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        return np.array([[cos_a,  sin_a, 0],
                         [-sin_a, cos_a, 0],
                         [0,      0,     1]])

    @staticmethod
    def apply_matrix(matrix: np.ndarray, pontos: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Aplica uma matriz de transformação homogênea a uma lista de pontos.
        
        Recebe uma matriz 3x3 e uma lista de tuplas (x, y).
        Retorna a lista de pontos transformados.
        """
        novos_pontos = []
        for (x, y) in pontos:
            vetor = np.array([x, y, 1.0])
            resultado = vetor @ matrix  # multiplicação vetor-linha x matriz
            novos_pontos.append((resultado[0], resultado[1]))
        return novos_pontos

    @staticmethod
    def centro_objeto(pontos: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Calcula o centro geométrico de um objeto."""
        n = len(pontos)
        if n == 0:
            return (0.0, 0.0)
        cx = sum(p[0] for p in pontos) / n
        cy = sum(p[1] for p in pontos) / n
        return (cx, cy)

    # --- Transformações compostas ---

    @staticmethod
    def translacao(pontos, dx, dy):
        """Aplica translação diretamente."""
        m = Transform.translation_matrix(dx, dy)
        return Transform.apply_matrix(m, pontos)

    @staticmethod
    def escalonamento_centro(pontos, sx, sy):
        """Aplica escalonamento em torno do centro do objeto.
        
        Passos: transladar centro para origem → escalonar → transladar de volta.
        """
        cx, cy = Transform.centro_objeto(pontos)
        m = Transform.translation_matrix(-cx, -cy)
        m = m @ Transform.scaling_matrix(sx, sy)
        m = m @ Transform.translation_matrix(cx, cy)
        return Transform.apply_matrix(m, pontos)

    @staticmethod
    def rotacao_origem(pontos, angulo):
        """Aplica rotação em torno do centro do mundo (origem)."""
        m = Transform.rotation_matrix(angulo)
        return Transform.apply_matrix(m, pontos)

    @staticmethod
    def rotacao_centro(pontos, angulo):
        """Aplica rotação em torno do centro do objeto."""
        cx, cy = Transform.centro_objeto(pontos)
        m = Transform.translation_matrix(-cx, -cy)
        m = m @ Transform.rotation_matrix(angulo)
        m = m @ Transform.translation_matrix(cx, cy)
        return Transform.apply_matrix(m, pontos)

    @staticmethod
    def rotacao_ponto(pontos, angulo, px, py):
        """Aplica rotação em torno de um ponto arbitrário (px, py)."""
        m = Transform.translation_matrix(-px, -py)
        m = m @ Transform.rotation_matrix(angulo)
        m = m @ Transform.translation_matrix(px, py)
        return Transform.apply_matrix(m, pontos)

    @staticmethod
    def aplicar_lista_transformacoes(pontos, lista_transformacoes):
        """Aplica uma lista de transformações sequencialmente a um conjunto de pontos.
        
        A matriz resultante é calculada combinando todas as transformações.
        Para transformações que dependem do centro do objeto (escalonamento e rotação_centro),
        o centro é recalculado com base nos pontos atuais.
        """
        resultado = list(pontos)
        for transf in lista_transformacoes:
            tipo = transf[0]
            if tipo == "translacao":
                _, dx, dy = transf
                resultado = Transform.translacao(resultado, dx, dy)
            elif tipo == "escalonamento":
                _, sx, sy = transf
                resultado = Transform.escalonamento_centro(resultado, sx, sy)
            elif tipo == "rotacao_origem":
                _, angulo = transf
                resultado = Transform.rotacao_origem(resultado, angulo)
            elif tipo == "rotacao_centro":
                _, angulo = transf
                resultado = Transform.rotacao_centro(resultado, angulo)
            elif tipo == "rotacao_ponto":
                _, angulo, px, py = transf
                resultado = Transform.rotacao_ponto(resultado, angulo, px, py)
        return resultado
