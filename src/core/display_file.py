# src/core/display_file.py

class DisplayFile:
    def __init__(self):
        self.objetos = []

    def adicionar_objeto(self, objeto):
        self.objetos.append(objeto)

    def obter_todos(self):
        return self.objetos