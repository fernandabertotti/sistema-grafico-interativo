# src/core/powergirl_model.py
"""Modelo de teste embutido para iluminacao de Phong (Trabalho 2.3).

Gera proceduralmente uma esfera por subdivisao UV. As normais por vertice sao
exatas (posicao normalizada, pois a esfera esta centrada na origem), o que
torna o modelo ideal para validar o shading de Phong por pixel.
"""
import math


def get_powergirl_triangles(raio: float = 100.0,
                            segmentos_u: int = 16,
                            segmentos_v: int = 16,
                            centro=(0.0, 0.0, 0.0)):
    """Retorna a lista de triangulos do modelo (esfera UV subdividida).

    `centro` desloca a esfera no mundo (as normais nao mudam com translacao).

    Cada triangulo e um dict:
      {
        'v': [(x, y, z), (x, y, z), (x, y, z)],   # vertices no mundo
        'n': [(nx, ny, nz), (nx, ny, nz), (nx, ny, nz)],  # normais por vertice
      }
    """
    cx, cy, cz = centro

    def normal(i, j):
        # i (latitude): 0..segmentos_v ; j (longitude): 0..segmentos_u
        theta = math.pi * i / segmentos_v        # 0..pi (polo a polo)
        phi = 2.0 * math.pi * j / segmentos_u    # 0..2pi (ao redor)
        nx = math.sin(theta) * math.cos(phi)
        ny = math.cos(theta)
        nz = math.sin(theta) * math.sin(phi)
        return (nx, ny, nz)

    def vertice(nrm):
        return (nrm[0] * raio + cx, nrm[1] * raio + cy, nrm[2] * raio + cz)

    triangulos = []
    for i in range(segmentos_v):
        for j in range(segmentos_u):
            n00 = normal(i, j)
            n01 = normal(i, j + 1)
            n10 = normal(i + 1, j)
            n11 = normal(i + 1, j + 1)
            v00 = vertice(n00)
            v01 = vertice(n01)
            v10 = vertice(n10)
            v11 = vertice(n11)

            # Cada quad da malha vira dois triangulos.
            triangulos.append({'v': [v00, v10, v11], 'n': [n00, n10, n11]})
            triangulos.append({'v': [v00, v11, v01], 'n': [n00, n11, n01]})

    return triangulos
