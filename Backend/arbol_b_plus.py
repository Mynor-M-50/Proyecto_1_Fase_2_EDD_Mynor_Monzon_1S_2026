ORDEN_BP = 2
MAX_LLAVES_BP = 2 * ORDEN_BP      # 4 llaves máximo
MAX_HIJOS_BP = MAX_LLAVES_BP + 1  # 5 hijos máximo


class NodoArbolBPlus:
    def __init__(self, es_hoja=True):
        self.llaves = [None] * MAX_LLAVES_BP
        self.hijos = [None] * MAX_HIJOS_BP
        self.num_llaves = 0
        self.es_hoja = es_hoja
        self.siguiente = None  # ← Puntero a la siguiente hoja (exclusivo de B+)

    def esta_lleno(self):
        return self.num_llaves == MAX_LLAVES_BP


class ArbolBPlus:
    def __init__(self):
        self.raiz = None

    # ─── UTILIDADES ───────────────────────────────────────────

    def _to_lower(self, s: str) -> str:
        return s.lower()

    def _comparar(self, a: str, b: str) -> int:
        la, lb = self._to_lower(a), self._to_lower(b)
        if la < lb: return -1
        if la > lb: return  1
        return 0

    # ─── SPLIT ────────────────────────────────────────────────

    def _subir_llave(self, padre, i, producto, nuevo_hijo):
        for j in range(padre.num_llaves, i, -1):
            padre.hijos[j + 1] = padre.hijos[j]
        padre.hijos[i + 1] = nuevo_hijo

        for j in range(padre.num_llaves - 1, i - 1, -1):
            padre.llaves[j + 1] = padre.llaves[j]
        padre.llaves[i] = producto
        padre.num_llaves += 1

    def _split(self, padre, i, hijo_lleno):
        nuevo_nodo = NodoArbolBPlus(hijo_lleno.es_hoja)
        medio = ORDEN_BP  # = 2

        if hijo_lleno.es_hoja:
            # Split de hoja: la hoja derecha se queda con las llaves desde 'medio'
            nuevo_nodo.num_llaves = hijo_lleno.num_llaves - medio
            for j in range(nuevo_nodo.num_llaves):
                nuevo_nodo.llaves[j] = hijo_lleno.llaves[j + medio]
            hijo_lleno.num_llaves = medio

            # Mantener enlace de hojas (Lista enlazada de hojas)
            nuevo_nodo.siguiente = hijo_lleno.siguiente
            hijo_lleno.siguiente = nuevo_nodo

            # Subir COPIA de la primera llave del nuevo nodo al padre
            self._subir_llave(padre, i, nuevo_nodo.llaves[0], nuevo_nodo)
        else:
            # Split de nodo interno: igual que Árbol B normal
            nuevo_nodo.num_llaves = hijo_lleno.num_llaves - medio - 1
            for j in range(nuevo_nodo.num_llaves):
                nuevo_nodo.llaves[j] = hijo_lleno.llaves[j + medio + 1]
            for j in range(nuevo_nodo.num_llaves + 1):
                nuevo_nodo.hijos[j] = hijo_lleno.hijos[j + medio + 1]

            llave_subir = hijo_lleno.llaves[medio]
            hijo_lleno.num_llaves = medio
            self._subir_llave(padre, i, llave_subir, nuevo_nodo)

    # ─── INSERTAR ─────────────────────────────────────────────

    def _insertar_no_lleno(self, nodo, producto):
        i = nodo.num_llaves - 1

        if nodo.es_hoja:
            while i >= 0 and self._comparar(producto.categoria, nodo.llaves[i].categoria) < 0:
                nodo.llaves[i + 1] = nodo.llaves[i]
                i -= 1
            nodo.llaves[i + 1] = producto
            nodo.num_llaves += 1
        else:
            while i >= 0 and self._comparar(producto.categoria, nodo.llaves[i].categoria) < 0:
                i -= 1
            i += 1

            if nodo.hijos[i].esta_lleno():
                self._split(nodo, i, nodo.hijos[i])
                if self._comparar(producto.categoria, nodo.llaves[i].categoria) > 0:
                    i += 1

            self._insertar_no_lleno(nodo.hijos[i], producto)

    def insertar(self, producto):
        if self.raiz is None:
            self.raiz = NodoArbolBPlus(True)
            self.raiz.llaves[0] = producto
            self.raiz.num_llaves = 1
            return

        if self.raiz.esta_lleno():
            nueva_raiz = NodoArbolBPlus(False)
            nueva_raiz.hijos[0] = self.raiz
            self._split(nueva_raiz, 0, self.raiz)
            self.raiz = nueva_raiz

        self._insertar_no_lleno(self.raiz, producto)

    # ─── BUSCAR ───────────────────────────────────────────────

    def _buscar_indice(self, nodo, categoria: str) -> int:
        idx = 0
        while idx < nodo.num_llaves and self._comparar(nodo.llaves[idx].categoria, categoria) < 0:
            idx += 1
        return idx

    def buscar(self, categoria: str):
        """Retorna el primer producto encontrado con esa categoría."""
        if self.raiz is None:
            return None
        actual = self.raiz

        while not actual.es_hoja:
            i = 0
            while i < actual.num_llaves and self._comparar(categoria, actual.llaves[i].categoria) >= 0:
                i += 1
            actual = actual.hijos[i]

        for i in range(actual.num_llaves):
            if self._comparar(categoria, actual.llaves[i].categoria) == 0:
                return actual.llaves[i]
        return None

    def buscar_por_categoria(self, categoria: str):
        """Retorna lista de productos cuya categoría coincide (case-insensitive)."""
        resultados = []
        if self.raiz is None:
            return resultados

        # Buscar la hoja donde debería estar la categoría
        actual = self.raiz
        while not actual.es_hoja:
            i = 0
            while i < actual.num_llaves and self._comparar(categoria, actual.llaves[i].categoria) > 0:
                i += 1
            actual = actual.hijos[i]

        # Recorrer hojas en adelante y recolectar coincidencias
        encontrada = False
        while actual is not None:
            for i in range(actual.num_llaves):
                if self._comparar(actual.llaves[i].categoria, categoria) == 0:
                    resultados.append(actual.llaves[i])
                    encontrada = True
                elif encontrada and self._comparar(actual.llaves[i].categoria, categoria) > 0:
                    # ya pasó la categoría buscada → podemos terminar
                    return resultados
            actual = actual.siguiente

        return resultados

    # ─── ELIMINAR ─────────────────────────────────────────────

    def _prestar_hoja_anterior(self, padre, idx):
        hijo = padre.hijos[idx]
        hermano = padre.hijos[idx - 1]

        for i in range(hijo.num_llaves, 0, -1):
            hijo.llaves[i] = hijo.llaves[i - 1]

        hijo.llaves[0] = hermano.llaves[hermano.num_llaves - 1]
        hijo.num_llaves += 1
        hermano.num_llaves -= 1
        padre.llaves[idx - 1] = hijo.llaves[0]

    def _prestar_hoja_siguiente(self, padre, idx):
        hijo = padre.hijos[idx]
        hermano = padre.hijos[idx + 1]

        hijo.llaves[hijo.num_llaves] = hermano.llaves[0]
        hijo.num_llaves += 1

        for i in range(hermano.num_llaves - 1):
            hermano.llaves[i] = hermano.llaves[i + 1]
        hermano.num_llaves -= 1
        padre.llaves[idx] = hermano.llaves[0]

    def _fusionar_hojas(self, padre, idx):
        hijo = padre.hijos[idx]
        hermano = padre.hijos[idx + 1]

        for i in range(hermano.num_llaves):
            hijo.llaves[hijo.num_llaves + i] = hermano.llaves[i]
        hijo.num_llaves += hermano.num_llaves

        # Mantener enlace de hojas
        hijo.siguiente = hermano.siguiente

        for i in range(idx + 1, padre.num_llaves):
            padre.llaves[i - 1] = padre.llaves[i]
        for i in range(idx + 2, padre.num_llaves + 1):
            padre.hijos[i - 1] = padre.hijos[i]
        padre.num_llaves -= 1
        # hermano queda sin referencias, Python lo libera solo

    def _prestar_interno_anterior(self, padre, idx):
        hijo = padre.hijos[idx]
        hermano = padre.hijos[idx - 1]

        for i in range(hijo.num_llaves, 0, -1):
            hijo.llaves[i] = hijo.llaves[i - 1]
        for i in range(hijo.num_llaves + 1, 0, -1):
            hijo.hijos[i] = hijo.hijos[i - 1]

        hijo.llaves[0] = padre.llaves[idx - 1]
        hijo.hijos[0] = hermano.hijos[hermano.num_llaves]
        hijo.num_llaves += 1

        padre.llaves[idx - 1] = hermano.llaves[hermano.num_llaves - 1]
        hermano.num_llaves -= 1

    def _prestar_interno_siguiente(self, padre, idx):
        hijo = padre.hijos[idx]
        hermano = padre.hijos[idx + 1]

        hijo.llaves[hijo.num_llaves] = padre.llaves[idx]
        hijo.hijos[hijo.num_llaves + 1] = hermano.hijos[0]
        hijo.num_llaves += 1

        padre.llaves[idx] = hermano.llaves[0]

        for i in range(hermano.num_llaves - 1):
            hermano.llaves[i] = hermano.llaves[i + 1]
        for i in range(hermano.num_llaves):
            hermano.hijos[i] = hermano.hijos[i + 1]
        hermano.num_llaves -= 1

    def _fusionar_internos(self, padre, idx):
        hijo = padre.hijos[idx]
        hermano = padre.hijos[idx + 1]

        hijo.llaves[hijo.num_llaves] = padre.llaves[idx]
        hijo.num_llaves += 1

        for i in range(hermano.num_llaves):
            hijo.llaves[hijo.num_llaves + i] = hermano.llaves[i]
        for i in range(hermano.num_llaves + 1):
            hijo.hijos[hijo.num_llaves + i] = hermano.hijos[i]
        hijo.num_llaves += hermano.num_llaves

        for i in range(idx + 1, padre.num_llaves):
            padre.llaves[i - 1] = padre.llaves[i]
        for i in range(idx + 2, padre.num_llaves + 1):
            padre.hijos[i - 1] = padre.hijos[i]
        padre.num_llaves -= 1

    def _eliminar_recursivo(self, nodo, categoria: str, codigo: str) -> bool:
        if nodo.es_hoja:
            for i in range(nodo.num_llaves):
                if (self._comparar(nodo.llaves[i].categoria, categoria) == 0 and
                        nodo.llaves[i].codigo_barras == codigo):
                    for j in range(i + 1, nodo.num_llaves):
                        nodo.llaves[j - 1] = nodo.llaves[j]
                    nodo.num_llaves -= 1
                    return True
            return False

        # Nodo interno: buscar hijo correcto
        idx = 0
        while idx < nodo.num_llaves and self._comparar(categoria, nodo.llaves[idx].categoria) > 0:
            idx += 1

        hijo = nodo.hijos[idx]
        eliminado = self._eliminar_recursivo(hijo, categoria, codigo)

        # Si no encontró en hijo izquierdo y la categoría coincide, probar derecho
        if not eliminado and idx < nodo.num_llaves and self._comparar(categoria, nodo.llaves[idx].categoria) == 0:
            hijo = nodo.hijos[idx + 1]
            eliminado = self._eliminar_recursivo(hijo, categoria, codigo)
            idx = idx + 1

        if not eliminado:
            return False

        # Actualizar índice si la primera llave del hijo cambió
        if idx > 0 and hijo.num_llaves > 0:
            nodo.llaves[idx - 1] = hijo.llaves[0]

        # Verificar underflow
        if hijo.num_llaves < ORDEN_BP:
            if hijo.es_hoja:
                if idx > 0 and nodo.hijos[idx - 1].num_llaves > ORDEN_BP:
                    self._prestar_hoja_anterior(nodo, idx)
                elif idx < nodo.num_llaves and nodo.hijos[idx + 1].num_llaves > ORDEN_BP:
                    self._prestar_hoja_siguiente(nodo, idx)
                elif idx < nodo.num_llaves:
                    self._fusionar_hojas(nodo, idx)
                else:
                    self._fusionar_hojas(nodo, idx - 1)
            else:
                if idx > 0 and nodo.hijos[idx - 1].num_llaves > ORDEN_BP:
                    self._prestar_interno_anterior(nodo, idx)
                elif idx < nodo.num_llaves and nodo.hijos[idx + 1].num_llaves > ORDEN_BP:
                    self._prestar_interno_siguiente(nodo, idx)
                elif idx < nodo.num_llaves:
                    self._fusionar_internos(nodo, idx)
                else:
                    self._fusionar_internos(nodo, idx - 1)
        return True

    def eliminar(self, categoria: str, codigo: str) -> bool:
        if self.raiz is None:
            return False

        eliminado = self._eliminar_recursivo(self.raiz, categoria, codigo)

        if self.raiz.num_llaves == 0:
            if self.raiz.es_hoja:
                self.raiz = None
            else:
                self.raiz = self.raiz.hijos[0]
        return eliminado

    # ─── EXTRAS ───────────────────────────────────────────────

    def is_empty(self) -> bool:
        return self.raiz is None

    def get_raiz(self):
        return self.raiz

    def imprimir_lineal(self):
        """Recorre todas las hojas usando el puntero 'siguiente'."""
        if self.raiz is None:
            return

        actual = self.raiz
        while not actual.es_hoja:
            actual = actual.hijos[0]

        while actual is not None:
            for i in range(actual.num_llaves):
                print(f"{actual.llaves[i].nombre} | {actual.llaves[i].categoria} [B+ Leaf]")
            actual = actual.siguiente