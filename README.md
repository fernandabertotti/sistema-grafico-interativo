# Sistema Gráfico Interativo (SGI)

Pipeline gráfico 2D e 3D implementado do zero em Python + PyQt6: window/viewport,
clipping, transformações, curvas (Bézier e B-Spline), superfícies bicúbicas e
projeções paralela e perspectiva.

## Execução

```bash
pip install -r requirements.txt
python main.py
```

Requer Python 3.10+; as únicas dependências são `numpy` e `PyQt6`.

Ao iniciar, o programa carrega uma cena de exemplo com um objeto de cada tipo.
A viewport começa na cena 2D; alternando para 3D, a câmera já aparece em ângulo,
permitindo visualizar os recursos de imediato.

## Utilização

O painel da esquerda concentra os controles e a viewport (à direita) exibe a
cena. A moldura vermelha indica a área de recorte (clipping).

**Cena ativa (2D / 3D).** O seletor no topo do painel alterna qual cena é
exibida na viewport: *2D* mostra apenas os objetos 2D e *3D* apenas os objetos
tridimensionais.

**Criar e editar objetos.** Objetos 2D e 3D ficam em listas separadas, mas
compartilham a mesma viewport. Use *Novo...* / *Novo 3D...* para criar,
duplo-clique para editar e o botão direito para o menu de contexto. No diálogo
de edição é possível acumular transformações (translação, escala e rotação) e
aplicá-las de uma só vez.

- **2D:** o tipo é definido pela quantidade de coordenadas (1 = ponto,
  2 = reta, 3+ = wireframe), ou selecionado manualmente como *Bézier* /
  *B-Spline*. Wireframes com 3+ vértices podem ser preenchidos. Bézier requer
  `3n+1` pontos de controle (4, 7, 10...); B-Spline requer 4 ou mais.
- **3D:** modelos de arame definidos por segmentos `(x1,y1,z1)-(x2,y2,z2)`.
- **Superfície B-Spline:** matriz de controle de 4×4 até 20×20, gerada por
  Forward Differences.

**Importar / Exportar .obj.** Formato Wavefront, com extensões próprias
(`usercor`, `usertype`, `userfill`, `usersteps`, `bsplinesurf`) que preservam
cor, tipo, preenchimento e superfícies na ida e na volta. Compatível com objetos
2D, 3D de arame e superfícies.

**Navegação.** A câmera pode ser controlada pelos botões ou pelo teclado:

| Tecla | Ação |
|-------|------|
| `W A S D` | transladar |
| `Q E` | afastar / aproximar em Z |
| `I K J L U O` | rotações |
| `[ ]` | ajustar a distância focal `d` |

**Clipping de reta.** Alterna entre os algoritmos de Cohen-Sutherland e
Liang-Barsky.

**Projeção 3D.** Perspectiva (com controle da distância focal `d`) ou paralela
ortogonal. *Z ↑ / Z ↓* aproxima e afasta a câmera — efeito mais perceptível com
a perspectiva ativada.

## Estrutura

```
main.py                     ponto de entrada
assets/                     .obj de exemplo (cubo, paralelepípedo)
src/
  core/
    geometry.py             tipos de objeto (2D e 3D)
    display_file.py         lista de objetos da cena
    window.py / window3d.py câmeras 2D e 3D (SCN, projeções)
    viewport.py             SCN -> pixels
    clipping.py             Cohen-Sutherland, Liang-Barsky, Sutherland-Hodgman
    transform.py / transform3d.py   transformações em coordenadas homogêneas
    bezier.py               Bézier cúbica por partes
    bspline.py              B-Spline cúbica uniforme (Forward Differences)
    bspline_surface.py      superfícies B-Spline bicúbicas
    obj_io.py               importar/exportar .obj
  ui/
    main_window.py          janela e controles (PyQt6)
    canvas.py               renderização da viewport
  utils/utils.py            constantes
```

## Recursos implementados

- Window/viewport com coordenadas normalizadas (SCN em `[-1,1]`) e rotação de window.
- Transformações 2D e 3D em coordenadas homogêneas: translação, escala e rotação
  (em torno do centro do mundo, do centro do objeto ou de ponto/eixo arbitrário).
- Clipping de ponto, reta (Cohen-Sutherland e Liang-Barsky) e polígono
  (Sutherland-Hodgman).
- Curvas de Bézier cúbica por partes (forma matricial) e B-Spline cúbica uniforme
  (Forward Differences).
- Câmera 3D com VRP/VPN/VUP, projeção paralela ortogonal e perspectiva, e
  superfícies B-Spline bicúbicas.
</content>
