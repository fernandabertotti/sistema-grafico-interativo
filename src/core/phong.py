# src/core/phong.py
"""Modelo de iluminacao de Phong (Trabalho 2.3).

I = ka*Ia + kd*(L.N)*Id + ks*(R.V)^n*Is
"""
import numpy as np


class LuzPontual:
    """Fonte de luz pontual com posicao e intensidade RGB."""
    def __init__(self, posicao, intensidade=(1.0, 1.0, 1.0)):
        self.posicao = np.array(posicao, dtype=float)
        self.intensidade = np.array(intensidade, dtype=float)


class MaterialPhong:
    """Propriedades de material para o modelo de Phong."""
    def __init__(self,
                 ka=(0.1, 0.1, 0.1),   # coeficiente ambiente
                 kd=(0.7, 0.7, 0.7),   # coeficiente difuso
                 ks=(0.5, 0.5, 0.5),   # coeficiente especular
                 shininess=32.0):
        self.ka = np.array(ka, dtype=float)
        self.kd = np.array(kd, dtype=float)
        self.ks = np.array(ks, dtype=float)
        self.shininess = float(shininess)


def _normalizar(vetor):
    """Retorna o vetor normalizado (ou ele mesmo, se for quase nulo)."""
    norma = np.linalg.norm(vetor)
    if norma < 1e-12:
        return vetor
    return vetor / norma


def calcular_phong(ponto_3d, normal, olho, luz: LuzPontual,
                   material: MaterialPhong,
                   luz_ambiente=(0.2, 0.2, 0.2)):
    """Calcula a cor (R, G, B) em [0,1] de um ponto pelo modelo de Phong.

    Todos os vetores sao normalizados internamente e a cor final e limitada
    ao intervalo [0,1].
    """
    p = np.array(ponto_3d, dtype=float)
    n = _normalizar(np.array(normal, dtype=float))
    l = _normalizar(luz.posicao - p)            # direcao ate a luz
    v = _normalizar(np.array(olho, dtype=float) - p)  # direcao ate o observador
    ia = np.array(luz_ambiente, dtype=float)

    # Iluminacao de dois lados: a normal aponta para o observador (superficies
    # abertas ficam iluminadas de qualquer lado que estiver voltado para a camera).
    if np.dot(n, v) < 0:
        n = -n

    # Componente ambiente.
    cor = material.ka * ia

    # Componente difusa (Lambert).
    n_dot_l = float(np.dot(n, l))
    if n_dot_l > 0.0:
        cor = cor + material.kd * n_dot_l * luz.intensidade

        # Componente especular (reflexao de L em torno de N).
        r = _normalizar(2.0 * n_dot_l * n - l)
        r_dot_v = float(np.dot(r, v))
        if r_dot_v > 0.0:
            cor = cor + material.ks * (r_dot_v ** material.shininess) * luz.intensidade

    cor = np.clip(cor, 0.0, 1.0)
    return (float(cor[0]), float(cor[1]), float(cor[2]))


def _normalizar_linhas(m):
    """Normaliza cada linha de uma matriz (M, 3)."""
    normas = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.clip(normas, 1e-12, None)


def calcular_phong_array(pontos, normais, olho, luz: LuzPontual,
                         material: MaterialPhong,
                         luz_ambiente=(0.2, 0.2, 0.2)):
    """Versão vetorizada de `calcular_phong` para vários pontos de uma vez.

    `pontos` e `normais` são arrays (M, 3). Retorna cores (M, 3) em [0,1].
    Usada pelo rasterizador para calcular Phong por pixel de forma eficiente.
    """
    p = np.asarray(pontos, dtype=float)
    n = _normalizar_linhas(np.asarray(normais, dtype=float))
    l = _normalizar_linhas(luz.posicao - p)
    v = _normalizar_linhas(np.asarray(olho, dtype=float) - p)
    ia = np.asarray(luz_ambiente, dtype=float)

    # Iluminacao de dois lados: normal voltada para o observador.
    inverter = (np.sum(n * v, axis=1) < 0)[:, None]
    n = np.where(inverter, -n, n)

    n_dot_l = np.sum(n * l, axis=1)              # (M,)
    n_dot_l_pos = np.clip(n_dot_l, 0.0, None)

    # Ambiente + difusa
    cor = material.ka * ia + material.kd * n_dot_l_pos[:, None] * luz.intensidade

    # Especular (só onde a face está voltada para a luz)
    r = _normalizar_linhas(2.0 * n_dot_l[:, None] * n - l)
    r_dot_v = np.clip(np.sum(r * v, axis=1), 0.0, None)
    fator_spec = (r_dot_v ** material.shininess)[:, None] * (n_dot_l > 0)[:, None]
    cor = cor + material.ks * fator_spec * luz.intensidade

    return np.clip(cor, 0.0, 1.0)
