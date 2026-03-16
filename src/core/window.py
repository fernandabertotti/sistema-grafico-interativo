# src/core/window.py
from utils import W_X_MIN, W_Y_MIN, W_Y_MAX, W_X_MAX, STEP, PERCENTAGE

class Window():
    def __init__(self, xmin = W_X_MIN, ymin = W_Y_MIN, xmax = W_X_MAX, ymax = W_Y_MAX):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax 
        self.ymax = ymax

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
        self.xmax -= step

    def left(self, step = STEP):
        # Move a janela para a esquerda
        self.xmin -= step
        self.xmax -= step

    # --- VERIFICAR! --- #
    def zoom_in(self, percentage = PERCENTAGE):
        # Diminui a janela em percentage%
        self.xmin *= 1 - percentage/100 
        self.ymin *= 1 - percentage/100 
        self.xmax *= 1 - percentage/100 
        self.ymax *= 1 - percentage/100    
        
    def zoom_out(self, percentage = PERCENTAGE): 
        # Aumenta a janela em percentage%
        self.xmin *= percentage/100 + 1
        self.ymin *= percentage/100 + 1
        self.xmax *= percentage/100 + 1
        self.ymax *= percentage/100 + 1
    


    
