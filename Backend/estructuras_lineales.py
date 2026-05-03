class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None

    def get_valor(self):
        return self.valor

    def get_siguiente(self):
        return self.siguiente

class ListaEnlazada:
    def __init__(self):
        self.head = None
        self.size = 0

    def get_size(self):
        return self.size

    def get_head(self):
        return self.head

    def insertar_al_final(self, valor):
        nuevo = Nodo(valor)
        if not self.head:
            self.head = nuevo
        else:
            actual = self.head
            while actual.siguiente:
                actual = actual.siguiente
            actual.siguiente = nuevo
        self.size += 1

    def eliminar_por_codigo(self, codigo):
        actual = self.head
        anterior = None
        while actual:
            # Asumimos que el valor es un objeto Producto
            if hasattr(actual.valor, 'codigo_barras') and actual.valor.codigo_barras == codigo:
                if anterior:
                    anterior.siguiente = actual.siguiente
                else:
                    self.head = actual.siguiente
                self.size -= 1
                return True
            anterior = actual
            actual = actual.siguiente
        return False

    def insertar_ordenado_por_nombre(self, valor):
        nuevo = Nodo(valor)

        if not self.head or valor.nombre < self.head.valor.nombre:
            nuevo.siguiente = self.head
            self.head = nuevo
        else:
            actual = self.head
            while (actual.siguiente and
                actual.siguiente.valor.nombre < valor.nombre):
                actual = actual.siguiente

            nuevo.siguiente = actual.siguiente
            actual.siguiente = nuevo

        self.size += 1

class Pila:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.esta_vacia():
            return self.items.pop()
        return None

    def esta_vacia(self):
        return len(self.items) == 0

class Cola:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if not self.esta_vacia():
            return self.items.pop(0) # El primero en entrar es el primero en salir
        return None

    def esta_vacia(self):
        return len(self.items) == 0