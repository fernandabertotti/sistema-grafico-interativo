# src/ui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QListWidget, QLineEdit, QLabel, QMessageBox)
from src.ui.canvas import Canvas
from src.core.geometry import Ponto, Reta, Wireframe


class MainWindow(QMainWindow):
    def __init__(self, display_file, window_obj, viewport):
        super().__init__()
        self.display_file = display_file
        self.window_obj = window_obj
        self.viewport = viewport

        self.setWindowTitle("Sistema Gráfico Interativo - Trabalho 1.1")
        self.setGeometry(100, 100, 1000, 600)

        self.setup_ui()

    def setup_ui(self):
        # Widget e Layout Principal
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Esquerda: Canvas (Nossa Viewport)
        self.canvas = Canvas(self.display_file, self.window_obj, self.viewport)
        main_layout.addWidget(self.canvas, stretch=3)

        # Direita: Painel de Controle
        painel_layout = QVBoxLayout()
        main_layout.addLayout(painel_layout, stretch=1)

        # 1. Lista de Objetos
        painel_layout.addWidget(QLabel("Objetos:"))
        self.list_widget = QListWidget()
        painel_layout.addWidget(self.list_widget)

        # 2. Controles de Navegação e Zoom
        painel_layout.addWidget(QLabel("Navegação e Zoom:"))
        btn_up = QPushButton("Cima")
        btn_down = QPushButton("Baixo")
        btn_left = QPushButton("Esquerda")
        btn_right = QPushButton("Direita")
        btn_zoom_in = QPushButton("Zoom In")
        btn_zoom_out = QPushButton("Zoom Out")

        # Conectando os botões às funções matemáticas da Window
        btn_up.clicked.connect(self.mover_cima)
        btn_down.clicked.connect(self.mover_baixo)
        btn_left.clicked.connect(self.mover_esquerda)
        btn_right.clicked.connect(self.mover_direita)
        btn_zoom_in.clicked.connect(self.zoom_in)
        btn_zoom_out.clicked.connect(self.zoom_out)

        painel_layout.addWidget(btn_up)
        painel_layout.addWidget(btn_down)
        painel_layout.addWidget(btn_left)
        painel_layout.addWidget(btn_right)
        painel_layout.addWidget(btn_zoom_in)
        painel_layout.addWidget(btn_zoom_out)

        # 3. Adicionar Novo Objeto
        painel_layout.addWidget(QLabel("Adicionar Objeto:"))
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome")
        painel_layout.addWidget(self.input_nome)

        self.input_coords = QLineEdit()
        self.input_coords.setPlaceholderText("(x1, y1), (x2, y2)...")
        painel_layout.addWidget(self.input_coords)

        btn_add = QPushButton("Adicionar")
        btn_add.clicked.connect(self.adicionar_objeto)
        painel_layout.addWidget(btn_add)

    # --- Funções de Ação ---

    def adicionar_objeto(self):
        nome = self.input_nome.text()
        coords_str = self.input_coords.text()

        try:
            coords = list(eval(f"[{coords_str}]"))

            if len(coords) == 1:
                novo_obj = Ponto(nome, coords)
            elif len(coords) == 2:
                novo_obj = Reta(nome, coords)
            elif len(coords) > 2:
                novo_obj = Wireframe(nome, coords)
            else:
                raise ValueError("Coordenadas insuficientes")

            self.display_file.adicionar_objeto(novo_obj)
            self.list_widget.addItem(f"{nome} ({novo_obj.tipo})")

            # Limpa os campos
            self.input_nome.clear()
            self.input_coords.clear()

            # Manda o canvas se redesenhar com o novo objeto
            self.canvas.update()

        except Exception as e:
            QMessageBox.warning(self, "Erro",
                                f"Erro ao adicionar objeto. Formato inválido.\nUse: (x1, y1), (x2, y2)\nDetalhe: {e}")

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