# src/core/obj_io.py
"""Módulo para leitura e escrita de arquivos Wavefront .obj.

Formato suportado:
  - Vértices: v x y z  (z é ignorado/setado como 0 em 2D)
  - Pontos: p v1
  - Linhas: l v1 v2 ...
  - Faces: f v1 v2 v3 ...  (wireframes)
  - Objetos: o nome
  - Cores: usercor r g b         (extensão customizada — cor RGB)
  - Tipo: usertype <tipo>        (extensão customizada — Curva2D, BSpline2D, Wireframe)
  - Preenchimento: userfill 1|0  (extensão customizada — wireframe preenchido)
  - Grupos: g nome  (tratados como sinônimo de 'o')

Cada objeto no display file gera um bloco:
  o nome_do_objeto
  usercor r g b
  usertype <tipo>          (apenas para Curva2D e BSpline2D; omitido para tipos nativos)
  userfill 1|0             (apenas para Wireframe)
  v x1 y1 0.0
  v x2 y2 0.0
  ...
  l/p/f/curva/bspline  (conforme tipo)
"""

from src.core.geometry import Ponto, Reta, Wireframe, Curva2D, BSpline2D


class DescritorOBJ:
    """Transcreve um objeto gráfico para o formato .obj."""

    @staticmethod
    def objeto_para_obj(objeto, offset_vertice=0):
        """Converte um ObjetoGrafico para linhas no formato .obj."""
        linhas = []

        # Nome do objeto
        linhas.append(f"o {objeto.nome}")

        # Cor (extensão customizada)
        r, g, b = DescritorOBJ._hex_para_rgb_normalizado(objeto.cor)
        linhas.append(f"usercor {r:.4f} {g:.4f} {b:.4f}")

        # Tipo customizado (necessário para Curva2D e BSpline2D, que não têm
        # equivalente nativo no formato .obj)
        if objeto.tipo in ("Curva2D", "BSpline2D"):
            linhas.append(f"usertype {objeto.tipo}")

        # Preenchimento (apenas wireframes)
        if objeto.tipo == "Wireframe":
            preenchido = 1 if getattr(objeto, 'preenchido', False) else 0
            linhas.append(f"userfill {preenchido}")

        # Vértices
        for (x, y) in objeto.pontos:
            linhas.append(f"v {x} {y} 0.0")

        num_vertices = len(objeto.pontos)
        indices = " ".join(str(offset_vertice + i + 1) for i in range(num_vertices))

        # Elemento geométrico
        if objeto.tipo == "Ponto":
            linhas.append(f"p {offset_vertice + 1}")
        elif objeto.tipo == "Reta":
            linhas.append(f"l {indices}")
        elif objeto.tipo == "Wireframe":
            linhas.append(f"f {indices}")
        elif objeto.tipo == "Curva2D":
            # Curvas não têm primitiva nativa no .obj — usamos 'curva' como
            # marcador customizado. O loader reconhece essa palavra-chave.
            linhas.append(f"curva {indices}")
        elif objeto.tipo == "BSpline2D":
            linhas.append(f"bspline {indices}")

        return linhas, num_vertices

    @staticmethod
    def _hex_para_rgb_normalizado(hex_cor):
        """Converte cor hex (#RRGGBB) para tupla normalizada (0-1)."""
        hex_cor = hex_cor.lstrip("#")
        r = int(hex_cor[0:2], 16) / 255.0
        g = int(hex_cor[2:4], 16) / 255.0
        b = int(hex_cor[4:6], 16) / 255.0
        return (r, g, b)

    @staticmethod
    def _rgb_normalizado_para_hex(r, g, b):
        """Converte tupla normalizada (0-1) para cor hex (#RRGGBB)."""
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
    """Carrega objetos de um arquivo .obj e retorna lista de ObjetoGrafico."""
    vertices_globais = []
    objetos = []

    nome_atual = None
    cor_atual = "#000000"
    tipo_atual = None    # definido por 'usertype' quando presente
    fill_atual = False   # definido por 'userfill' quando presente

    with open(filepath, "r") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue

            partes = linha.split()
            token = partes[0]

            if token in ("o", "g"):
                nome_atual = " ".join(partes[1:]) if len(partes) > 1 else f"obj_{len(objetos)}"
                cor_atual = "#000000"
                tipo_atual = None
                fill_atual = False

            elif token == "usercor":
                if len(partes) >= 4:
                    r, g, b = float(partes[1]), float(partes[2]), float(partes[3])
                    cor_atual = DescritorOBJ._rgb_normalizado_para_hex(r, g, b)

            elif token == "usertype":
                if len(partes) >= 2:
                    tipo_atual = partes[1]

            elif token == "userfill":
                if len(partes) >= 2:
                    fill_atual = partes[1] == "1"

            elif token == "v":
                x = float(partes[1])
                y = float(partes[2])
                vertices_globais.append((x, y))

            elif token == "p":
                if nome_atual is None:
                    nome_atual = f"ponto_{len(objetos)}"
                indices = [int(idx) for idx in partes[1:]]
                pontos = [vertices_globais[i - 1] for i in indices]
                objetos.append(Ponto(nome_atual, pontos, cor_atual))
                nome_atual = None
                tipo_atual = None
                fill_atual = False

            elif token == "l":
                if nome_atual is None:
                    nome_atual = f"linha_{len(objetos)}"
                indices = [int(idx) for idx in partes[1:]]
                pontos = [vertices_globais[i - 1] for i in indices]
                if len(pontos) == 2:
                    objetos.append(Reta(nome_atual, pontos, cor_atual))
                else:
                    objetos.append(Wireframe(nome_atual, pontos, cor_atual, preenchido=fill_atual))
                nome_atual = None
                tipo_atual = None
                fill_atual = False

            elif token == "f":
                if nome_atual is None:
                    nome_atual = f"wireframe_{len(objetos)}"
                indices = []
                for idx_str in partes[1:]:
                    idx = int(idx_str.split("/")[0])
                    indices.append(idx)
                pontos = [vertices_globais[i - 1] for i in indices]
                objetos.append(Wireframe(nome_atual, pontos, cor_atual, preenchido=fill_atual))
                nome_atual = None
                tipo_atual = None
                fill_atual = False

            elif token == "curva":
                if nome_atual is None:
                    nome_atual = f"curva_{len(objetos)}"
                indices = [int(idx) for idx in partes[1:]]
                pontos = [vertices_globais[i - 1] for i in indices]
                objetos.append(Curva2D(nome_atual, pontos, cor_atual))
                nome_atual = None
                tipo_atual = None
                fill_atual = False

            elif token == "bspline":
                if nome_atual is None:
                    nome_atual = f"bspline_{len(objetos)}"
                indices = [int(idx) for idx in partes[1:]]
                pontos = [vertices_globais[i - 1] for i in indices]
                objetos.append(BSpline2D(nome_atual, pontos, cor_atual))
                nome_atual = None
                tipo_atual = None
                fill_atual = False

    return objetos