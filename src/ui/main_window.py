# src/ui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QListWidget, QLineEdit, QLabel, QMessageBox,
                             QGridLayout, QGroupBox, QDialog, QTabWidget,
                             QMenu, QButtonGroup)
from PyQt6.QtCore import Qt
from src.ui.canvas import Canvas
from src.core.geometry import Ponto, Reta, Wireframe

# --- CLASSE DO DIÁLOGO (POP-UP) ---

class JanelaObjetoDialog(QDialog):
    """Janela modal para adicionar ou editar objetos"""
    def __init__(self, parent=None, nome="", coords="", cor_atual="#000000", modo_edicao=False):
        super().__init__(parent)
        self.setWindowTitle("Propriedades do Objeto" if modo_edicao else "Novo Objeto")
        self.setFixedSize(350, 300)
        self.modo_edicao = modo_edicao
        self.apagar_solicitado = False

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

        layout_geometria.addWidget(QLabel("Coordenadas [(x1, y1), (x2, y2)...]:"))
        self.input_coords = QLineEdit(coords)
        layout_geometria.addWidget(self.input_coords)

        # --- Seletor de Cores ---
        layout_geometria.addWidget(QLabel("Cor do Traço:"))
        layout_cores = QHBoxLayout()
        self.grupo_cores = QButtonGroup(self)
        
        # Lista de cores hexadecimais (Preto, Vermelho, Verde, Azul, Amarelo, Magenta, Ciano, Laranja)
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
        layout_geometria.addStretch()

        self.abas.addTab(self.aba_geometria, "Geometria")

        # Aba 2: Transformações
        self.aba_transformacoes = QWidget()
        layout_transf = QVBoxLayout(self.aba_transformacoes)
        layout_transf.addWidget(QLabel("Ferramentas de Transformação 2D\n(Translação, Escala, Rotação)\n\nEm desenvolvimento..."))
        self.abas.addTab(self.aba_transformacoes, "Transformações 2D")
        
        if not modo_edicao:
            self.abas.setTabEnabled(1, False)

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

    def acao_apagar(self):
        self.apagar_solicitado = True
        self.accept()

    def obter_dados(self):
        id_cor = self.grupo_cores.checkedId()
        cor_selecionada = self.lista_cores[id_cor] if id_cor != -1 else "#000000"
        return self.input_nome.text(), self.input_coords.text(), cor_selecionada


# --- CLASSE DA JANELA PRINCIPAL ---

class MainWindow(QMainWindow):
    def __init__(self, display_file, window_obj, viewport):
        super().__init__()
        self.display_file = display_file
        self.window_obj = window_obj
        self.viewport = viewport

        self.setWindowTitle("Sistema Grafico Interativo - V1.1")
        self.setGeometry(100, 100, 1000, 600)

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
            /* Aqui agrupamos os campos de texto, a lista e o nosso canvas */
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

        painel_layout.addWidget(grupo_nav)
        painel_layout.addStretch()

        # DIREITA: Canvas (Viewport)
        grupo_viewport = QGroupBox("Viewport")
        
        layout_canvas = QVBoxLayout(grupo_viewport)
        # Adiciona uma margem para que o canvas não fique colado na linha do GroupBox
        layout_canvas.setContentsMargins(10, 15, 10, 10) 
        
        self.canvas = Canvas(self.display_file, self.window_obj, self.viewport)

        # Identifica o canvas para o CSS aplicar o fundo branco e a borda rebaixada
        self.canvas.setObjectName("AreaCanvas") 
        self.canvas.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True) # Força o PyQt a pintar o fundo do QSS
        self.canvas.setStyleSheet("") # Limpa qualquer estilo conflitante que estava no canvas.py
        
        layout_canvas.addWidget(self.canvas)
        
        main_layout.addWidget(grupo_viewport, stretch=4)

    # --- Funções de Ação de Interface ---

    def abrir_dialogo_novo_objeto(self):
        dialogo = JanelaObjetoDialog(self)
        if dialogo.exec():
            nome, coords_str, cor = dialogo.obter_dados()
            self.processar_adicao_objeto(nome, coords_str, cor)

    def editar_objeto_selecionado(self):
        item_atual = self.list_widget.currentItem()
        if not item_atual:
            QMessageBox.information(self, "Aviso", "Selecione um objeto na lista primeiro.")
            return

        nome_obj = item_atual.data(Qt.ItemDataRole.UserRole)
        obj_ref = next((obj for obj in self.display_file.obter_todos() if obj.nome == nome_obj), None)
        if not obj_ref: return

        coords_str = ", ".join([str(pt) for pt in obj_ref.pontos])
        
        dialogo = JanelaObjetoDialog(self, nome=obj_ref.nome, coords=coords_str, cor_atual=obj_ref.cor, modo_edicao=True)
        if dialogo.exec():
            if dialogo.apagar_solicitado:
                self.apagar_objeto(item_atual)
            else:
                _, novas_coords_str, nova_cor = dialogo.obter_dados()
                self.display_file.remover_objeto(obj_ref.nome)
                self.processar_adicao_objeto(obj_ref.nome, novas_coords_str, nova_cor, item_lista=item_atual)

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
            menu.setStyleSheet("QMenu { background-color: #D4D0C8; border: 1px solid black; } QMenu::item:selected { background-color: #000080; color: white; }")
            acao_editar = menu.addAction("Propriedades...")
            acao_apagar = menu.addAction("Apagar")
            
            acao = menu.exec(self.list_widget.mapToGlobal(posicao))
            if acao == acao_editar:
                self.editar_objeto_selecionado()
            elif acao == acao_apagar:
                self.apagar_objeto(item)

    # --- Lógica de Negócio ---

    def processar_adicao_objeto(self, nome, coords_str, cor, item_lista=None):
        if not nome or not coords_str:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos.")
            return

        try:
            coords = list(eval(f"[{coords_str}]"))

            for x, y in coords:
                float(x)
                float(y)

            if len(coords) == 1:
                novo_obj = Ponto(nome, coords, cor)
            elif len(coords) == 2:
                novo_obj = Reta(nome, coords, cor)
            elif len(coords) > 2:
                novo_obj = Wireframe(nome, coords, cor)
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