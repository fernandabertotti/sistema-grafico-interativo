from src.core.geometry import ObjetoGrafico

class DisplayFile:
    def __init__(self):
        self.objetos = []

    def adicionar_objeto(self, objeto: ObjetoGrafico):
        self.objetos.append(objeto)

    def remover_objeto(self, nome: str):
        for obj in self.objetos:
            if obj.nome == nome:
                self.objetos.remove(obj)

    def obter_todos(self):
        return self.objetos