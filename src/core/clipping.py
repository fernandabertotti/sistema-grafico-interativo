from src.utils.utils import INSIDE, LEFT, RIGHT, BOTTOM, TOP

# Clipping de ponto
def clip_ponto(ponto_scn):
    """Retorna True se o ponto está dentro da window SCN [-1,1]x[-1,1]."""
    x, y = ponto_scn
    return -1 <= x <= 1 and -1 <= y <= 1


# Clipping de reta (Cohen-Sutherland)
def _compute_rc(x, y, xmin=-1, xmax=1, ymin=-1, ymax=1):
    rc = INSIDE
    if x < xmin: rc |= LEFT
    elif x > xmax: rc |= RIGHT
    if y < ymin: rc |= BOTTOM
    elif y > ymax: rc |= TOP
    return rc

def clip_reta_cohen_sutherland(p1, p2):
    """
    Retorna (p1_clip, p2_clip) se visível, ou None se completamente fora.
    """
    x1, y1 = p1
    x2, y2 = p2
    rc1, rc2 = _compute_rc(x1, y1), _compute_rc(x2, y2)

    while True:
        if not (rc1 | rc2):        # ambos dentro
            return (x1, y1), (x2, y2)
        if rc1 & rc2:              # ambos no mesmo lado fora
            return None
        # escolhe o ponto fora
        rc_out = rc1 if rc1 else rc2
        dx, dy = x2 - x1, y2 - y1
        if rc_out & TOP:
            x = x1 + dx * (1 - y1) / dy
            y = 1.0
        elif rc_out & BOTTOM:
            x = x1 + dx * (-1 - y1) / dy
            y = -1.0
        elif rc_out & RIGHT:
            y = y1 + dy * (1 - x1) / dx
            x = 1.0
        else:  # LEFT
            y = y1 + dy * (-1 - x1) / dx
            x = -1.0

        if rc_out == rc1:
            x1, y1 = x, y
            rc1 = _compute_rc(x1, y1)
        else:
            x2, y2 = x, y
            rc2 = _compute_rc(x2, y2)


# Clipping de reta (Liang-Barsky)
def clip_reta_liang_barsky(p1, p2):
    """
    Retorna (p1_clip, p2_clip) se visível, ou None se completamente fora.
    """
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1

    p = [-dx, dx, -dy, dy]
    q = [x1 - (-1), 1 - x1, y1 - (-1), 1 - y1]

    u1, u2 = 0.0, 1.0

    for pk, qk in zip(p, q):
        if pk == 0:
            if qk < 0:
                return None  # paralela e fora
        elif pk < 0:
            u1 = max(u1, qk / pk)
        else:
            u2 = min(u2, qk / pk)

    if u1 > u2:
        return None

    nx1 = x1 + u1 * dx
    ny1 = y1 + u1 * dy
    nx2 = x1 + u2 * dx
    ny2 = y1 + u2 * dy
    return (nx1, ny1), (nx2, ny2)


# Clipping de polígono (Sutherland-Hodgman)
def _intersect_edge(p1, p2, borda):
    """Calcula interseção de segmento p1-p2 com uma borda da window."""
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1

    if borda == 'left':
        t = (-1 - x1) / dx if dx != 0 else 0
    elif borda == 'right':
        t = (1 - x1) / dx if dx != 0 else 0
    elif borda == 'bottom':
        t = (-1 - y1) / dy if dy != 0 else 0
    else:  # top
        t = (1 - y1) / dy if dy != 0 else 0

    return (x1 + t * dx, y1 + t * dy)

def _inside(p, borda):
    x, y = p
    if borda == 'left':   return x >= -1
    if borda == 'right':  return x <= 1
    if borda == 'bottom': return y >= -1
    if borda == 'top':    return y <= 1

def clip_poligono_sutherland_hodgman(vertices):
    """
    Recebe lista de pontos SCN, retorna lista clipada (ou [] se totalmente fora).
    """
    output = list(vertices)
    for borda in ('left', 'right', 'bottom', 'top'):
        if not output:
            return []
        entrada = output
        output = []
        for i in range(len(entrada)):
            atual = entrada[i]
            anterior = entrada[i - 1]
            if _inside(atual, borda):
                if not _inside(anterior, borda):
                    output.append(_intersect_edge(anterior, atual, borda))
                output.append(atual)
            elif _inside(anterior, borda):
                output.append(_intersect_edge(anterior, atual, borda))
    return output