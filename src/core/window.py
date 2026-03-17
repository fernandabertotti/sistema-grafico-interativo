from src.utils.utils import W_X_MIN, W_Y_MIN, W_Y_MAX, W_X_MAX, STEP, PERCENTAGE

class Window():
    def __init__(self, xmin = W_X_MIN, ymin = W_Y_MIN, xmax = W_X_MAX, ymax = W_Y_MAX):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax 
        self.ymax = ymax

    # --- PANNING --- #
    def up(self, step = STEP):
        # Move a janela para cima
        self.ymin += step
        self.ymax += step

    def down(self, step = STEP):
        # Move a janela para baixo
        self.ymin -= step
        self.ymax -= step

    def right(self, step = STEP):
        # Move a janela para a direita
        self.xmin += step
        self.xmax += step

    def left(self, step = STEP):
        # Move a janela para a esquerda
        self.xmin -= step
        self.xmax -= step

    def zoom_in(self, percentage = PERCENTAGE):
        # Aproxima a visão (diminui o tamanho da window)
        factor = percentage / 100
        dx = (self.xmax - self.xmin) * factor / 2
        dy = (self.ymax - self.ymin) * factor / 2
        self.xmin += dx
        self.xmax -= dx
        self.ymin += dy
        self.ymax -= dy
        
    def zoom_out(self, percentage = PERCENTAGE): 
        # Afasta a visão (aumenta o tamanho da window)
        factor = percentage / 100
        dx = (self.xmax - self.xmin) * factor / 2
        dy = (self.ymax - self.ymin) * factor / 2
        self.xmin -= dx
        self.xmax += dx
        self.ymin -= dy
        self.ymax += dy
    


    
