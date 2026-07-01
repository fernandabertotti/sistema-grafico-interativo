# Sistema Gráfico Interativo (SGI)

Sistema gráfico interativo em **Python + PyQt6** com pipeline 2D e 3D próprio:
window/viewport, clipping, curvas, superfícies, projeções paralela e perspectiva,
e um **rasterizador próprio** (framebuffer) com Z-buffer e iluminação de Phong.

---

## Requisitos e instalação

- Python 3.10+
- Dependências em `requirements.txt` (`numpy`, `PyQt6`)

```bash
pip install -r requirements.txt
```

## Como executar

```bash
python main.py
```

Ao abrir, já vem uma **cena de exemplo**: objetos 2D (ponto, reta, quadrado
preenchido, triângulo, curva de Bézier, B-spline) e objetos 3D (cubo, pirâmide,
esfera e uma superfície B-spline).

---

## Interface

O painel da esquerda concentra os controles; a **Viewport** (direita) mostra a
cena, com a moldura vermelha indicando a área de recorte (clipping).

### Cena Ativa (2D x 3D)
No topo há o seletor **Cena Ativa**. Objetos 2D e 3D **nunca aparecem juntos**:
- **2D** — mostra ponto, reta, wireframe (polígonos), curvas de Bézier e B-splines.
- **3D** — mostra objetos 3D e superfícies B-spline.

### Objetos 2D / Objetos 3D
Cada tipo tem sua própria lista. Use **Novo...** / **Novo 3D...** para criar,
duplo-clique (ou **Editar...**) para alterar, e o menu de contexto (botão direito)
para propriedades/apagar. É possível aplicar **transformações** (translação,
escala e rotação) na aba de transformações do diálogo de edição.

- Objetos 2D são classificados automaticamente pela quantidade de coordenadas
  (1 = ponto, 2 = reta, 3+ = wireframe), ou você escolhe **Curva de Bézier** /
  **B-Spline**. Wireframes com 3+ vértices podem ser **preenchidos**.
- **Nova Sup. B-Spline...** cria uma superfície a partir de uma matriz de controle.

### Arquivo (.obj)
**Importar .obj** / **Exportar .obj** — formato Wavefront. Faces 3D (`f`) viram
objetos sólidos sombreáveis; objetos 2D e 3D de arame também são suportados.

### Navegação
Move/rotaciona a **câmera** (translação, rotação nos eixos X/Y/Z e zoom).
Também pelo teclado: `W A S D` (transladar), `Q E` (afastar/aproximar em Z),
`I K J L U O` (rotações), `[ ]` (distância focal `d`).

### Clipping de Reta
Alterna entre **Cohen-Sutherland** e **Liang-Barsky** para o recorte de retas.

### Projeção 3D
- **Modo Perspectiva** (com controle da distância focal `d`) ou projeção paralela.
- **Z ↑ Aprox. / Z ↓ Afastar** — aproxima/afasta a câmera no eixo de visão
  (só tem efeito visível com a perspectiva ligada).

### Exibição 3D (Rasterização) — Trabalhos 2.1, 2.2 e 2.3
Modo de exibição aplicado a **todos** os objetos 3D de uma vez:
- **Arame (wireframe)** — desenho vetorial de arestas.
- **Sólido (Z-buffer)** — faces preenchidas com cor plana e remoção de
  superfícies ocultas por **Z-buffer**.
- **Phong (iluminação)** — sombreamento de Phong por pixel.

Com **Phong** selecionado, aparecem os controles de:
- **Posição da luz** (sliders X/Y/Z) — arraste para ver o brilho se mover.
- **Material do objeto**: Ambiente (Ka), Difuso (Kd), Especular (Ks) e
  Brilho (Shininess).

A caixa **Usar Z-buffer (oclusão)** liga/desliga a checagem de profundidade —
desligada, superfícies de trás podem sobrescrever as da frente.

---

## Os três trabalhos de rasterização

- **2.1 — Rasterização (framebuffer):** `src/core/framebuffer.py` implementa
  `draw_pixel`, `draw_line` (Bresenham), `draw_trapezoid` e `draw_polygon`
  (decomposição em trapézios). O preenchimento de polígonos 2D do SGI usa o
  `draw_polygon`.
- **2.2 — Z-buffer:** `draw_triangle_3d` rasteriza triângulos com interpolação
  de profundidade e checagem por Z-buffer; `clear` reseta cor e profundidade.
- **2.3 — Iluminação de Phong:** `src/core/phong.py` (modelo de Phong) e
  `draw_triangle_phong`, que calcula a cor por pixel interpolando posição e
  normal (iluminação de dois lados para superfícies abertas).

---

## Estrutura do projeto

```
main.py                     # ponto de entrada
requirements.txt
assets/                     # arquivos .obj de exemplo
src/
  core/
    geometry.py             # tipos de objeto (2D e 3D)
    display_file.py         # lista de objetos da cena
    window.py / window3d.py # câmeras 2D e 3D (SCN, projeções)
    viewport.py             # transformação SCN -> pixels
    clipping.py             # Cohen-Sutherland, Liang-Barsky, Sutherland-Hodgman
    transform.py / transform3d.py   # transformações 2D e 3D
    bezier*.py / bspline*.py        # curvas e superfícies
    framebuffer.py          # rasterizador próprio (2.1 e 2.2)
    phong.py                # iluminação de Phong (2.3)
    obj_io.py               # importar/exportar .obj
  ui/
    main_window.py          # janela e controles (PyQt6)
    canvas.py               # renderização da viewport
  utils/utils.py            # constantes
```
