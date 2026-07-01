# src/ui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QListWidget, QListWidgetItem, QLineEdit, QLabel, QMessageBox,
                             QGridLayout, QGroupBox, QDialog, QTabWidget,
                             QMenu, QButtonGroup, QRadioButton, QComboBox, QFileDialog,
                             QCheckBox, QSlider, QTextEdit)
from PyQt6.QtCore import Qt
from src.ui.canvas import Canvas
from src.core.geometry import (
    Ponto, Reta, Wireframe, Curva2D, BSpline2D, Ponto3D, Objeto3D,
    SuperficieBSpline3D, triangulo_flat, arestas_de_triangulos,
)
from src.core.powergirl_model import get_powergirl_triangles
from src.core.transform3d import Transform3D as Transform3D3D
from src.core.window3d import Window3D
from src.core.transform import Transform
from src.core.obj_io import salvar_obj, carregar_obj
from src.core.bspline_surface import validar_matriz_controle


def _parse_segmentos_3d(texto: str):
    """Converte '(x1,y1,z1)-(x2,y2,z2), ...' em lista de (Ponto3D, Ponto3D).

    Levanta ValueError se o formato estiver errado.
    """
    import re
    segmentos = []
    padrao = r'\(([^)]+)\)\s*-\s*\(([^)]+)\)'
    for m in re.finditer(padrao, texto):
        coords_a = tuple(float(v.strip()) for v in m.group(1).split(','))
        coords_b = tuple(float(v.strip()) for v in m.group(2).split(','))
        if len(coords_a) != 3 or len(coords_b) != 3:
            raise ValueError(f"Coordenada deve ter 3 valores: {m.group(0)!r}")
        segmentos.append((Ponto3D(*coords_a), Ponto3D(*coords_b)))
    if not segmentos:
        raise ValueError("Nenhum segmento encontrado. Use o formato: (x1,y1,z1)-(x2,y2,z2), ...")
    return segmentos


def _parse_matriz_pontos_3d(texto: str):
    import ast
    matriz = []
    for linha_txt in texto.strip().split(";"):
        linha_txt = linha_txt.strip()
        if not linha_txt:
            continue
        valores = ast.literal_eval(f"[{linha_txt}]")
        linha = []
        for ponto in valores:
            if len(ponto) != 3:
                raise ValueError(f"Ponto deve ter 3 valores: {ponto!r}")
            linha.append(Ponto3D(float(ponto[0]), float(ponto[1]), float(ponto[2])))
        matriz.append(linha)
    validar_matriz_controle(matriz)
    return matriz


def _format_matriz_pontos_3d(matriz):
    linhas = []
    for linha in matriz:
        linhas.append(", ".join(f"({p.x:g},{p.y:g},{p.z:g})" for p in linha))
    return ";\n".join(linhas)


# --- CLASSE DO DIÁLOGO (POP-UP) ---

class JanelaObjetoDialog(QDialog):
    """Janela modal para adicionar ou editar objetos"""

    def __init__(self, parent=None, nome="", coords="", cor_atual="#000000", modo_edicao=False, preenchido=False, tipo_atual="Automático"):
        super().__init__(parent)
        self.setWindowTitle("Propriedades do Objeto" if modo_edicao else "Novo Objeto")
        self.setFixedSize(500, 480)
        self.modo_edicao = modo_edicao
        self.apagar_solicitado = False
        self.lista_transformacoes = []

        layout_principal = QVBoxLayout(self)

        # Sistema de Abas
        self.abas = QTabWidget()
        layout_principal.addWidget(self.abas)

        # Aba 1: Geometria
        self.aba_geometria = QWidget()
        layout_geometria = QVBoxLayout(self.aba_geometria)

        layout_geometria.addWidget(QLabel("Nome do Objeto:"))
        self.input_nome = QLineEdit(nome)
        if modo_edicao:
            self.input_nome.setReadOnly(True)
            self.input_nome.setStyleSheet("background-color: #E0E0E0;")
        layout_geometria.addWidget(self.input_nome)

        # Seletor de tipo
        layout_geometria.addWidget(QLabel("Tipo do objeto:"))
        self.combo_tipo_objeto = QComboBox()
        self.combo_tipo_objeto.addItems(["Automático", "Curva de Bézier", "B-Spline"])
        if tipo_atual == "Curva2D":
            self.combo_tipo_objeto.setCurrentText("Curva de Bézier")
        if tipo_atual == "BSpline2D":
            self.combo_tipo_objeto.setCurrentText("B-Spline")
        self.combo_tipo_objeto.currentIndexChanged.connect(self._atualizar_visibilidade_por_tipo)
        layout_geometria.addWidget(self.combo_tipo_objeto)

        layout_geometria.addWidget(QLabel("Coordenadas [(x1, y1), (x2, y2)...]:"))
        self.input_coords = QLineEdit(coords)
        layout_geometria.addWidget(self.input_coords)

        # --- Seletor de Cores ---
        layout_geometria.addWidget(QLabel("Cor do Traço:"))
        layout_cores = QHBoxLayout()
        self.grupo_cores = QButtonGroup(self)

        self.lista_cores = ["#000000", "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#FFA500"]

        for i, cor in enumerate(self.lista_cores):
            btn_cor = QPushButton()
            btn_cor.setFixedSize(20, 20)
            btn_cor.setStyleSheet(f"""
                QPushButton {{ background-color: {cor}; border: 2px outset #FFFFFF; border-bottom-color: #808080; border-right-color: #808080; }}
                QPushButton:checked {{ border: 2px inset #000000; border-bottom-color: #FFFFFF; border-right-color: #FFFFFF; }}
            """)
            btn_cor.setCheckable(True)
            self.grupo_cores.addButton(btn_cor, i)
            layout_cores.addWidget(btn_cor)

            if cor == cor_atual:
                btn_cor.setChecked(True)

        if self.grupo_cores.checkedId() == -1:
            self.grupo_cores.button(0).setChecked(True)

        layout_cores.addStretch()
        layout_geometria.addLayout(layout_cores)

        # Checkbox de preenchimento (visível apenas para wireframes)
        self.check_preenchido = QCheckBox("Preencher wireframe com cor")
        self.check_preenchido.setChecked(preenchido)
        self.check_preenchido.setVisible(False)
        layout_geometria.addWidget(self.check_preenchido)

        # Atualiza visibilidade do checkbox ao editar coordenadas
        self.input_coords.textChanged.connect(self._atualizar_check_preenchido)
        if coords:
            self._atualizar_check_preenchido(coords)

        layout_geometria.addStretch()

        self.abas.addTab(self.aba_geometria, "Geometria")

        # Aba 2: Transformações 2D
        self.aba_transformacoes = QWidget()
        layout_transf = QVBoxLayout(self.aba_transformacoes)

        # --- Seletor de tipo de transformação ---
        layout_tipo = QHBoxLayout()
        layout_tipo.addWidget(QLabel("Tipo:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Translação", "Escalonamento", "Rotação"])
        self.combo_tipo.currentIndexChanged.connect(self.atualizar_campos_transformacao)
        layout_tipo.addWidget(self.combo_tipo)
        layout_transf.addLayout(layout_tipo)

        self.grupo_campos = QGroupBox("Parâmetros")
        self.layout_campos = QVBoxLayout(self.grupo_campos)

        # Campos de Translação
        self.widget_translacao = QWidget()
        lt = QHBoxLayout(self.widget_translacao)
        lt.setContentsMargins(0, 0, 0, 0)
        lt.addWidget(QLabel("Dx:"))
        self.input_dx = QLineEdit("0")
        self.input_dx.setFixedWidth(60)
        lt.addWidget(self.input_dx)
        lt.addWidget(QLabel("Dy:"))
        self.input_dy = QLineEdit("0")
        self.input_dy.setFixedWidth(60)
        lt.addWidget(self.input_dy)
        lt.addStretch()

        # Campos de Escalonamento
        self.widget_escalonamento = QWidget()
        le = QHBoxLayout(self.widget_escalonamento)
        le.setContentsMargins(0, 0, 0, 0)
        le.addWidget(QLabel("Sx:"))
        self.input_sx = QLineEdit("1")
        self.input_sx.setFixedWidth(60)
        le.addWidget(self.input_sx)
        le.addWidget(QLabel("Sy:"))
        self.input_sy = QLineEdit("1")
        self.input_sy.setFixedWidth(60)
        le.addWidget(self.input_sy)
        le.addStretch()

        # Campos de Rotação
        self.widget_rotacao = QWidget()
        lr = QVBoxLayout(self.widget_rotacao)
        lr.setContentsMargins(0, 0, 0, 0)

        linha_angulo = QHBoxLayout()
        linha_angulo.addWidget(QLabel("Ângulo (graus):"))
        self.input_angulo = QLineEdit("0")
        self.input_angulo.setFixedWidth(60)
        linha_angulo.addWidget(self.input_angulo)
        linha_angulo.addStretch()
        lr.addLayout(linha_angulo)

        self.radio_centro_mundo = QRadioButton("Em torno do center do mundo")
        self.radio_centro_objeto = QRadioButton("Em torno do center do objeto")
        self.radio_ponto_arb = QRadioButton("Em torno de um ponto arbitrário")
        self.radio_centro_objeto.setChecked(True)

        lr.addWidget(self.radio_centro_mundo)
        lr.addWidget(self.radio_centro_objeto)
        lr.addWidget(self.radio_ponto_arb)

        linha_ponto = QHBoxLayout()
        linha_ponto.addWidget(QLabel("   Px:"))
        self.input_px = QLineEdit("0")
        self.input_px.setFixedWidth(60)
        linha_ponto.addWidget(self.input_px)
        linha_ponto.addWidget(QLabel("Py:"))
        self.input_py = QLineEdit("0")
        self.input_py.setFixedWidth(60)
        linha_ponto.addWidget(self.input_py)
        linha_ponto.addStretch()
        lr.addLayout(linha_ponto)

        self.radio_ponto_arb.toggled.connect(self.toggle_ponto_arbitrario)
        self.input_px.setEnabled(False)
        self.input_py.setEnabled(False)

        self.layout_campos.addWidget(self.widget_translacao)
        self.layout_campos.addWidget(self.widget_escalonamento)
        self.layout_campos.addWidget(self.widget_rotacao)

        layout_transf.addWidget(self.grupo_campos)

        # Botão para adicionar transformação à lista
        btn_add_transf = QPushButton("Adicionar à lista ▼")
        btn_add_transf.clicked.connect(self.adicionar_transformacao)
        layout_transf.addWidget(btn_add_transf)

        # Lista de transformações acumuladas
        layout_transf.addWidget(QLabel("Transformações a aplicar:"))
        self.lista_transf_widget = QListWidget()
        self.lista_transf_widget.setMaximumHeight(100)
        layout_transf.addWidget(self.lista_transf_widget)

        # Botão para remover transformação da lista
        btn_rem_transf = QPushButton("Remover selecionada")
        btn_rem_transf.clicked.connect(self.remover_transformacao)
        layout_transf.addWidget(btn_rem_transf)

        self.abas.addTab(self.aba_transformacoes, "Transformações 2D")

        if not modo_edicao:
            self.abas.setTabEnabled(1, False)

        self.atualizar_campos_transformacao(0)

        # Botoes de Acao Inferiores
        layout_botoes = QHBoxLayout()
        if modo_edicao:
            btn_apagar = QPushButton("Apagar")
            btn_apagar.clicked.connect(self.acao_apagar)
            layout_botoes.addWidget(btn_apagar)

        layout_botoes.addStretch()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        layout_botoes.addWidget(btn_ok)
        layout_botoes.addWidget(btn_cancelar)
        layout_principal.addLayout(layout_botoes)

    def toggle_ponto_arbitrario(self, checked):
        self.input_px.setEnabled(checked)
        self.input_py.setEnabled(checked)

    def atualizar_campos_transformacao(self, index):
        """Mostra/esconde os campos conforme o tipo de transformação selecionado."""
        self.widget_translacao.setVisible(index == 0)
        self.widget_escalonamento.setVisible(index == 1)
        self.widget_rotacao.setVisible(index == 2)

    def adicionar_transformacao(self):
        """Adiciona a transformação atual à lista de transformações."""
        try:
            tipo_idx = self.combo_tipo.currentIndex()
            if tipo_idx == 0:  # Translação
                dx = float(self.input_dx.text())
                dy = float(self.input_dy.text())
                self.lista_transformacoes.append(("translacao", dx, dy))
                self.lista_transf_widget.addItem(f"Translação (dx={dx}, dy={dy})")

            elif tipo_idx == 1:  # Escalonamento
                sx = float(self.input_sx.text())
                sy = float(self.input_sy.text())
                self.lista_transformacoes.append(("escalonamento", sx, sy))
                self.lista_transf_widget.addItem(f"Escalonamento (sx={sx}, sy={sy})")

            elif tipo_idx == 2:  # Rotação
                angulo = float(self.input_angulo.text())
                if self.radio_centro_mundo.isChecked():
                    self.lista_transformacoes.append(("rotacao_origem", angulo))
                    self.lista_transf_widget.addItem(f"Rotação {angulo}° (center do mundo)")
                elif self.radio_centro_objeto.isChecked():
                    self.lista_transformacoes.append(("rotacao_centro", angulo))
                    self.lista_transf_widget.addItem(f"Rotação {angulo}° (center do objeto)")
                elif self.radio_ponto_arb.isChecked():
                    px = float(self.input_px.text())
                    py = float(self.input_py.text())
                    self.lista_transformacoes.append(("rotacao_ponto", angulo, px, py))
                    self.lista_transf_widget.addItem(f"Rotação {angulo}° (ponto ({px},{py}))")
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valores numéricos inválidos.")

    def remover_transformacao(self):
        """Remove a transformação selecionada da lista."""
        row = self.lista_transf_widget.currentRow()
        if row >= 0:
            self.lista_transf_widget.takeItem(row)
            self.lista_transformacoes.pop(row)

    def acao_apagar(self):
        self.apagar_solicitado = True
        self.accept()

    def _atualizar_check_preenchido(self, texto):
        """Mostra o checkbox de preenchimento apenas para wireframes (>2 coords, tipo Automático)."""
        tipo = self.combo_tipo_objeto.currentText()
        if tipo in ("Curva de Bézier", "B-Spline"):
            self.check_preenchido.setVisible(False)
            return
        try:
            coords = list(eval(f"[{texto}]"))
            self.check_preenchido.setVisible(len(coords) > 2)
        except:
            self.check_preenchido.setVisible(False)

    def _atualizar_visibilidade_por_tipo(self, _index):
        """Re-avalia a visibilidade do checkbox quando o tipo muda."""
        self._atualizar_check_preenchido(self.input_coords.text())

    def obter_dados(self):
        id_cor = self.grupo_cores.checkedId()
        cor_selecionada = self.lista_cores[id_cor] if id_cor != -1 else "#000000"
        tipo = self.combo_tipo_objeto.currentText()
        return (self.input_nome.text(), self.input_coords.text(), cor_selecionada,
                self.check_preenchido.isChecked(), tipo)

    def obter_transformacoes(self):
        """Retorna a lista de transformações acumuladas."""
        return self.lista_transformacoes


class JanelaObjeto3DDialog(QDialog):
    """Diálogo para criar/editar Objeto3D (modelo de arame 3D)."""

    def __init__(self, parent=None, nome="", segmentos_str="", cor_atual="#000000", modo_edicao=False):
        super().__init__(parent)
        self.setWindowTitle("Propriedades Objeto 3D" if modo_edicao else "Novo Objeto 3D")
        self.setFixedSize(520, 500)
        self.modo_edicao = modo_edicao
        self.apagar_solicitado = False
        self.lista_transformacoes = []

        layout_principal = QVBoxLayout(self)
        self.abas = QTabWidget()
        layout_principal.addWidget(self.abas)

        # --- Aba Geometria ---
        aba_geo = QWidget()
        layout_geo = QVBoxLayout(aba_geo)

        layout_geo.addWidget(QLabel("Nome:"))
        self.input_nome = QLineEdit(nome)
        if modo_edicao:
            self.input_nome.setReadOnly(True)
            self.input_nome.setStyleSheet("background-color: #E0E0E0;")
        layout_geo.addWidget(self.input_nome)

        layout_geo.addWidget(QLabel("Segmentos  [(x1,y1,z1)-(x2,y2,z2), ...]:"))
        self.input_segs = QLineEdit(segmentos_str)
        self.input_segs.setPlaceholderText("(0,0,0)-(1,0,0), (1,0,0)-(1,1,0)")
        layout_geo.addWidget(self.input_segs)

        layout_geo.addWidget(QLabel("Cor do Traço:"))
        layout_cores = QHBoxLayout()
        self.grupo_cores = QButtonGroup(self)
        self.lista_cores = ["#000000", "#FF0000", "#00FF00", "#0000FF",
                            "#FFFF00", "#FF00FF", "#00FFFF", "#FFA500"]
        for i, cor in enumerate(self.lista_cores):
            btn = QPushButton()
            btn.setFixedSize(20, 20)
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: {cor}; border: 2px outset #FFFFFF;
                               border-bottom-color: #808080; border-right-color: #808080; }}
                QPushButton:checked {{ border: 2px inset #000000;
                                       border-bottom-color: #FFFFFF; border-right-color: #FFFFFF; }}
            """)
            btn.setCheckable(True)
            self.grupo_cores.addButton(btn, i)
            layout_cores.addWidget(btn)
            if cor == cor_atual:
                btn.setChecked(True)
        if self.grupo_cores.checkedId() == -1:
            self.grupo_cores.button(0).setChecked(True)
        layout_cores.addStretch()
        layout_geo.addLayout(layout_cores)
        layout_geo.addStretch()
        self.abas.addTab(aba_geo, "Geometria")

        # --- Aba Transformações 3D ---
        aba_transf = QWidget()
        layout_transf = QVBoxLayout(aba_transf)

        linha_tipo = QHBoxLayout()
        linha_tipo.addWidget(QLabel("Tipo:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Translação", "Escalonamento", "Rotação"])
        self.combo_tipo.currentIndexChanged.connect(self._atualizar_campos)
        linha_tipo.addWidget(self.combo_tipo)
        layout_transf.addLayout(linha_tipo)

        self.grupo_campos = QGroupBox("Parâmetros")
        layout_campos = QVBoxLayout(self.grupo_campos)

        # Translação
        self.widget_trl = QWidget()
        lt = QHBoxLayout(self.widget_trl); lt.setContentsMargins(0,0,0,0)
        for lbl, attr in [("Dx:", "input_dx"), ("Dy:", "input_dy"), ("Dz:", "input_dz")]:
            lt.addWidget(QLabel(lbl))
            inp = QLineEdit("0"); inp.setFixedWidth(55)
            setattr(self, attr, inp); lt.addWidget(inp)
        lt.addStretch()

        # Escalonamento
        self.widget_esc = QWidget()
        le = QHBoxLayout(self.widget_esc); le.setContentsMargins(0,0,0,0)
        for lbl, attr in [("Sx:", "input_sx"), ("Sy:", "input_sy"), ("Sz:", "input_sz")]:
            le.addWidget(QLabel(lbl))
            inp = QLineEdit("1"); inp.setFixedWidth(55)
            setattr(self, attr, inp); le.addWidget(inp)
        le.addStretch()

        # Rotação
        self.widget_rot = QWidget()
        lr = QVBoxLayout(self.widget_rot); lr.setContentsMargins(0,0,0,0)
        linha_ang = QHBoxLayout()
        linha_ang.addWidget(QLabel("Ângulo (°):"))
        self.input_angulo = QLineEdit("0"); self.input_angulo.setFixedWidth(60)
        linha_ang.addWidget(self.input_angulo); linha_ang.addStretch()
        lr.addLayout(linha_ang)
        self.radio_eixo_x = QRadioButton("Eixo X (centro obj)")
        self.radio_eixo_y = QRadioButton("Eixo Y (centro obj)")
        self.radio_eixo_z = QRadioButton("Eixo Z (centro obj)")
        self.radio_arb   = QRadioButton("Eixo arbitrário")
        self.radio_eixo_z.setChecked(True)
        for r in [self.radio_eixo_x, self.radio_eixo_y, self.radio_eixo_z, self.radio_arb]:
            lr.addWidget(r)
        self.radio_arb.toggled.connect(self._toggle_arb)

        self.widget_arb = QWidget()
        la = QHBoxLayout(self.widget_arb); la.setContentsMargins(0,0,0,0)
        la.addWidget(QLabel("Eixo (ax,ay,az):"))
        self.input_eixo = QLineEdit("0,0,1"); self.input_eixo.setFixedWidth(80)
        la.addWidget(self.input_eixo)
        la.addWidget(QLabel("  Ponto (px,py,pz):"))
        self.input_ponto_eixo = QLineEdit("0,0,0"); self.input_ponto_eixo.setFixedWidth(80)
        la.addWidget(self.input_ponto_eixo); la.addStretch()
        self.widget_arb.setEnabled(False)
        lr.addWidget(self.widget_arb)

        layout_campos.addWidget(self.widget_trl)
        layout_campos.addWidget(self.widget_esc)
        layout_campos.addWidget(self.widget_rot)
        layout_transf.addWidget(self.grupo_campos)

        btn_add = QPushButton("Adicionar à lista ▼")
        btn_add.clicked.connect(self._adicionar_transformacao)
        layout_transf.addWidget(btn_add)

        layout_transf.addWidget(QLabel("Transformações a aplicar:"))
        self.lista_transf_widget = QListWidget()
        self.lista_transf_widget.setMaximumHeight(100)
        layout_transf.addWidget(self.lista_transf_widget)

        btn_rem = QPushButton("Remover selecionada")
        btn_rem.clicked.connect(self._remover_transformacao)
        layout_transf.addWidget(btn_rem)

        self.abas.addTab(aba_transf, "Transformações 3D")
        if not modo_edicao:
            self.abas.setTabEnabled(1, False)

        self._atualizar_campos(0)

        # Botões OK/Cancelar
        layout_btns = QHBoxLayout()
        if modo_edicao:
            btn_apagar = QPushButton("Apagar")
            btn_apagar.clicked.connect(self._acao_apagar)
            layout_btns.addWidget(btn_apagar)
        layout_btns.addStretch()
        btn_ok = QPushButton("OK"); btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancelar"); btn_cancel.clicked.connect(self.reject)
        layout_btns.addWidget(btn_ok); layout_btns.addWidget(btn_cancel)
        layout_principal.addLayout(layout_btns)

    def _toggle_arb(self, checked):
        self.widget_arb.setEnabled(checked)

    def _atualizar_campos(self, index):
        self.widget_trl.setVisible(index == 0)
        self.widget_esc.setVisible(index == 1)
        self.widget_rot.setVisible(index == 2)

    def _adicionar_transformacao(self):
        try:
            idx = self.combo_tipo.currentIndex()
            if idx == 0:
                dx = float(self.input_dx.text())
                dy = float(self.input_dy.text())
                dz = float(self.input_dz.text())
                self.lista_transformacoes.append(("translacao", dx, dy, dz))
                self.lista_transf_widget.addItem(f"Translação ({dx},{dy},{dz})")
            elif idx == 1:
                sx = float(self.input_sx.text())
                sy = float(self.input_sy.text())
                sz = float(self.input_sz.text())
                self.lista_transformacoes.append(("escalonamento", sx, sy, sz))
                self.lista_transf_widget.addItem(f"Escalonamento ({sx},{sy},{sz})")
            elif idx == 2:
                ang = float(self.input_angulo.text())
                if self.radio_eixo_x.isChecked():
                    self.lista_transformacoes.append(("rotacao_x", ang))
                    self.lista_transf_widget.addItem(f"Rotação X {ang}°")
                elif self.radio_eixo_y.isChecked():
                    self.lista_transformacoes.append(("rotacao_y", ang))
                    self.lista_transf_widget.addItem(f"Rotação Y {ang}°")
                elif self.radio_eixo_z.isChecked():
                    self.lista_transformacoes.append(("rotacao_z", ang))
                    self.lista_transf_widget.addItem(f"Rotação Z {ang}°")
                elif self.radio_arb.isChecked():
                    parts_e = [float(v) for v in self.input_eixo.text().split(",")]
                    parts_p = [float(v) for v in self.input_ponto_eixo.text().split(",")]
                    eixo = tuple(parts_e)
                    ponto = tuple(parts_p)
                    self.lista_transformacoes.append(("rotacao_arbitraria", ang, eixo, ponto))
                    self.lista_transf_widget.addItem(f"Rot. Arb. {ang}° eixo{eixo} pt{ponto}")
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valores numéricos inválidos.")

    def _remover_transformacao(self):
        row = self.lista_transf_widget.currentRow()
        if row >= 0:
            self.lista_transf_widget.takeItem(row)
            self.lista_transformacoes.pop(row)

    def _acao_apagar(self):
        self.apagar_solicitado = True
        self.accept()

    def obter_dados(self):
        id_cor = self.grupo_cores.checkedId()
        cor = self.lista_cores[id_cor] if id_cor != -1 else "#000000"
        return self.input_nome.text(), self.input_segs.text(), cor

    def obter_transformacoes(self):
        return self.lista_transformacoes


class JanelaSuperficieBSplineDialog(QDialog):
    """Dialogo para criar/editar superficies bicubicas B-Spline."""

    def __init__(self, parent=None, nome="", matriz_str="", cor_atual="#000000",
                 passos=10, modo_edicao=False):
        super().__init__(parent)
        self.setWindowTitle("Propriedades Superficie B-Spline" if modo_edicao else "Nova Superficie B-Spline")
        self.setFixedSize(620, 620)
        self.modo_edicao = modo_edicao
        self.apagar_solicitado = False
        self.lista_transformacoes = []

        layout_principal = QVBoxLayout(self)
        self.abas = QTabWidget()
        layout_principal.addWidget(self.abas)

        aba_geo = QWidget()
        layout_geo = QVBoxLayout(aba_geo)
        layout_geo.addWidget(QLabel("Nome:"))
        self.input_nome = QLineEdit(nome)
        if modo_edicao:
            self.input_nome.setReadOnly(True)
            self.input_nome.setStyleSheet("background-color: #E0E0E0;")
        layout_geo.addWidget(self.input_nome)

        layout_geo.addWidget(QLabel("Matriz de controle 4x4 ate 20x20. Separe linhas com ';':"))
        self.input_matriz = QTextEdit()
        self.input_matriz.setPlainText(matriz_str)
        self.input_matriz.setPlaceholderText("(x11,y11,z11), (x12,y12,z12), ...;\n(x21,y21,z21), ...")
        layout_geo.addWidget(self.input_matriz)

        linha_passos = QHBoxLayout()
        linha_passos.addWidget(QLabel("Passos por patch:"))
        self.input_passos = QLineEdit(str(passos))
        self.input_passos.setFixedWidth(60)
        linha_passos.addWidget(self.input_passos)
        linha_passos.addStretch()
        layout_geo.addLayout(linha_passos)

        layout_geo.addWidget(QLabel("Cor do Traço:"))
        layout_cores = QHBoxLayout()
        self.grupo_cores = QButtonGroup(self)
        self.lista_cores = ["#000000", "#FF0000", "#00FF00", "#0000FF",
                            "#FFFF00", "#FF00FF", "#00FFFF", "#FFA500"]
        for i, cor in enumerate(self.lista_cores):
            btn = QPushButton()
            btn.setFixedSize(20, 20)
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: {cor}; border: 2px outset #FFFFFF;
                               border-bottom-color: #808080; border-right-color: #808080; }}
                QPushButton:checked {{ border: 2px inset #000000;
                                       border-bottom-color: #FFFFFF; border-right-color: #FFFFFF; }}
            """)
            btn.setCheckable(True)
            self.grupo_cores.addButton(btn, i)
            layout_cores.addWidget(btn)
            if cor == cor_atual:
                btn.setChecked(True)
        if self.grupo_cores.checkedId() == -1:
            self.grupo_cores.button(0).setChecked(True)
        layout_cores.addStretch()
        layout_geo.addLayout(layout_cores)
        self.abas.addTab(aba_geo, "Geometria")

        aba_transf = QWidget()
        layout_transf = QVBoxLayout(aba_transf)
        linha_tipo = QHBoxLayout()
        linha_tipo.addWidget(QLabel("Tipo:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Translação", "Escalonamento", "Rotação"])
        self.combo_tipo.currentIndexChanged.connect(self._atualizar_campos)
        linha_tipo.addWidget(self.combo_tipo)
        layout_transf.addLayout(linha_tipo)

        self.grupo_campos = QGroupBox("Parâmetros")
        layout_campos = QVBoxLayout(self.grupo_campos)
        self.widget_trl = QWidget()
        lt = QHBoxLayout(self.widget_trl); lt.setContentsMargins(0, 0, 0, 0)
        for lbl, attr in [("Dx:", "input_dx"), ("Dy:", "input_dy"), ("Dz:", "input_dz")]:
            lt.addWidget(QLabel(lbl))
            inp = QLineEdit("0"); inp.setFixedWidth(55)
            setattr(self, attr, inp); lt.addWidget(inp)
        lt.addStretch()

        self.widget_esc = QWidget()
        le = QHBoxLayout(self.widget_esc); le.setContentsMargins(0, 0, 0, 0)
        for lbl, attr in [("Sx:", "input_sx"), ("Sy:", "input_sy"), ("Sz:", "input_sz")]:
            le.addWidget(QLabel(lbl))
            inp = QLineEdit("1"); inp.setFixedWidth(55)
            setattr(self, attr, inp); le.addWidget(inp)
        le.addStretch()

        self.widget_rot = QWidget()
        lr = QVBoxLayout(self.widget_rot); lr.setContentsMargins(0, 0, 0, 0)
        linha_ang = QHBoxLayout()
        linha_ang.addWidget(QLabel("Ângulo (°):"))
        self.input_angulo = QLineEdit("0"); self.input_angulo.setFixedWidth(60)
        linha_ang.addWidget(self.input_angulo); linha_ang.addStretch()
        lr.addLayout(linha_ang)
        self.radio_eixo_x = QRadioButton("Eixo X (centro obj)")
        self.radio_eixo_y = QRadioButton("Eixo Y (centro obj)")
        self.radio_eixo_z = QRadioButton("Eixo Z (centro obj)")
        self.radio_arb = QRadioButton("Eixo arbitrário")
        self.radio_eixo_z.setChecked(True)
        for radio in [self.radio_eixo_x, self.radio_eixo_y, self.radio_eixo_z, self.radio_arb]:
            lr.addWidget(radio)
        self.radio_arb.toggled.connect(self._toggle_arb)
        self.widget_arb = QWidget()
        la = QHBoxLayout(self.widget_arb); la.setContentsMargins(0, 0, 0, 0)
        la.addWidget(QLabel("Eixo (ax,ay,az):"))
        self.input_eixo = QLineEdit("0,0,1"); self.input_eixo.setFixedWidth(80)
        la.addWidget(self.input_eixo)
        la.addWidget(QLabel("Ponto (px,py,pz):"))
        self.input_ponto_eixo = QLineEdit("0,0,0"); self.input_ponto_eixo.setFixedWidth(80)
        la.addWidget(self.input_ponto_eixo); la.addStretch()
        self.widget_arb.setEnabled(False)
        lr.addWidget(self.widget_arb)

        layout_campos.addWidget(self.widget_trl)
        layout_campos.addWidget(self.widget_esc)
        layout_campos.addWidget(self.widget_rot)
        layout_transf.addWidget(self.grupo_campos)

        btn_add = QPushButton("Adicionar à lista ▼")
        btn_add.clicked.connect(self._adicionar_transformacao)
        layout_transf.addWidget(btn_add)
        layout_transf.addWidget(QLabel("Transformações a aplicar:"))
        self.lista_transf_widget = QListWidget()
        self.lista_transf_widget.setMaximumHeight(100)
        layout_transf.addWidget(self.lista_transf_widget)
        btn_rem = QPushButton("Remover selecionada")
        btn_rem.clicked.connect(self._remover_transformacao)
        layout_transf.addWidget(btn_rem)
        self.abas.addTab(aba_transf, "Transformações 3D")
        if not modo_edicao:
            self.abas.setTabEnabled(1, False)
        self._atualizar_campos(0)

        layout_btns = QHBoxLayout()
        if modo_edicao:
            btn_apagar = QPushButton("Apagar")
            btn_apagar.clicked.connect(self._acao_apagar)
            layout_btns.addWidget(btn_apagar)
        layout_btns.addStretch()
        btn_ok = QPushButton("OK"); btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancelar"); btn_cancel.clicked.connect(self.reject)
        layout_btns.addWidget(btn_ok); layout_btns.addWidget(btn_cancel)
        layout_principal.addLayout(layout_btns)

    def _toggle_arb(self, checked):
        self.widget_arb.setEnabled(checked)

    def _atualizar_campos(self, index):
        self.widget_trl.setVisible(index == 0)
        self.widget_esc.setVisible(index == 1)
        self.widget_rot.setVisible(index == 2)

    def _adicionar_transformacao(self):
        try:
            idx = self.combo_tipo.currentIndex()
            if idx == 0:
                dx = float(self.input_dx.text())
                dy = float(self.input_dy.text())
                dz = float(self.input_dz.text())
                self.lista_transformacoes.append(("translacao", dx, dy, dz))
                self.lista_transf_widget.addItem(f"Translação ({dx},{dy},{dz})")
            elif idx == 1:
                sx = float(self.input_sx.text())
                sy = float(self.input_sy.text())
                sz = float(self.input_sz.text())
                self.lista_transformacoes.append(("escalonamento", sx, sy, sz))
                self.lista_transf_widget.addItem(f"Escalonamento ({sx},{sy},{sz})")
            elif idx == 2:
                ang = float(self.input_angulo.text())
                if self.radio_eixo_x.isChecked():
                    self.lista_transformacoes.append(("rotacao_x", ang))
                    self.lista_transf_widget.addItem(f"Rotação X {ang}°")
                elif self.radio_eixo_y.isChecked():
                    self.lista_transformacoes.append(("rotacao_y", ang))
                    self.lista_transf_widget.addItem(f"Rotação Y {ang}°")
                elif self.radio_eixo_z.isChecked():
                    self.lista_transformacoes.append(("rotacao_z", ang))
                    self.lista_transf_widget.addItem(f"Rotação Z {ang}°")
                elif self.radio_arb.isChecked():
                    eixo = tuple(float(v) for v in self.input_eixo.text().split(","))
                    ponto = tuple(float(v) for v in self.input_ponto_eixo.text().split(","))
                    self.lista_transformacoes.append(("rotacao_arbitraria", ang, eixo, ponto))
                    self.lista_transf_widget.addItem(f"Rot. Arb. {ang}° eixo{eixo} pt{ponto}")
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valores numéricos inválidos.")

    def _remover_transformacao(self):
        row = self.lista_transf_widget.currentRow()
        if row >= 0:
            self.lista_transf_widget.takeItem(row)
            self.lista_transformacoes.pop(row)

    def _acao_apagar(self):
        self.apagar_solicitado = True
        self.accept()

    def obter_dados(self):
        id_cor = self.grupo_cores.checkedId()
        cor = self.lista_cores[id_cor] if id_cor != -1 else "#000000"
        passos = int(self.input_passos.text())
        return self.input_nome.text(), self.input_matriz.toPlainText(), cor, passos

    def obter_transformacoes(self):
        return self.lista_transformacoes


# --- CLASSE DA JANELA PRINCIPAL ---

class MainWindow(QMainWindow):
    def __init__(self, display_file, window_obj, viewport, window3d):
        super().__init__()
        self.display_file = display_file
        self.window_obj = window_obj
        self.viewport = viewport
        self.window3d = window3d
        self.transform = Transform()

        self.setWindowTitle("Sistema Grafico Interativo - V1.8")
        self.setGeometry(80, 80, 1280, 680)

        self.aplicar_tema()
        self.setup_ui()
        self._carregar_cena_inicial()

    def aplicar_tema(self):
        estilo = """
            QWidget {
                background-color: #D4D0C8;
                color: black;
                font-family: 'MS Sans Serif', Arial, sans-serif;
                font-size: 12px;
            }
            QPushButton {
                border: 2px outset #FFFFFF;
                border-bottom-color: #808080;
                border-right-color: #808080;
                background-color: #D4D0C8;
                padding: 4px 8px;
            }
            QPushButton:pressed {
                border: 2px inset #FFFFFF;
                border-bottom-color: #808080;
                border-right-color: #808080;
            }
            QLineEdit, QListWidget, QWidget#AreaCanvas {
                border: 2px inset #808080;
                border-bottom-color: #FFFFFF;
                border-right-color: #FFFFFF;
                background-color: white;
            }
            QGroupBox {
                border: 2px groove #808080;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QTabWidget::pane {
                border: 2px outset #FFFFFF;
                border-bottom-color: #808080;
                border-right-color: #808080;
            }
            QComboBox {
                border: 2px inset #808080;
                border-bottom-color: #FFFFFF;
                border-right-color: #FFFFFF;
                background-color: white;
                padding: 2px 4px;
            }
        """
        self.setStyleSheet(estilo)

    def setup_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setCentralWidget(main_widget)

        # ESQUERDA: Painel de Controle em duas colunas (cabe em tela de laptop)
        painel_container = QHBoxLayout()
        main_layout.addLayout(painel_container, stretch=3)
        coluna_esq = QVBoxLayout()
        coluna_dir = QVBoxLayout()
        painel_container.addLayout(coluna_esq)
        painel_container.addLayout(coluna_dir)

        # --- Grupo 1: Objetos ---
        grupo_objetos = QGroupBox("Objetos")
        layout_objetos = QVBoxLayout(grupo_objetos)

        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(110)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.abrir_menu_contexto)
        self.list_widget.itemDoubleClicked.connect(self.editar_objeto_selecionado)
        layout_objetos.addWidget(self.list_widget)

        botoes_lista_layout = QHBoxLayout()
        btn_novo = QPushButton("Novo...")
        btn_novo.clicked.connect(self.abrir_dialogo_novo_objeto)
        btn_editar = QPushButton("Editar...")
        btn_editar.clicked.connect(self.editar_objeto_selecionado)

        botoes_lista_layout.addWidget(btn_novo)
        botoes_lista_layout.addWidget(btn_editar)
        layout_objetos.addLayout(botoes_lista_layout)

        coluna_esq.addWidget(grupo_objetos)

        # --- Grupo: Objetos 3D ---
        grupo_3d = QGroupBox("Objetos 3D")
        layout_3d = QVBoxLayout(grupo_3d)

        self.list_widget_3d = QListWidget()
        self.list_widget_3d.setMaximumHeight(110)
        self.list_widget_3d.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget_3d.customContextMenuRequested.connect(self._menu_contexto_3d)
        self.list_widget_3d.itemDoubleClicked.connect(self._editar_objeto_3d)
        layout_3d.addWidget(self.list_widget_3d)

        botoes_3d = QHBoxLayout()
        btn_novo_3d = QPushButton("Novo 3D...")
        btn_novo_3d.clicked.connect(self._novo_objeto_3d)
        btn_editar_3d = QPushButton("Editar 3D...")
        btn_editar_3d.clicked.connect(self._editar_objeto_3d)
        botoes_3d.addWidget(btn_novo_3d)
        botoes_3d.addWidget(btn_editar_3d)
        layout_3d.addLayout(botoes_3d)

        botoes_superficie = QHBoxLayout()
        btn_nova_superficie = QPushButton("Nova Sup. B-Spline...")
        btn_nova_superficie.clicked.connect(self._nova_superficie_bspline)
        botoes_superficie.addWidget(btn_nova_superficie)
        layout_3d.addLayout(botoes_superficie)

        coluna_esq.addWidget(grupo_3d)

        # --- Grupo: Arquivo (2D + 3D) ---
        grupo_arquivo = QGroupBox("Arquivo (2D + 3D)")
        botoes_obj_layout = QHBoxLayout(grupo_arquivo)
        btn_importar = QPushButton("Importar .obj")
        btn_importar.clicked.connect(self.importar_obj)
        btn_exportar = QPushButton("Exportar .obj")
        btn_exportar.clicked.connect(self.exportar_obj)
        botoes_obj_layout.addWidget(btn_importar)
        botoes_obj_layout.addWidget(btn_exportar)

        coluna_esq.addWidget(grupo_arquivo)

        # --- Grupo: Navegação ---
        grupo_nav = QGroupBox("Navegação")
        layout_nav = QVBoxLayout(grupo_nav)

        linha_passo = QHBoxLayout()
        linha_passo.addWidget(QLabel("Passo:"))
        self.input_passo = QLineEdit("10")
        self.input_passo.setFixedWidth(50)
        linha_passo.addWidget(self.input_passo)
        linha_passo.addStretch()
        layout_nav.addLayout(linha_passo)

        # Translação
        layout_nav.addWidget(QLabel("Translação"))
        grid_trl = QGridLayout()
        btn_y_pos = QPushButton("▲ Y")
        btn_x_neg = QPushButton("◄ X")
        btn_x_pos = QPushButton("X ►")
        btn_y_neg = QPushButton("▼ Y")
        btn_y_pos.clicked.connect(self._mover_y_pos)
        btn_x_neg.clicked.connect(self._mover_x_neg)
        btn_x_pos.clicked.connect(self._mover_x_pos)
        btn_y_neg.clicked.connect(self._mover_y_neg)
        grid_trl.addWidget(btn_y_pos, 0, 1)
        grid_trl.addWidget(btn_x_neg, 1, 0)
        grid_trl.addWidget(btn_x_pos, 1, 2)
        grid_trl.addWidget(btn_y_neg, 2, 1)
        layout_nav.addLayout(grid_trl)

        linha_z = QHBoxLayout()
        btn_z_pos = QPushButton("Z ↑ Aprox.")
        btn_z_neg = QPushButton("Z ↓ Afastar")
        btn_z_pos.clicked.connect(self._mover_z_pos)
        btn_z_neg.clicked.connect(self._mover_z_neg)
        linha_z.addWidget(btn_z_pos)
        linha_z.addWidget(btn_z_neg)
        layout_nav.addLayout(linha_z)

        # Rotação
        layout_nav.addWidget(QLabel("Rotação"))
        rot_grid = QGridLayout()
        btn_rx_neg = QPushButton("Rx−"); btn_rx_pos = QPushButton("Rx+")
        btn_ry_neg = QPushButton("Ry−"); btn_ry_pos = QPushButton("Ry+")
        btn_rz_neg = QPushButton("Rz−"); btn_rz_pos = QPushButton("Rz+")
        btn_rx_neg.clicked.connect(lambda: self._rot_u(-1))
        btn_rx_pos.clicked.connect(lambda: self._rot_u(1))
        btn_ry_neg.clicked.connect(lambda: self._rot_v(-1))
        btn_ry_pos.clicked.connect(lambda: self._rot_v(1))
        btn_rz_neg.clicked.connect(lambda: self._rot_n(-1))
        btn_rz_pos.clicked.connect(lambda: self._rot_n(1))
        rot_grid.addWidget(btn_rx_neg, 0, 1)
        rot_grid.addWidget(btn_rx_pos, 0, 2)
        rot_grid.addWidget(QLabel("Eixo X"), 0, 0)
        rot_grid.addWidget(btn_ry_neg, 1, 1)
        rot_grid.addWidget(btn_ry_pos, 1, 2)
        rot_grid.addWidget(QLabel("Eixo Y"), 1, 0)
        rot_grid.addWidget(btn_rz_neg, 2, 1)
        rot_grid.addWidget(btn_rz_pos, 2, 2)
        rot_grid.addWidget(QLabel("Eixo Z"), 2, 0)
        layout_nav.addLayout(rot_grid)

        # Zoom (escala)
        zoom_row = QHBoxLayout()
        btn_zoom_in = QPushButton("Zoom +")
        btn_zoom_out = QPushButton("Zoom −")
        btn_zoom_in.clicked.connect(self._zoom_in)
        btn_zoom_out.clicked.connect(self._zoom_out)
        zoom_row.addWidget(btn_zoom_in)
        zoom_row.addWidget(btn_zoom_out)
        layout_nav.addLayout(zoom_row)

        coluna_esq.addWidget(grupo_nav)
        coluna_esq.addStretch()

        # --- Grupo 3: Clipping de Reta ---
        grupo_clip = QGroupBox("Clipping de Reta")
        clipping_layout = QVBoxLayout(grupo_clip)

        self.radio_cs = QRadioButton("Cohen-Sutherland")
        self.radio_lb = QRadioButton("Liang-Barsky")
        self.radio_cs.setChecked(True)

        self.radio_cs.toggled.connect(self._atualizar_algoritmo_clip)
        self.radio_lb.toggled.connect(self._atualizar_algoritmo_clip)

        clipping_layout.addWidget(self.radio_cs)
        clipping_layout.addWidget(self.radio_lb)
        coluna_dir.addWidget(grupo_clip)

        # --- Grupo: Perspectiva ---
        grupo_persp = QGroupBox("Projeção 3D")
        layout_persp = QVBoxLayout(grupo_persp)

        self.check_perspectiva = QCheckBox("Modo Perspectiva")
        self.check_perspectiva.setChecked(False)
        self.check_perspectiva.toggled.connect(self._toggle_perspectiva)
        layout_persp.addWidget(self.check_perspectiva)

        linha_d = QHBoxLayout()
        linha_d.addWidget(QLabel("d:"))
        self._slider_focal = QSlider(Qt.Orientation.Horizontal)
        self._slider_focal.setMinimum(50)
        self._slider_focal.setMaximum(5000)
        self._slider_focal.setValue(500)
        self._slider_focal.setTickInterval(500)
        self._slider_focal.valueChanged.connect(self._slider_focal_changed)
        linha_d.addWidget(self._slider_focal)
        self._label_d_valor = QLabel("500")
        self._label_d_valor.setFixedWidth(38)
        linha_d.addWidget(self._label_d_valor)
        layout_persp.addLayout(linha_d)

        self._label_modo_persp = QLabel("Modo: Normal  |  [ diminui  ] aumenta d")
        self._label_modo_persp.setWordWrap(True)
        layout_persp.addWidget(self._label_modo_persp)

        coluna_dir.addWidget(grupo_persp)

        # --- Grupo: Rasterização / Shading ---
        coluna_dir.addWidget(self._criar_grupo_shading())
        coluna_dir.addStretch()

        # DIREITA: Canvas (Viewport)
        grupo_viewport = QGroupBox("Viewport")

        layout_canvas = QVBoxLayout(grupo_viewport)
        layout_canvas.setContentsMargins(10, 15, 10, 10)

        self.canvas = Canvas(self.display_file, self.window_obj, self.viewport, self.window3d)

        self.canvas.setObjectName("AreaCanvas")
        self.canvas.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.canvas.setStyleSheet("")

        layout_canvas.addWidget(self.canvas)

        main_layout.addWidget(grupo_viewport, stretch=4)

    # --- Funções de Ação de Interface ---

    def abrir_dialogo_novo_objeto(self):
        dialogo = JanelaObjetoDialog(self)
        if dialogo.exec():
            nome, coords_str, cor, preenchido, tipo = dialogo.obter_dados()
            self.processar_adicao_objeto(nome, coords_str, cor, preenchido=preenchido, tipo=tipo)

    def editar_objeto_selecionado(self):
        item_atual = self.list_widget.currentItem()
        if not item_atual:
            QMessageBox.information(self, "Aviso", "Selecione um objeto na lista primeiro.")
            return

        nome_obj = item_atual.data(Qt.ItemDataRole.UserRole)
        obj_ref = next((obj for obj in self.display_file.obter_todos() if obj.nome == nome_obj), None)
        if not obj_ref: return

        coords_str = ", ".join([str(pt) for pt in obj_ref.pontos])

        preenchido_atual = getattr(obj_ref, 'preenchido', False)
        dialogo = JanelaObjetoDialog(self, nome=obj_ref.nome, coords=coords_str, cor_atual=obj_ref.cor,
                                     modo_edicao=True, preenchido=preenchido_atual, tipo_atual=obj_ref.tipo)
        if dialogo.exec():
            if dialogo.apagar_solicitado:
                self.apagar_objeto(item_atual)
            else:
                _, novas_coords_str, nova_cor, preenchido, tipo_escolhido = dialogo.obter_dados()

                # Aplica transformações acumuladas (se houver)
                transformacoes = dialogo.obter_transformacoes()
                if transformacoes:
                    novos_pontos = Transform.aplicar_lista_transformacoes(obj_ref.pontos, transformacoes)
                    obj_ref.pontos = novos_pontos
                    obj_ref.cor = nova_cor
                    if hasattr(obj_ref, 'preenchido'):
                        obj_ref.preenchido = preenchido
                    self.canvas.update()
                    return

                # Atualiza cor e preenchimento
                obj_ref.cor = nova_cor
                if hasattr(obj_ref, 'preenchido'):
                    obj_ref.preenchido = preenchido

                # Atualiza coordenadas se o usuário editou manualmente
                try:
                    coords_editadas = list(eval(f"[{novas_coords_str}]"))
                    for x, y in coords_editadas:
                        float(x)
                        float(y)

                    # Determina o novo tipo conforme a escolha do usuário
                    if tipo_escolhido == "Curva de Bézier":
                        if len(coords_editadas) < 4 or (len(coords_editadas) - 1) % 3 != 0:
                            QMessageBox.warning(self, "Erro",
                                f"Curva de Bézier precisa ter 3n+1 pontos (4, 7, 10, 13...).\n"
                                f"Você informou {len(coords_editadas)} pontos. Alterações de coordenadas ignoradas.")
                            self.canvas.update()
                            return
                        novo_tipo = "Curva2D"
                    elif tipo_escolhido == "B-Spline":
                        if len(coords_editadas) < 4:
                            QMessageBox.warning(self, "Erro",
                                f"B-Spline precisa de pelo menos 4 pontos de controle.\n"
                                f"Você informou {len(coords_editadas)} pontos. Alterações de coordenadas ignoradas.")
                            self.canvas.update()
                            return
                        novo_tipo = "BSpline2D"
                    else:
                        novo_tipo = "Ponto" if len(coords_editadas) == 1 else \
                                    "Reta" if len(coords_editadas) == 2 else "Wireframe"

                    if novo_tipo != obj_ref.tipo:
                        self.display_file.remover_objeto(obj_ref.nome)
                        if novo_tipo == "Ponto":
                            novo_obj = Ponto(obj_ref.nome, coords_editadas, nova_cor)
                        elif novo_tipo == "Reta":
                            novo_obj = Reta(obj_ref.nome, coords_editadas, nova_cor)
                        elif novo_tipo == "Curva2D":
                            novo_obj = Curva2D(obj_ref.nome, coords_editadas, nova_cor)
                        elif novo_tipo == "BSpline2D":
                            novo_obj = BSpline2D(obj_ref.nome, coords_editadas, nova_cor)
                        else:
                            novo_obj = Wireframe(obj_ref.nome, coords_editadas, nova_cor, preenchido=preenchido)
                        self.display_file.adicionar_objeto(novo_obj)
                        item_atual.setText(f"{obj_ref.nome} [{novo_tipo}]")
                    else:
                        obj_ref.pontos = coords_editadas
                except:
                    pass

                self.canvas.update()

    def apagar_objeto(self, item):
        nome_obj = item.data(Qt.ItemDataRole.UserRole)
        self.display_file.remover_objeto(nome_obj)
        linha = self.list_widget.row(item)
        self.list_widget.takeItem(linha)
        self.canvas.update()

    def abrir_menu_contexto(self, posicao):
        item = self.list_widget.itemAt(posicao)
        if item:
            menu = QMenu()
            menu.setStyleSheet(
                "QMenu { background-color: #D4D0C8; border: 1px solid black; } QMenu::item:selected { background-color: #000080; color: white; }")
            acao_editar = menu.addAction("Propriedades...")
            acao_apagar = menu.addAction("Apagar")

            acao = menu.exec(self.list_widget.mapToGlobal(posicao))
            if acao == acao_editar:
                self.editar_objeto_selecionado()
            elif acao == acao_apagar:
                self.apagar_objeto(item)

    # --- Lógica de Negócio ---

    def processar_adicao_objeto(self, nome, coords_str, cor, item_lista=None, preenchido=False, tipo="Automático"):
        if not nome or not coords_str:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos.")
            return

        try:
            coords = list(eval(f"[{coords_str}]"))

            for x, y in coords:
                float(x)
                float(y)

            if tipo == "Curva de Bézier":
                if len(coords) < 4:
                    QMessageBox.warning(self, "Erro",
                        "Curva de Bézier precisa de pelo menos 4 pontos de controle.")
                    return
                if (len(coords) - 1) % 3 != 0:
                    QMessageBox.warning(self, "Erro",
                        f"Curva de Bézier precisa ter 3n+1 pontos de controle (4, 7, 10, 13...).\n"
                        f"Você informou {len(coords)} pontos.")
                    return
                novo_obj = Curva2D(nome, coords, cor)
            elif tipo == "B-Spline":
                if len(coords) < 4:
                    QMessageBox.warning(self, "Erro",
                        "B-Spline precisa de pelo menos 4 pontos de controle.")
                    return
                novo_obj = BSpline2D(nome, coords, cor)
            else:
                # Automático: classifica pela quantidade
                if len(coords) == 1:
                    novo_obj = Ponto(nome, coords, cor)
                elif len(coords) == 2:
                    novo_obj = Reta(nome, coords, cor)
                elif len(coords) > 2:
                    novo_obj = Wireframe(nome, coords, cor, preenchido=preenchido)
                else:
                    raise ValueError("Coordenadas insuficientes")

            self.display_file.adicionar_objeto(novo_obj)
            texto_exibicao = f"{nome} [{novo_obj.tipo}]"

            if item_lista:
                item_lista.setText(texto_exibicao)
            else:
                self.list_widget.addItem(texto_exibicao)
                novo_item = self.list_widget.item(self.list_widget.count() - 1)
                novo_item.setData(Qt.ItemDataRole.UserRole, nome)

            self.canvas.update()

        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Formato de coordenadas inválido.\nUse: (x1, y1), (x2, y2), ...")

    # --- Navegação Unificada ---

    def _passo(self):
        try:
            return float(self.input_passo.text())
        except ValueError:
            return 10.0

    def _mover_x_pos(self):
        s = self._passo()
        self.window_obj.right(s); self.window3d.move_u(s); self.canvas.update()

    def _mover_x_neg(self):
        s = self._passo()
        self.window_obj.left(s); self.window3d.move_u(-s); self.canvas.update()

    def _mover_y_pos(self):
        s = self._passo()
        self.window_obj.up(s); self.window3d.move_v(s); self.canvas.update()

    def _mover_y_neg(self):
        s = self._passo()
        self.window_obj.down(s); self.window3d.move_v(-s); self.canvas.update()

    def _mover_z_pos(self):
        self.window3d.move_n(self._passo()); self.canvas.update()

    def _mover_z_neg(self):
        self.window3d.move_n(-self._passo()); self.canvas.update()

    def _rot_u(self, sinal):
        self.window3d.rotate_u(sinal * self._passo()); self.canvas.update()

    def _rot_v(self, sinal):
        self.window3d.rotate_v(sinal * self._passo()); self.canvas.update()

    def _rot_n(self, sinal):
        ang = sinal * self._passo()
        self.window3d.rotate_n(ang)
        self.window_obj.rotate(ang)
        self.canvas.update()

    def _zoom_in(self):
        self.window_obj.zoom_in(); self.window3d.zoom_in(); self.canvas.update()

    def _zoom_out(self):
        self.window_obj.zoom_out(); self.window3d.zoom_out(); self.canvas.update()

    # --- Importar/Exportar OBJ ---
    def importar_obj(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Importar arquivo .obj", "", "Wavefront OBJ (*.obj);;Todos (*)")
        if not filepath:
            return

        try:
            objetos = carregar_obj(filepath)
            for obj in objetos:
                # Evitar nomes duplicados
                nomes_existentes = [o.nome for o in self.display_file.obter_todos()]
                nome_original = obj.nome
                contador = 1
                while obj.nome in nomes_existentes:
                    obj.nome = f"{nome_original}_{contador}"
                    contador += 1

                self.display_file.adicionar_objeto(obj)
                if obj.tipo in ("Objeto3D", "SuperficieBSpline3D"):
                    item = QListWidgetItem(f"{obj.nome} [{obj.tipo}]")
                    item.setData(Qt.ItemDataRole.UserRole, obj.nome)
                    self.list_widget_3d.addItem(item)
                else:
                    texto = f"{obj.nome} [{obj.tipo}]"
                    self.list_widget.addItem(texto)
                    novo_item = self.list_widget.item(self.list_widget.count() - 1)
                    novo_item.setData(Qt.ItemDataRole.UserRole, obj.nome)

            self.canvas.update()
            QMessageBox.information(self, "Sucesso", f"{len(objetos)} objeto(s) importado(s).")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao importar .obj:\n{str(e)}")

    def exportar_obj(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exportar arquivo .obj", "mundo.obj", "Wavefront OBJ (*.obj);;Todos (*)")
        if not filepath:
            return

        try:
            salvar_obj(filepath, self.display_file)
            QMessageBox.information(self, "Sucesso", f"Mundo exportado para:\n{filepath}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao exportar .obj:\n{str(e)}")

    def _atualizar_algoritmo_clip(self):
        """Passa o algoritmo escolhido para o canvas e força redesenho."""
        if self.radio_cs.isChecked():
            self.canvas.algoritmo_clip_reta = "CS"
        else:
            self.canvas.algoritmo_clip_reta = "LB"
        self.canvas.update()

    # --- Ações Objetos 3D ---

    def _novo_objeto_3d(self):
        dialogo = JanelaObjeto3DDialog(self)
        if dialogo.exec():
            nome, segs_str, cor = dialogo.obter_dados()
            if not nome or not segs_str:
                QMessageBox.warning(self, "Erro", "Preencha nome e segmentos.")
                return
            try:
                segs = _parse_segmentos_3d(segs_str)
                obj = Objeto3D(nome, segs, cor)
                self.display_file.adicionar_objeto(obj)
                item = QListWidgetItem(f"{nome} [Objeto3D]")
                item.setData(Qt.ItemDataRole.UserRole, nome)
                self.list_widget_3d.addItem(item)
                self.canvas.update()
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Segmentos inválidos:\n{e}")

    def _nova_superficie_bspline(self):
        dialogo = JanelaSuperficieBSplineDialog(self)
        if dialogo.exec():
            try:
                nome, matriz_str, cor, passos = dialogo.obter_dados()
                if not nome or not matriz_str:
                    QMessageBox.warning(self, "Erro", "Preencha nome e matriz de controle.")
                    return
                matriz = _parse_matriz_pontos_3d(matriz_str)
                if passos <= 0:
                    raise ValueError("Passos deve ser maior que zero.")
                obj = SuperficieBSpline3D(nome, matriz, cor, passos)
                self.display_file.adicionar_objeto(obj)
                item = QListWidgetItem(f"{nome} [SuperficieBSpline3D]")
                item.setData(Qt.ItemDataRole.UserRole, nome)
                self.list_widget_3d.addItem(item)
                self.canvas.update()
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Matriz inválida:\n{e}")

    def _editar_objeto_3d(self):
        item = self.list_widget_3d.currentItem()
        if not item:
            QMessageBox.information(self, "Aviso", "Selecione um objeto 3D.")
            return
        nome = item.data(Qt.ItemDataRole.UserRole)
        sup = next((o for o in self.display_file.obter_todos()
                    if o.nome == nome and o.tipo == "SuperficieBSpline3D"), None)
        if sup:
            self._editar_superficie_bspline(item, sup)
            return

        obj = next((o for o in self.display_file.obter_todos()
                    if o.nome == nome and o.tipo == "Objeto3D"), None)
        if not obj:
            return
        segs_str = ", ".join(
            f"({p1.x},{p1.y},{p1.z})-({p2.x},{p2.y},{p2.z})"
            for p1, p2 in obj.segmentos)
        dialogo = JanelaObjeto3DDialog(self, nome=nome, segmentos_str=segs_str,
                                       cor_atual=obj.cor, modo_edicao=True)
        if dialogo.exec():
            if dialogo.apagar_solicitado:
                self.display_file.remover_objeto(nome)
                row = self.list_widget_3d.row(item)
                self.list_widget_3d.takeItem(row)
                self.canvas.update()
                return
            _, novas_segs_str, nova_cor = dialogo.obter_dados()
            transformacoes = dialogo.obter_transformacoes()
            if transformacoes:
                obj.segmentos = Transform3D3D.aplicar_lista_transformacoes(
                    obj.segmentos, transformacoes)
            elif novas_segs_str != segs_str:
                try:
                    obj.segmentos = _parse_segmentos_3d(novas_segs_str)
                except Exception as e:
                    QMessageBox.warning(self, "Erro", f"Segmentos inválidos:\n{e}")
            obj.cor = nova_cor
            self.canvas.update()

    def _editar_superficie_bspline(self, item, obj):
        matriz_str = _format_matriz_pontos_3d(obj.matriz_controle)
        dialogo = JanelaSuperficieBSplineDialog(
            self, nome=obj.nome, matriz_str=matriz_str, cor_atual=obj.cor,
            passos=getattr(obj, "passos", 10), modo_edicao=True)
        if dialogo.exec():
            if dialogo.apagar_solicitado:
                self.display_file.remover_objeto(obj.nome)
                row = self.list_widget_3d.row(item)
                self.list_widget_3d.takeItem(row)
                self.canvas.update()
                return
            try:
                _, nova_matriz_str, nova_cor, novos_passos = dialogo.obter_dados()
                transformacoes = dialogo.obter_transformacoes()
                if transformacoes:
                    obj.matriz_controle = Transform3D3D.aplicar_lista_transformacoes_matriz(
                        obj.matriz_controle, transformacoes)
                elif nova_matriz_str != matriz_str:
                    obj.matriz_controle = _parse_matriz_pontos_3d(nova_matriz_str)
                if novos_passos <= 0:
                    raise ValueError("Passos deve ser maior que zero.")
                obj.cor = nova_cor
                obj.passos = novos_passos
                self.canvas.update()
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Matriz inválida:\n{e}")

    def _menu_contexto_3d(self, posicao):
        item = self.list_widget_3d.itemAt(posicao)
        if item:
            menu = QMenu()
            menu.setStyleSheet(
                "QMenu { background-color: #D4D0C8; border: 1px solid black; } "
                "QMenu::item:selected { background-color: #000080; color: white; }")
            acao_editar = menu.addAction("Propriedades...")
            acao_apagar = menu.addAction("Apagar")
            acao = menu.exec(self.list_widget_3d.mapToGlobal(posicao))
            if acao == acao_editar:
                self._editar_objeto_3d()
            elif acao == acao_apagar:
                nome = item.data(Qt.ItemDataRole.UserRole)
                self.display_file.remover_objeto(nome)
                self.list_widget_3d.takeItem(self.list_widget_3d.row(item))
                self.canvas.update()


    # --- Perspectiva ---

    def _toggle_perspectiva(self, checked):
        self.canvas.modo_perspectiva = checked
        self.canvas.update()

    def _slider_focal_changed(self, valor):
        self.canvas.distancia_focal = float(valor)
        self._label_d_valor.setText(str(valor))
        self._atualizar_label_modo()
        self.canvas.update()

    def _atualizar_label_modo(self):
        d = self.canvas.distancia_focal
        if d < 300:
            modo = "Grande Angular"
        elif d <= 1000:
            modo = "Normal"
        else:
            modo = "Teleobjetiva"
        self._label_modo_persp.setText(f"Modo: {modo}  |  [ diminui  ] aumenta d")

    def _ajustar_focal(self, delta):
        novo_d = max(50, min(5000, int(self.canvas.distancia_focal) + delta))
        self.canvas.distancia_focal = float(novo_d)
        self._slider_focal.setValue(novo_d)
        self._label_d_valor.setText(str(novo_d))
        self._atualizar_label_modo()
        self.canvas.update()

    # --- Exibição 3D: Arame / Sólido / Phong (Trabalhos 2.1, 2.2 e 2.3) ---

    def _criar_grupo_shading(self):
        """Monta o grupo de controles de exibição 3D e iluminação de Phong."""
        grupo = QGroupBox("Exibição 3D (Rasterização)")
        layout = QVBoxLayout(grupo)

        # Modo de exibição dos objetos 3D (aplicado a todos de uma vez).
        self.radio_arame = QRadioButton("Arame (wireframe)")
        self.radio_solido = QRadioButton("Sólido (Z-buffer)")
        self.radio_phong = QRadioButton("Phong (iluminação)")
        self.radio_arame.setChecked(True)
        self.grupo_modo_3d = QButtonGroup(self)
        for r in (self.radio_arame, self.radio_solido, self.radio_phong):
            self.grupo_modo_3d.addButton(r)
            layout.addWidget(r)
        self.radio_arame.toggled.connect(lambda on: on and self._set_modo_render("arame"))
        self.radio_solido.toggled.connect(lambda on: on and self._set_modo_render("solido"))
        self.radio_phong.toggled.connect(lambda on: on and self._set_modo_render("phong"))

        self.check_zbuffer = QCheckBox("Usar Z-buffer")
        self.check_zbuffer.setChecked(True)
        self.check_zbuffer.toggled.connect(self._toggle_zbuffer)
        layout.addWidget(self.check_zbuffer)

        btn_esfera = QPushButton("Adicionar esfera de teste")
        btn_esfera.clicked.connect(self._adicionar_esfera_teste)
        layout.addWidget(btn_esfera)

        # Posição da luz (Lx, Ly, Lz) — valores iniciais iguais aos padrões do Canvas
        layout.addWidget(QLabel("Posição da luz (Lx, Ly, Lz):"))
        linha_luz = QHBoxLayout()
        self.input_lx = QLineEdit("200"); self.input_lx.setFixedWidth(55)
        self.input_ly = QLineEdit("200"); self.input_ly.setFixedWidth(55)
        self.input_lz = QLineEdit("-300"); self.input_lz.setFixedWidth(55)
        for inp in (self.input_lx, self.input_ly, self.input_lz):
            inp.editingFinished.connect(self._atualizar_luz)
            linha_luz.addWidget(inp)
        linha_luz.addStretch()
        layout.addLayout(linha_luz)

        # Coeficientes de material (Ka, Kd, Ks) e Shininess via sliders
        self._label_ka = QLabel()
        self._slider_ka = self._criar_slider_coef(0, 100, 10, self._atualizar_material)
        layout.addWidget(self._label_ka)
        layout.addWidget(self._slider_ka)

        self._label_kd = QLabel()
        self._slider_kd = self._criar_slider_coef(0, 100, 70, self._atualizar_material)
        layout.addWidget(self._label_kd)
        layout.addWidget(self._slider_kd)

        self._label_ks = QLabel()
        self._slider_ks = self._criar_slider_coef(0, 100, 50, self._atualizar_material)
        layout.addWidget(self._label_ks)
        layout.addWidget(self._slider_ks)

        self._label_shine = QLabel()
        self._slider_shine = self._criar_slider_coef(1, 128, 32, self._atualizar_material)
        layout.addWidget(self._label_shine)
        layout.addWidget(self._slider_shine)

        self._atualizar_labels_material()
        return grupo

    def _criar_slider_coef(self, minimo, maximo, valor, callback):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(minimo)
        slider.setMaximum(maximo)
        slider.setValue(valor)
        slider.valueChanged.connect(callback)
        return slider

    def _atualizar_labels_material(self):
        self._label_ka.setText(f"Ka: {self._slider_ka.value() / 100.0:.2f}")
        self._label_kd.setText(f"Kd: {self._slider_kd.value() / 100.0:.2f}")
        self._label_ks.setText(f"Ks: {self._slider_ks.value() / 100.0:.2f}")
        self._label_shine.setText(f"Shininess: {self._slider_shine.value()}")

    def _set_modo_render(self, modo):
        """Define o modo de exibição 3D (arame/solido/phong) para todos os objetos 3D."""
        self.canvas.modo_render_3d = modo
        self.canvas.update()

    def _toggle_zbuffer(self, checked):
        self.canvas.usar_zbuffer = checked
        self.canvas.update()

    def _atualizar_luz(self):
        try:
            lx = float(self.input_lx.text())
            ly = float(self.input_ly.text())
            lz = float(self.input_lz.text())
        except ValueError:
            return
        self.canvas.luz.posicao[:] = [lx, ly, lz]
        self.canvas.update()

    def _atualizar_material(self):
        ka = self._slider_ka.value() / 100.0
        kd = self._slider_kd.value() / 100.0
        ks = self._slider_ks.value() / 100.0
        shine = float(self._slider_shine.value())
        self.canvas.material.ka[:] = [ka, ka, ka]
        self.canvas.material.kd[:] = [kd, kd, kd]
        self.canvas.material.ks[:] = [ks, ks, ks]
        self.canvas.material.shininess = shine
        self._atualizar_labels_material()
        self.canvas.update()

    def _adicionar_esfera_teste(self):
        """Adiciona uma esfera de teste (Objeto3D com faces) para demonstrar Phong."""
        nome_base = "Esfera"
        nomes = [o.nome for o in self.display_file.obter_todos()]
        nome = nome_base
        contador = 1
        while nome in nomes:
            nome = f"{nome_base}_{contador}"
            contador += 1
        # Posiciona a esfera à esquerda, longe do cubo (origem) e da pirâmide (x=200).
        triangulos = get_powergirl_triangles(centro=(-200.0, 0.0, 0.0))
        segmentos = arestas_de_triangulos(triangulos)
        obj = Objeto3D(nome, segmentos, "#CCA0FF", triangulos=triangulos)
        self.display_file.adicionar_objeto(obj)
        item = QListWidgetItem(f"{nome} [Objeto3D]")
        item.setData(Qt.ItemDataRole.UserRole, nome)
        self.list_widget_3d.addItem(item)
        # Se ainda estiver em Arame, muda para Phong para visualizar o sombreamento.
        if self.canvas.modo_render_3d == "arame":
            self.radio_phong.setChecked(True)
        self.canvas.update()

    def keyPressEvent(self, event):
        key = event.key()
        atalhos = {
            Qt.Key.Key_W: self._mover_y_pos,
            Qt.Key.Key_S: self._mover_y_neg,
            Qt.Key.Key_A: self._mover_x_neg,
            Qt.Key.Key_D: self._mover_x_pos,
            Qt.Key.Key_Q: self._mover_z_neg,
            Qt.Key.Key_E: self._mover_z_pos,
            Qt.Key.Key_I: lambda: self._rot_u(1),
            Qt.Key.Key_K: lambda: self._rot_u(-1),
            Qt.Key.Key_J: lambda: self._rot_v(-1),
            Qt.Key.Key_L: lambda: self._rot_v(1),
            Qt.Key.Key_U: lambda: self._rot_n(1),
            Qt.Key.Key_O: lambda: self._rot_n(-1),
            Qt.Key.Key_BracketLeft:  lambda: self._ajustar_focal(-50),
            Qt.Key.Key_BracketRight: lambda: self._ajustar_focal(50),
        }
        fn = atalhos.get(key)
        if fn:
            fn()
        else:
            super().keyPressEvent(event)

    # --- Cena Inicial ---

    @staticmethod
    def _quads_para_triangulos(vertices, quads, centro=None):
        """Converte faces quadrangulares (índices) em triângulos com normal plana."""
        triangulos = []
        for a, b, c, d in quads:
            triangulos.append(triangulo_flat(vertices[a], vertices[b], vertices[c], centro))
            triangulos.append(triangulo_flat(vertices[a], vertices[c], vertices[d], centro))
        return triangulos

    def _carregar_cena_inicial(self):
        """Adiciona cubo e pirâmide (com faces) ao display file no startup."""
        # Cubo centrado na origem (size 100)
        cv = [
            (-50, -50, -50), (50, -50, -50), (50,  50, -50), (-50,  50, -50),
            (-50, -50,  50), (50, -50,  50), (50,  50,  50), (-50,  50,  50),
        ]
        ce = [(0,1),(1,2),(2,3),(3,0), (4,5),(5,6),(6,7),(7,4),
              (0,4),(1,5),(2,6),(3,7)]
        cube_segs = [(Ponto3D(*cv[i]), Ponto3D(*cv[j])) for i, j in ce]
        # Faces do cubo (quads) -> triângulos com normal plana orientada para fora.
        cube_quads = [(0,1,2,3), (4,5,6,7), (0,4,7,3),
                      (1,5,6,2), (3,7,6,2), (0,4,5,1)]
        cube_tris = self._quads_para_triangulos(cv, cube_quads, centro=(0,0,0))
        cubo = Objeto3D("Cubo", cube_segs, "#0000FF", triangulos=cube_tris)

        # Pirâmide quadrangular deslocada (centro em x=200)
        pv = [
            (200,  80,   0),
            (150, -50, -60), (250, -50, -60),
            (250, -50,  60), (150, -50,  60),
        ]
        pe = [(0,1),(0,2),(0,3),(0,4), (1,2),(2,3),(3,4),(4,1)]
        pyr_segs = [(Ponto3D(*pv[i]), Ponto3D(*pv[j])) for i, j in pe]
        centro_pyr = (200, -14, 0)  # centróide aproximado
        pyr_tris = [
            triangulo_flat(pv[0], pv[1], pv[2], centro_pyr),  # 4 lados
            triangulo_flat(pv[0], pv[2], pv[3], centro_pyr),
            triangulo_flat(pv[0], pv[3], pv[4], centro_pyr),
            triangulo_flat(pv[0], pv[4], pv[1], centro_pyr),
            triangulo_flat(pv[1], pv[2], pv[3], centro_pyr),  # base (2 triângulos)
            triangulo_flat(pv[1], pv[3], pv[4], centro_pyr),
        ]
        piramide = Objeto3D("Piramide", pyr_segs, "#FF0000", triangulos=pyr_tris)

        for obj in (cubo, piramide):
            self.display_file.adicionar_objeto(obj)
            item = QListWidgetItem(f"{obj.nome} [Objeto3D]")
            item.setData(Qt.ItemDataRole.UserRole, obj.nome)
            self.list_widget_3d.addItem(item)

        self.canvas.update()
