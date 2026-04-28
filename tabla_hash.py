from estructuras_lineales import ListaEnlazada

class TablaHash:
    TAMANIO = 101  # Número primo para mejor distribución

    def __init__(self):
        # Creamos 101 listas enlazadas (una por cubeta)
        self.tabla = [ListaEnlazada() for _ in range(self.TAMANIO)]

    def _funcion_hash(self, llave: str) -> int:
        # Algoritmo djb2 - igual que tu C++
        hash_val = 5381
        for c in llave:
            hash_val = ((hash_val << 5) + hash_val) + ord(c)
            hash_val &= 0xFFFFFFFFFFFFFFFF  # Evita overflow en Python
        return hash_val % self.TAMANIO

    def insertar(self, producto):
        indice = self._funcion_hash(producto.codigo_barras)
        self.tabla[indice].insertar_al_final(producto)

    def buscar(self, codigo: str):
        indice = self._funcion_hash(codigo)
        actual = self.tabla[indice].head
        while actual:
            if actual.valor.codigo_barras == codigo:
                return actual.valor
            actual = actual.siguiente
        return None  # En C++ retornabas nullptr, aquí retornamos None

    def eliminar(self, codigo: str):
        indice = self._funcion_hash(codigo)
        self.tabla[indice].eliminar_por_codigo(codigo)

    def imprimir_estado(self):
        print("--- Estado de la Tabla Hash ---")
        for i in range(self.TAMANIO):
            if self.tabla[i].head is not None:
                print(f"Indice [{i}]: ", end="")
                actual = self.tabla[i].head
                while actual:
                    print(actual.valor.nombre, end=" -> ")
                    actual = actual.siguiente
                print("None")

    def get_cubetas_ocupadas(self) -> int:
        count = 0
        for i in range(self.TAMANIO):
            if self.tabla[i].head is not None:
                count += 1
        return count

    def get_cubeta(self, i: int):
        return self.tabla[i]

    def get_tamanio(self) -> int:
        return self.TAMANIO