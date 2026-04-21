# src/ui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QListWidget, QLineEdit, QLabel, QMessageBox,
                             QGridLayout, QGroupBox, QDialog, QTabWidget,
                             QMenu, QButtonGroup, QRadioButton, QComboBox, QFileDialog,
                             QCheckBox)
from PyQt6.QtCore import Qt
from src.ui.canvas import Canvas
from src.core.geometry import Ponto, Reta, Wireframe, Curva2D
from src.core.transform import Transform
from src.core.obj_io import salvar_obj, carregar_obj


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
        self.combo_tipo_objeto.addItems(["Automático", "Curva de Bézier"])
        if tipo_atual == "Curva2D":
            self.combo_tipo_objeto.setCurrentText("Curva de Bézier")
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
        if self.combo_tipo_objeto.currentText() == "Curva de Bézier":
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


# --- CLASSE DA JANELA PRINCIPAL ---

class MainWindow(QMainWindow):
    def __init__(self, display_file, window_obj, viewport):
        super().__init__()
        self.display_file = display_file
        self.window_obj = window_obj
        self.viewport = viewport
        self.transform = Transform()

        self.setWindowTitle("Sistema Grafico Interativo - V1.5")
        self.setGeometry(100, 100, 1050, 650)

        self.aplicar_tema()
        self.setup_ui()

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

        # ESQUERDA: Painel de Controle
        painel_layout = QVBoxLayout()
        main_layout.addLayout(painel_layout, stretch=1)

        # --- Grupo 1: Objetos ---
        grupo_objetos = QGroupBox("Objetos")
        layout_objetos = QVBoxLayout(grupo_objetos)

        self.list_widget = QListWidget()
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

        # Botões de importar/exportar OBJ
        botoes_obj_layout = QHBoxLayout()
        btn_importar = QPushButton("Importar .obj")
        btn_importar.clicked.connect(self.importar_obj)
        btn_exportar = QPushButton("Exportar .obj")
        btn_exportar.clicked.connect(self.exportar_obj)
        botoes_obj_layout.addWidget(btn_importar)
        botoes_obj_layout.addWidget(btn_exportar)
        layout_objetos.addLayout(botoes_obj_layout)

        painel_layout.addWidget(grupo_objetos)

        # --- Grupo 2: Navegação e Zoom ---
        grupo_nav = QGroupBox("Window View")
        layout_nav = QVBoxLayout(grupo_nav)

        nav_grid = QGridLayout()
        btn_up = QPushButton("Up")
        btn_down = QPushButton("Down")
        btn_left = QPushButton("Left")
        btn_right = QPushButton("Right")
        btn_zoom_in = QPushButton("Zoom In")
        btn_zoom_out = QPushButton("Zoom Out")

        btn_up.clicked.connect(self.mover_cima)
        btn_down.clicked.connect(self.mover_baixo)
        btn_left.clicked.connect(self.mover_esquerda)
        btn_right.clicked.connect(self.mover_direita)
        btn_zoom_in.clicked.connect(self.zoom_in)
        btn_zoom_out.clicked.connect(self.zoom_out)

        nav_grid.addWidget(btn_up, 0, 1)
        nav_grid.addWidget(btn_left, 1, 0)
        nav_grid.addWidget(btn_right, 1, 2)
        nav_grid.addWidget(btn_down, 2, 1)
        layout_nav.addLayout(nav_grid)

        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(btn_zoom_in)
        zoom_layout.addWidget(btn_zoom_out)
        layout_nav.addLayout(zoom_layout)

        # --- Rotação da Window ---
        rot_layout = QHBoxLayout()
        rot_layout.addWidget(QLabel("Rotação:"))
        self.input_rot_window = QLineEdit("10")
        self.input_rot_window.setFixedWidth(50)
        rot_layout.addWidget(self.input_rot_window)
        rot_layout.addWidget(QLabel("°"))

        btn_rot_esq = QPushButton("↷")
        btn_rot_esq.setFixedWidth(30)
        btn_rot_esq.clicked.connect(self.rotacionar_window_esquerda)
        btn_rot_dir = QPushButton("↶")
        btn_rot_dir.setFixedWidth(30)
        btn_rot_dir.clicked.connect(self.rotacionar_window_direita)
        rot_layout.addWidget(btn_rot_dir)
        rot_layout.addWidget(btn_rot_esq)
        rot_layout.addStretch()

        layout_nav.addLayout(rot_layout)

        # Label que mostra o ângulo atual
        self.label_angulo = QLabel("Ângulo atual: 0.0°")
        layout_nav.addWidget(self.label_angulo)

        painel_layout.addWidget(grupo_nav)
        painel_layout.addStretch()

           
        # --- Grupo 3: Clipping de Reta ---
        grupo_clip = QGroupBox("Clipping de Reta")
        clipping_layout = QVBoxLayout(grupo_clip)

        self.radio_cs = QRadioButton("Cohen-Sutherland")
        self.radio_lb = QRadioButton("Liang-Barsky")
        self.radio_cs.setChecked(True)

        # Conecta os radios ao canvas para ele saber qual algoritmo usar
        self.radio_cs.toggled.connect(self._atualizar_algoritmo_clip)
        self.radio_lb.toggled.connect(self._atualizar_algoritmo_clip)

        clipping_layout.addWidget(self.radio_cs)
        clipping_layout.addWidget(self.radio_lb)
        painel_layout.addWidget(grupo_clip)
        painel_layout.addStretch()


        # DIREITA: Canvas (Viewport)
        grupo_viewport = QGroupBox("Viewport")

        layout_canvas = QVBoxLayout(grupo_viewport)
        layout_canvas.setContentsMargins(10, 15, 10, 10)

        self.canvas = Canvas(self.display_file, self.window_obj, self.viewport)

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

    # --- Funções de Navegação ---
    def mover_cima(self):
        self.window_obj.up()
        self.canvas.update()

    def mover_baixo(self):
        self.window_obj.down()
        self.canvas.update()

    def mover_esquerda(self):
        self.window_obj.left()
        self.canvas.update()

    def mover_direita(self):
        self.window_obj.right()
        self.canvas.update()

    def zoom_in(self):
        self.window_obj.zoom_in()
        self.canvas.update()

    def zoom_out(self):
        self.window_obj.zoom_out()
        self.canvas.update()

    # --- Rotação da Window ---
    def rotacionar_window_esquerda(self):
        try:
            angulo = float(self.input_rot_window.text())
            self.window_obj.rotate(angulo)
            self.label_angulo.setText(f"Ângulo atual: {self.window_obj.angulo:.1f}°")
            self.canvas.update()
        except ValueError:
            QMessageBox.warning(self, "Erro", "Ângulo inválido.")

    def rotacionar_window_direita(self):
        try:
            angulo = float(self.input_rot_window.text())
            self.window_obj.rotate(-angulo)
            self.label_angulo.setText(f"Ângulo atual: {self.window_obj.angulo:.1f}°")
            self.canvas.update()
        except ValueError:
            QMessageBox.warning(self, "Erro", "Ângulo inválido.")

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