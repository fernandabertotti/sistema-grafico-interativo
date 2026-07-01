# src/core/transform3d.py
import numpy as np
from typing import List, Tuple
from src.core.geometry import Ponto3D


class Transform3D:
    """Transformações 3D com matrizes 4x4 em coordenadas homogêneas.
    Convenção: vetores-linha à esquerda  →  ponto @ M  (igual ao Transform 2D).
    """

    @staticmethod
    def translation_matrix(dx: float, dy: float, dz: float) -> np.ndarray:
        return np.array([
            [1,  0,  0,  0],
            [0,  1,  0,  0],
            [0,  0,  1,  0],
            [dx, dy, dz, 1]
        ], dtype=float)

    @staticmethod
    def scaling_matrix(sx: float, sy: float, sz: float) -> np.ndarray:
        return np.array([
            [sx, 0,  0,  0],
            [0,  sy, 0,  0],
            [0,  0,  sz, 0],
            [0,  0,  0,  1]
        ], dtype=float)

    @staticmethod
    def rotation_x_matrix(angulo_graus: float) -> np.ndarray:
        a = np.radians(angulo_graus)
        c, s = np.cos(a), np.sin(a)
        return np.array([
            [1,  0,  0,  0],
            [0,  c,  s,  0],
            [0, -s,  c,  0],
            [0,  0,  0,  1]
        ], dtype=float)

    @staticmethod
    def rotation_y_matrix(angulo_graus: float) -> np.ndarray:
        a = np.radians(angulo_graus)
        c, s = np.cos(a), np.sin(a)
        return np.array([
            [ c,  0, -s,  0],
            [ 0,  1,  0,  0],
            [ s,  0,  c,  0],
            [ 0,  0,  0,  1]
        ], dtype=float)

    @staticmethod
    def rotation_z_matrix(angulo_graus: float) -> np.ndarray:
        a = np.radians(angulo_graus)
        c, s = np.cos(a), np.sin(a)
        return np.array([
            [ c,  s,  0,  0],
            [-s,  c,  0,  0],
            [ 0,  0,  1,  0],
            [ 0,  0,  0,  1]
        ], dtype=float)

    @staticmethod
    def rotation_arbitrary_axis(angulo_graus: float, eixo: tuple, ponto: tuple) -> np.ndarray:
        """Rotação em torno de eixo arbitrário passando por 'ponto'.

        Algoritmo: T(-ponto) → Rx(alinhar ao XZ) → Ry(alinhar ao Z) → Rz(θ) → inversos → T(ponto).
        """
        a, b, c = eixo
        norm = np.sqrt(a**2 + b**2 + c**2)
        a, b, c = a / norm, b / norm, c / norm

        px, py, pz = ponto
        d = np.sqrt(b**2 + c**2)

        T1 = Transform3D.translation_matrix(-px, -py, -pz)
        T2 = Transform3D.translation_matrix(px, py, pz)

        if d != 0:
            Rx = np.array([
                [1,  0,    0,   0],
                [0,  c/d,  b/d, 0],
                [0, -b/d,  c/d, 0],
                [0,  0,    0,   1]
            ], dtype=float)
            Rx_inv = np.array([
                [1,  0,    0,   0],
                [0,  c/d, -b/d, 0],
                [0,  b/d,  c/d, 0],
                [0,  0,    0,   1]
            ], dtype=float)
        else:
            Rx = np.eye(4)
            Rx_inv = np.eye(4)

        # Ry: alinhar (a, 0, d) com Z  →  cos=d, sin=-a
        Ry = np.array([
            [ d,  0,  a, 0],
            [ 0,  1,  0, 0],
            [-a,  0,  d, 0],
            [ 0,  0,  0, 1]
        ], dtype=float)
        Ry_inv = np.array([
            [d,  0, -a, 0],
            [0,  1,  0, 0],
            [a,  0,  d, 0],
            [0,  0,  0, 1]
        ], dtype=float)

        Rz = Transform3D.rotation_z_matrix(angulo_graus)
        return T1 @ Rx @ Ry @ Rz @ Ry_inv @ Rx_inv @ T2

    @staticmethod
    def apply_matrix(matrix: np.ndarray, segmentos) -> list:
        """Aplica matriz 4x4 a uma lista de segmentos (Ponto3D, Ponto3D)."""
        resultado = []
        for p1, p2 in segmentos:
            v1 = np.array([p1.x, p1.y, p1.z, 1.0]) @ matrix
            v2 = np.array([p2.x, p2.y, p2.z, 1.0]) @ matrix
            resultado.append((Ponto3D(v1[0], v1[1], v1[2]),
                               Ponto3D(v2[0], v2[1], v2[2])))
        return resultado

    @staticmethod
    def apply_matrix_pontos(matrix: np.ndarray, pontos) -> list:
        """Aplica matriz 4x4 a uma lista de Ponto3D."""
        resultado = []
        for p in pontos:
            v = np.array([p.x, p.y, p.z, 1.0]) @ matrix
            resultado.append(Ponto3D(v[0], v[1], v[2]))
        return resultado

    @staticmethod
    def apply_matrix_matriz_pontos(matrix: np.ndarray, matriz) -> list:
        return [Transform3D.apply_matrix_pontos(matrix, linha) for linha in matriz]

    @staticmethod
    def centro_objeto(segmentos) -> Tuple[float, float, float]:
        """Centróide de todos os pontos dos segmentos."""
        pontos = [p for seg in segmentos for p in seg]
        n = len(pontos)
        if n == 0:
            return (0.0, 0.0, 0.0)
        cx = sum(p.x for p in pontos) / n
        cy = sum(p.y for p in pontos) / n
        cz = sum(p.z for p in pontos) / n
        return (cx, cy, cz)

    @staticmethod
    def centro_matriz_pontos(matriz) -> Tuple[float, float, float]:
        pontos = [p for linha in matriz for p in linha]
        n = len(pontos)
        if n == 0:
            return (0.0, 0.0, 0.0)
        return (
            sum(p.x for p in pontos) / n,
            sum(p.y for p in pontos) / n,
            sum(p.z for p in pontos) / n,
        )

    @staticmethod
    def translacao(segmentos, dx: float, dy: float, dz: float) -> list:
        return Transform3D.apply_matrix(
            Transform3D.translation_matrix(dx, dy, dz), segmentos)

    @staticmethod
    def escalonamento_centro(segmentos, sx: float, sy: float, sz: float) -> list:
        cx, cy, cz = Transform3D.centro_objeto(segmentos)
        M = (Transform3D.translation_matrix(-cx, -cy, -cz)
             @ Transform3D.scaling_matrix(sx, sy, sz)
             @ Transform3D.translation_matrix(cx, cy, cz))
        return Transform3D.apply_matrix(M, segmentos)

    @staticmethod
    def rotacao_eixo(segmentos, angulo: float, eixo: str) -> list:
        """Rotação em torno do eixo X, Y ou Z, em torno do centróide."""
        cx, cy, cz = Transform3D.centro_objeto(segmentos)
        fn = {'x': Transform3D.rotation_x_matrix,
              'y': Transform3D.rotation_y_matrix,
              'z': Transform3D.rotation_z_matrix}[eixo]
        M = (Transform3D.translation_matrix(-cx, -cy, -cz)
             @ fn(angulo)
             @ Transform3D.translation_matrix(cx, cy, cz))
        return Transform3D.apply_matrix(M, segmentos)

    @staticmethod
    def rotacao_eixo_arbitrario(segmentos, angulo: float, eixo: tuple, ponto: tuple) -> list:
        M = Transform3D.rotation_arbitrary_axis(angulo, eixo, ponto)
        return Transform3D.apply_matrix(M, segmentos)

    @staticmethod
    def aplicar_lista_transformacoes(segmentos, lista) -> list:
        """Aplica lista de transformações sequencialmente.

        Formatos aceitos:
          ("translacao", dx, dy, dz)
          ("escalonamento", sx, sy, sz)
          ("rotacao_x" | "rotacao_y" | "rotacao_z", angulo)
          ("rotacao_arbitraria", angulo, (ax,ay,az), (px,py,pz))
        """
        resultado = list(segmentos)
        for t in lista:
            tipo = t[0]
            if tipo == "translacao":
                _, dx, dy, dz = t
                resultado = Transform3D.translacao(resultado, dx, dy, dz)
            elif tipo == "escalonamento":
                _, sx, sy, sz = t
                resultado = Transform3D.escalonamento_centro(resultado, sx, sy, sz)
            elif tipo in ("rotacao_x", "rotacao_y", "rotacao_z"):
                _, angulo = t
                eixo = tipo[-1]
                resultado = Transform3D.rotacao_eixo(resultado, angulo, eixo)
            elif tipo == "rotacao_arbitraria":
                _, angulo, eixo, ponto = t
                resultado = Transform3D.rotacao_eixo_arbitrario(resultado, angulo, eixo, ponto)
        return resultado

    @staticmethod
    def _matriz_para_transformacao(t, centro) -> np.ndarray:
        tipo = t[0]
        cx, cy, cz = centro
        if tipo == "translacao":
            _, dx, dy, dz = t
            return Transform3D.translation_matrix(dx, dy, dz)
        if tipo == "escalonamento":
            _, sx, sy, sz = t
            return (Transform3D.translation_matrix(-cx, -cy, -cz)
                    @ Transform3D.scaling_matrix(sx, sy, sz)
                    @ Transform3D.translation_matrix(cx, cy, cz))
        if tipo in ("rotacao_x", "rotacao_y", "rotacao_z"):
            _, angulo = t
            fn = {'x': Transform3D.rotation_x_matrix,
                  'y': Transform3D.rotation_y_matrix,
                  'z': Transform3D.rotation_z_matrix}[tipo[-1]]
            return (Transform3D.translation_matrix(-cx, -cy, -cz)
                    @ fn(angulo)
                    @ Transform3D.translation_matrix(cx, cy, cz))
        if tipo == "rotacao_arbitraria":
            _, angulo, eixo, ponto = t
            return Transform3D.rotation_arbitrary_axis(angulo, eixo, ponto)
        return np.eye(4)

    @staticmethod
    def apply_matrix_triangulos(matrix: np.ndarray, triangulos) -> list:
        L = matrix[:3, :3]
        try:
            L_inv_T = np.linalg.inv(L).T
        except np.linalg.LinAlgError:
            L_inv_T = L
        novos = []
        for tri in triangulos:
            vs = []
            for (x, y, z) in tri['v']:
                v = np.array([x, y, z, 1.0]) @ matrix
                vs.append((float(v[0]), float(v[1]), float(v[2])))
            ns = []
            for (nx, ny, nz) in tri['n']:
                n = np.array([nx, ny, nz], dtype=float) @ L_inv_T
                norma = np.linalg.norm(n)
                if norma > 1e-12:
                    n = n / norma
                ns.append((float(n[0]), float(n[1]), float(n[2])))
            novos.append({'v': vs, 'n': ns})
        return novos

    @staticmethod
    def aplicar_lista_transformacoes_com_faces(segmentos, triangulos, lista):
        segs = list(segmentos)
        tris = list(triangulos) if triangulos else None
        for t in lista:
            centro = Transform3D.centro_objeto(segs)
            M = Transform3D._matriz_para_transformacao(t, centro)
            segs = Transform3D.apply_matrix(M, segs)
            if tris is not None:
                tris = Transform3D.apply_matrix_triangulos(M, tris)
        return segs, tris

    @staticmethod
    def aplicar_lista_transformacoes_matriz(matriz_pontos, lista) -> list:
        resultado = [list(linha) for linha in matriz_pontos]
        for t in lista:
            tipo = t[0]
            if tipo == "translacao":
                _, dx, dy, dz = t
                M = Transform3D.translation_matrix(dx, dy, dz)
            elif tipo == "escalonamento":
                _, sx, sy, sz = t
                cx, cy, cz = Transform3D.centro_matriz_pontos(resultado)
                M = (Transform3D.translation_matrix(-cx, -cy, -cz)
                     @ Transform3D.scaling_matrix(sx, sy, sz)
                     @ Transform3D.translation_matrix(cx, cy, cz))
            elif tipo in ("rotacao_x", "rotacao_y", "rotacao_z"):
                _, angulo = t
                eixo = tipo[-1]
                cx, cy, cz = Transform3D.centro_matriz_pontos(resultado)
                fn = {'x': Transform3D.rotation_x_matrix,
                      'y': Transform3D.rotation_y_matrix,
                      'z': Transform3D.rotation_z_matrix}[eixo]
                M = (Transform3D.translation_matrix(-cx, -cy, -cz)
                     @ fn(angulo)
                     @ Transform3D.translation_matrix(cx, cy, cz))
            elif tipo == "rotacao_arbitraria":
                _, angulo, eixo, ponto = t
                M = Transform3D.rotation_arbitrary_axis(angulo, eixo, ponto)
            else:
                continue
            resultado = Transform3D.apply_matrix_matriz_pontos(M, resultado)
        return resultado
