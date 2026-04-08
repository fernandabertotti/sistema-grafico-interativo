# src/core/obj_io.py
"""Módulo para leitura e escrita de arquivos Wavefront .obj.

Formato suportado:
  - Vértices: v x y z  (z é ignorado/setado como 0 em 2D)
  - Pontos: p v1
  - Linhas: l v1 v2 ...
  - Faces: f v1 v2 v3 ...  (usadas como wireframes)
  - Objetos: o nome
  - Cores: usercor r g b  (extensão customizada para manter cor RGB)
  - Grupos: g nome  (tratados como sinônimo de 'o')

Cada objeto no display file gera um bloco:
  o nome_do_objeto
  usercor r g b
  v x1 y1 0.0
  v x2 y2 0.0
  ...
  l/p/f  (conforme tipo)
"""

from src.core.geometry import Ponto, Reta, Wireframe


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

        # Vértices
        for (x, y) in objeto.pontos:
            linhas.append(f"v {x} {y} 0.0")

        num_vertices = len(objeto.pontos)

        # Elemento (ponto, linha ou face)
        if objeto.tipo == "Ponto":
            linhas.append(f"p {offset_vertice + 1}")
        elif objeto.tipo == "Reta":
            indices = " ".join(str(offset_vertice + i + 1) for i in range(num_vertices))
            linhas.append(f"l {indices}")
        elif objeto.tipo == "Wireframe":
            indices = " ".join(str(offset_vertice + i + 1) for i in range(num_vertices))
            linhas.append(f"f {indices}")

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
    vertices_globais = []  # índice 1-based no .obj
    objetos = []

    nome_atual = None
    cor_atual = "#000000"

    with open(filepath, "r") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue

            partes = linha.split()
            tipo = partes[0]

            if tipo == "o" or tipo == "g":
                # Novo objeto/grupo
                nome_atual = " ".join(partes[1:]) if len(partes) > 1 else f"obj_{len(objetos)}"
                cor_atual = "#000000"

            elif tipo == "usercor":
                # Cor customizada
                if len(partes) >= 4:
                    r, g, b = float(partes[1]), float(partes[2]), float(partes[3])
                    cor_atual = DescritorOBJ._rgb_normalizado_para_hex(r, g, b)

            elif tipo == "v":
                # Vértice
                x = float(partes[1])
                y = float(partes[2])
                # z é ignorado (partes[3] se existir)
                vertices_globais.append((x, y))

            elif tipo == "p":
                # Ponto
                if nome_atual is None:
                    nome_atual = f"ponto_{len(objetos)}"
                indices = [int(idx) for idx in partes[1:]]
                pontos = [vertices_globais[i - 1] for i in indices]
                objetos.append(Ponto(nome_atual, pontos, cor_atual))
                nome_atual = None

            elif tipo == "l":
                # Linha
                if nome_atual is None:
                    nome_atual = f"linha_{len(objetos)}"
                indices = [int(idx) for idx in partes[1:]]
                pontos = [vertices_globais[i - 1] for i in indices]
                if len(pontos) == 2:
                    objetos.append(Reta(nome_atual, pontos, cor_atual))
                else:
                    # Polilinha como wireframe aberto — tratamos como wireframe
                    objetos.append(Wireframe(nome_atual, pontos, cor_atual))
                nome_atual = None

            elif tipo == "f":
                # Face (wireframe fechado)
                if nome_atual is None:
                    nome_atual = f"wireframe_{len(objetos)}"
                # Suporta formato v, v/vt, v/vt/vn, v//vn
                indices = []
                for idx_str in partes[1:]:
                    idx = int(idx_str.split("/")[0])
                    indices.append(idx)
                pontos = [vertices_globais[i - 1] for i in indices]
                objetos.append(Wireframe(nome_atual, pontos, cor_atual))
                nome_atual = None

    return objetos
