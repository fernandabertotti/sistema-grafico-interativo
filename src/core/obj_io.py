# src/core/obj_io.py
"""Módulo para leitura e escrita de arquivos Wavefront .obj.

Formato suportado:
  - Vértices: v x y z
  - Pontos: p v1
  - Linhas: l v1 v2 ...
  - Faces: f v1 v2 v3 ...  (wireframes)
  - Objetos: o nome
  - Cores: usercor r g b         (extensão customizada — cor RGB)
  - Tipo: usertype <tipo>        (extensão customizada — Curva2D, BSpline2D, Wireframe, Objeto3D)
  - Preenchimento: userfill 1|0  (extensão customizada — wireframe preenchido)
  - Grupos: g nome  (tratados como sinônimo de 'o')

Objetos 2D escrevem z=0.0; Objeto3D escreve z real e usa 'usertype Objeto3D'.
Para Objeto3D, cada segmento gera dois vértices consecutivos + uma linha 'l i j'.
"""

from src.core.geometry import (
    Ponto, Reta, Wireframe, Curva2D, BSpline2D, Ponto3D, Objeto3D,
    SuperficieBSpline3D, triangulo_flat,
)


class DescritorOBJ:
    """Transcreve um objeto gráfico para o formato .obj."""

    @staticmethod
    def objeto_para_obj(objeto, offset_vertice=0):
        """Converte um objeto gráfico para linhas no formato .obj.

        Retorna (linhas, num_vertices_escritos).
        """
        linhas = []
        linhas.append(f"o {objeto.nome}")

        r, g, b = DescritorOBJ._hex_para_rgb_normalizado(objeto.cor)
        linhas.append(f"usercor {r:.4f} {g:.4f} {b:.4f}")

        if objeto.tipo == "SuperficieBSpline3D":
            linhas.append("usertype SuperficieBSpline3D")
            linhas_qtd = len(objeto.matriz_controle)
            colunas_qtd = len(objeto.matriz_controle[0]) if linhas_qtd else 0
            linhas.append(f"usersteps {getattr(objeto, 'passos', 10)}")
            for linha in objeto.matriz_controle:
                for p in linha:
                    linhas.append(f"v {p.x} {p.y} {p.z}")
            indices = " ".join(
                str(offset_vertice + i + 1)
                for i in range(linhas_qtd * colunas_qtd))
            linhas.append(f"bsplinesurf {linhas_qtd} {colunas_qtd} {indices}")
            return linhas, linhas_qtd * colunas_qtd

        if objeto.tipo == "Objeto3D":
            linhas.append("usertype Objeto3D")
            for p1, p2 in objeto.segmentos:
                linhas.append(f"v {p1.x} {p1.y} {p1.z}")
                linhas.append(f"v {p2.x} {p2.y} {p2.z}")
            for i in range(len(objeto.segmentos)):
                i1 = offset_vertice + 2 * i + 1
                i2 = offset_vertice + 2 * i + 2
                linhas.append(f"l {i1} {i2}")
            return linhas, len(objeto.segmentos) * 2

        if objeto.tipo in ("Curva2D", "BSpline2D"):
            linhas.append(f"usertype {objeto.tipo}")

        if objeto.tipo == "Wireframe":
            preenchido = 1 if getattr(objeto, 'preenchido', False) else 0
            linhas.append(f"userfill {preenchido}")

        for (x, y) in objeto.pontos:
            linhas.append(f"v {x} {y} 0.0")

        num_vertices = len(objeto.pontos)
        indices = " ".join(str(offset_vertice + i + 1) for i in range(num_vertices))

        if objeto.tipo == "Ponto":
            linhas.append(f"p {offset_vertice + 1}")
        elif objeto.tipo == "Reta":
            linhas.append(f"l {indices}")
        elif objeto.tipo == "Wireframe":
            linhas.append(f"f {indices}")
        elif objeto.tipo == "Curva2D":
            linhas.append(f"curva {indices}")
        elif objeto.tipo == "BSpline2D":
            linhas.append(f"bspline {indices}")

        return linhas, num_vertices

    @staticmethod
    def _hex_para_rgb_normalizado(hex_cor):
        hex_cor = hex_cor.lstrip("#")
        r = int(hex_cor[0:2], 16) / 255.0
        g = int(hex_cor[2:4], 16) / 255.0
        b = int(hex_cor[4:6], 16) / 255.0
        return (r, g, b)

    @staticmethod
    def _rgb_normalizado_para_hex(r, g, b):
        ri = max(0, min(255, int(round(r * 255))))
        gi = max(0, min(255, int(round(g * 255))))
        bi = max(0, min(255, int(round(b * 255))))
        return f"#{ri:02X}{gi:02X}{bi:02X}"


def salvar_obj(filepath, display_file):
    """Salva todos os objetos do display file em um arquivo .obj."""
    linhas = []
    linhas.append("# Arquivo OBJ gerado pelo Sistema Gráfico Interativo")
    linhas.append("")

    offset = 0
    for obj in display_file.obter_todos():
        obj_linhas, num_v = DescritorOBJ.objeto_para_obj(obj, offset)
        linhas.extend(obj_linhas)
        linhas.append("")
        offset += num_v

    with open(filepath, "w") as f:
        f.write("\n".join(linhas))


def carregar_obj(filepath):
    """Carrega objetos de um arquivo .obj e retorna lista de objetos gráficos.

    Suporta objetos 2D (Ponto, Reta, Wireframe, Curva2D, BSpline2D) e 3D (Objeto3D).
    Vértices são armazenados como (x, y, z); objetos 2D usam apenas (x, y).
    """
    vertices_globais = []   # (x, y, z)
    objetos = []

    nome_atual = None
    cor_atual = "#000000"
    tipo_atual = None
    fill_atual = False
    passos_atual = 10

    # Estado para acumular segmentos de Objeto3D (múltiplos 'l' por objeto)
    nome_3d = None
    cor_3d = "#000000"
    segmentos_3d = []
    triangulos_3d = []

    def _finalizar_objeto_3d():
        nonlocal segmentos_3d, triangulos_3d, nome_3d, cor_3d
        if segmentos_3d and nome_3d:
            objetos.append(Objeto3D(nome_3d, list(segmentos_3d), cor_3d,
                                    triangulos=list(triangulos_3d) or None))
        segmentos_3d = []
        triangulos_3d = []
        nome_3d = None

    with open(filepath, "r") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue

            partes = linha.split()
            token = partes[0]

            if token in ("o", "g"):
                _finalizar_objeto_3d()
                nome_atual = " ".join(partes[1:]) if len(partes) > 1 else f"obj_{len(objetos)}"
                cor_atual = "#000000"
                tipo_atual = None
                fill_atual = False
                passos_atual = 10

            elif token == "usercor":
                if len(partes) >= 4:
                    r, g, b = float(partes[1]), float(partes[2]), float(partes[3])
                    cor_atual = DescritorOBJ._rgb_normalizado_para_hex(r, g, b)

            elif token == "usertype":
                if len(partes) >= 2:
                    tipo_atual = partes[1]
                    if tipo_atual == "Objeto3D":
                        nome_3d = nome_atual
                        cor_3d = cor_atual

            elif token == "userfill":
                if len(partes) >= 2:
                    fill_atual = partes[1] == "1"

            elif token == "usersteps":
                if len(partes) >= 2:
                    passos_atual = int(partes[1])

            elif token == "v":
                x = float(partes[1])
                y = float(partes[2])
                z = float(partes[3]) if len(partes) > 3 else 0.0
                vertices_globais.append((x, y, z))

            elif token == "p":
                if nome_atual is None:
                    nome_atual = f"ponto_{len(objetos)}"
                indices = [int(idx) for idx in partes[1:]]
                pontos = [vertices_globais[i - 1][:2] for i in indices]
                objetos.append(Ponto(nome_atual, pontos, cor_atual))
                nome_atual = None; tipo_atual = None; fill_atual = False

            elif token == "l":
                if tipo_atual == "Objeto3D":
                    indices = [int(idx) for idx in partes[1:]]
                    pts = [vertices_globais[i - 1] for i in indices]
                    if len(pts) >= 2:
                        segmentos_3d.append((Ponto3D(*pts[0]), Ponto3D(*pts[1])))
                else:
                    if nome_atual is None:
                        nome_atual = f"linha_{len(objetos)}"
                    indices = [int(idx) for idx in partes[1:]]
                    pontos = [vertices_globais[i - 1][:2] for i in indices]
                    if len(pontos) == 2:
                        objetos.append(Reta(nome_atual, pontos, cor_atual))
                    else:
                        objetos.append(Wireframe(nome_atual, pontos, cor_atual, preenchido=fill_atual))
                    nome_atual = None; tipo_atual = None; fill_atual = False

            elif token == "f":
                if nome_atual is None:
                    nome_atual = f"obj_{len(objetos)}"
                indices = []
                for idx_str in partes[1:]:
                    indices.append(int(idx_str.split("/")[0]))
                verts = [vertices_globais[i - 1] for i in indices]

                # Face com vértices 3D (z != 0) → acumula arestas em Objeto3D
                is_3d_face = any(abs(v[2]) > 1e-10 for v in verts)
                if is_3d_face:
                    if nome_3d is None:
                        nome_3d = nome_atual
                        cor_3d = cor_atual
                    n_f = len(verts)
                    for j in range(n_f):
                        segmentos_3d.append((Ponto3D(*verts[j]),
                                             Ponto3D(*verts[(j + 1) % n_f])))
                    for j in range(1, n_f - 1):
                        triangulos_3d.append(
                            triangulo_flat(verts[0], verts[j], verts[j + 1]))
                else:
                    pontos = [v[:2] for v in verts]
                    objetos.append(Wireframe(nome_atual, pontos, cor_atual, preenchido=fill_atual))
                    nome_atual = None; tipo_atual = None; fill_atual = False

            elif token == "curva":
                if nome_atual is None:
                    nome_atual = f"curva_{len(objetos)}"
                indices = [int(idx) for idx in partes[1:]]
                pontos = [vertices_globais[i - 1][:2] for i in indices]
                objetos.append(Curva2D(nome_atual, pontos, cor_atual))
                nome_atual = None; tipo_atual = None; fill_atual = False

            elif token == "bspline":
                if nome_atual is None:
                    nome_atual = f"bspline_{len(objetos)}"
                indices = [int(idx) for idx in partes[1:]]
                pontos = [vertices_globais[i - 1][:2] for i in indices]
                objetos.append(BSpline2D(nome_atual, pontos, cor_atual))
                nome_atual = None; tipo_atual = None; fill_atual = False

            elif token == "bsplinesurf":
                if nome_atual is None:
                    nome_atual = f"superficie_{len(objetos)}"
                linhas_qtd = int(partes[1])
                colunas_qtd = int(partes[2])
                indices = [int(idx) for idx in partes[3:]]
                if len(indices) != linhas_qtd * colunas_qtd:
                    raise ValueError("Quantidade de indices da superficie B-Spline invalida.")
                matriz = []
                pos = 0
                for _ in range(linhas_qtd):
                    linha = []
                    for _ in range(colunas_qtd):
                        linha.append(Ponto3D(*vertices_globais[indices[pos] - 1]))
                        pos += 1
                    matriz.append(linha)
                objetos.append(SuperficieBSpline3D(nome_atual, matriz, cor_atual, passos_atual))
                nome_atual = None; tipo_atual = None; fill_atual = False; passos_atual = 10

    _finalizar_objeto_3d()
    return objetos
