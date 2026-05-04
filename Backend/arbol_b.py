ORDEN_B = 2
MAX_LLAVES = 2 * ORDEN_B      # 4 llaves maximo
MAX_HIJOS = MAX_LLAVES + 1    # 5 hijos maximo


class NodoArbolB:
    def __init__(self, es_hoja=True):
        self.llaves = [None] * MAX_LLAVES
        self.hijos = [None] * MAX_HIJOS
        self.num_llaves = 0
        self.es_hoja = es_hoja

    def esta_lleno(self):
        return self.num_llaves == MAX_LLAVES


class ArbolB:
    def __init__(self):
        self.raiz = None

    # ─── Utilidades ───────────────────────────────────────────

    def _to_lower(self, s: str) -> str:
        return s.lower()

    def _comparar(self, a: str, b: str) -> int:
        la, lb = self._to_lower(a), self._to_lower(b)
        if la < lb: return -1
        if la > lb: return  1
        return 0

    # ─── Split ────────────────────────────────────────────────

    def _split(self, padre, i, hijo_lleno):
        nueva_pagina = NodoArbolB(hijo_lleno.es_hoja)
        medio = ORDEN_B  # = 2

        # Copiar llaves de la derecha al nuevo nodo
        for j in range(hijo_lleno.num_llaves - medio - 1):
            nueva_pagina.llaves[j] = hijo_lleno.llaves[j + medio + 1]

        nueva_pagina.num_llaves = hijo_lleno.num_llaves - medio - 1

        # Si no es hoja, copiar hijos tambie
        if not hijo_lleno.es_hoja:
            for j in range(nueva_pagina.num_llaves + 1):
                nueva_pagina.hijos[j] = hijo_lleno.hijos[j + medio + 1]

        # Reducir hijo izquierdo
        hijo_lleno.num_llaves = medio

        # Mover hijos del padr a la derecha
        for j in range(padre.num_llaves, i, -1):
            padre.hijos[j + 1] = padre.hijos[j]

        padre.hijos[i + 1] = nueva_pagina

        # Mover llaves del padre a la derecha
        for j in range(padre.num_llaves - 1, i - 1, -1):
            padre.llaves[j + 1] = padre.llaves[j]

        # Subir llave central al padre
        padre.llaves[i] = hijo_lleno.llaves[medio]
        padre.num_llaves += 1

    # ─── Insertar ─────────────────────────────────────────────

    def _insertar_no_lleno(self, nodo, producto):
        i = nodo.num_llaves - 1

        if nodo.es_hoja:
            while i >= 0 and self._comparar(producto.fecha_vencimiento, nodo.llaves[i].fecha_vencimiento) < 0:
                nodo.llaves[i + 1] = nodo.llaves[i]
                i -= 1
            nodo.llaves[i + 1] = producto
            nodo.num_llaves += 1
        else:
            while i >= 0 and self._comparar(producto.fecha_vencimiento, nodo.llaves[i].fecha_vencimiento) < 0:
                i -= 1
            i += 1

            if nodo.hijos[i].esta_lleno():
                self._split(nodo, i, nodo.hijos[i])
                if self._comparar(producto.fecha_vencimiento, nodo.llaves[i].fecha_vencimiento) > 0:
                    i += 1

            self._insertar_no_lleno(nodo.hijos[i], producto)

    def insertar(self, producto) -> bool:
        if self.raiz is None:
            self.raiz = NodoArbolB(True)
            self.raiz.llaves[0] = producto
            self.raiz.num_llaves = 1
            return True

        if self.raiz.esta_lleno():
            nueva_raiz = NodoArbolB(False)
            nueva_raiz.hijos[0] = self.raiz
            self._split(nueva_raiz, 0, self.raiz)
            self.raiz = nueva_raiz

        self._insertar_no_lleno(self.raiz, producto)
        return True

    # ─── Buscar ───────────────────────────────────────────────

    def _buscar(self, nodo, fecha: str):
        if nodo is None:
            return None

        i = 0
        while i < nodo.num_llaves and self._comparar(fecha, nodo.llaves[i].fecha_vencimiento) > 0:
            i += 1

        if i < nodo.num_llaves and self._comparar(fecha, nodo.llaves[i].fecha_vencimiento) == 0:
            return nodo.llaves[i]

        if nodo.es_hoja:
            return None

        return self._buscar(nodo.hijos[i], fecha)

    def buscar(self, fecha: str):
        return self._buscar(self.raiz, fecha)

    # ─── Elimibar ─────────────────────────────────────────────

    def _buscar_indice(self, nodo, fecha: str) -> int:
        idx = 0
        while idx < nodo.num_llaves and nodo.llaves[idx] is not None and self._comparar(
                nodo.llaves[idx].fecha_vencimiento, fecha) < 0:
            idx += 1
        return idx

    def _get_predecesor(self, nodo, idx):
        actual = nodo.hijos[idx]
        while not actual.es_hoja:
            actual = actual.hijos[actual.num_llaves]
        return actual.llaves[actual.num_llaves - 1]

    def _get_sucesor(self, nodo, idx):
        actual = nodo.hijos[idx + 1]
        while not actual.es_hoja:
            actual = actual.hijos[0]
        return actual.llaves[0]

    def _prestar_de_anterior(self, nodo, idx):
        hijo = nodo.hijos[idx]
        hermano = nodo.hijos[idx - 1]

        for i in range(hijo.num_llaves - 1, -1, -1):
            hijo.llaves[i + 1] = hijo.llaves[i]

        if not hijo.es_hoja:
            for i in range(hijo.num_llaves, -1, -1):
                hijo.hijos[i + 1] = hijo.hijos[i]

        hijo.llaves[0] = nodo.llaves[idx - 1]

        if not hijo.es_hoja:
            hijo.hijos[0] = hermano.hijos[hermano.num_llaves]

        nodo.llaves[idx - 1] = hermano.llaves[hermano.num_llaves - 1]
        hijo.num_llaves += 1
        hermano.num_llaves -= 1

    def _prestar_de_siguiente(self, nodo, idx):
        hijo = nodo.hijos[idx]
        hermano = nodo.hijos[idx + 1]

        hijo.llaves[hijo.num_llaves] = nodo.llaves[idx]

        if not hijo.es_hoja:
            hijo.hijos[hijo.num_llaves + 1] = hermano.hijos[0]

        nodo.llaves[idx] = hermano.llaves[0]

        for i in range(1, hermano.num_llaves):
            hermano.llaves[i - 1] = hermano.llaves[i]

        if not hermano.es_hoja:
            for i in range(1, hermano.num_llaves + 1):
                hermano.hijos[i - 1] = hermano.hijos[i]

        hijo.num_llaves += 1
        hermano.num_llaves -= 1

    def _fusionar(self, nodo, idx):
        hijo = nodo.hijos[idx]
        hermano = nodo.hijos[idx + 1]

        hijo.llaves[ORDEN_B] = nodo.llaves[idx]

        for i in range(hermano.num_llaves):
            hijo.llaves[i + ORDEN_B + 1] = hermano.llaves[i]

        if not hijo.es_hoja:
            for i in range(hermano.num_llaves + 1):
                hijo.hijos[i + ORDEN_B + 1] = hermano.hijos[i]

        for i in range(idx + 1, nodo.num_llaves):
            nodo.llaves[i - 1] = nodo.llaves[i]

        #Limpiar la ultima llave que quedp duplicada
        nodo.llaves[nodo.num_llaves - 1] = None

        for i in range(idx + 2, nodo.num_llaves + 1):
            nodo.hijos[i - 1] = nodo.hijos[i]

        hijo.num_llaves += hermano.num_llaves + 1
        nodo.num_llaves -= 1
        # hermano queda sin referencias

    def _eliminar_recursivo(self, nodo, fecha: str):
        idx = self._buscar_indice(nodo, fecha)

        # Caso A: La llave esta en este nodo
        if idx < nodo.num_llaves and nodo.llaves[idx] is not None and self._comparar(nodo.llaves[idx].fecha_vencimiento,
                                                                                    fecha) == 0:
            if nodo.es_hoja:
                # Caso A1: Es hoja
                for i in range(idx + 1, nodo.num_llaves):
                    nodo.llaves[i - 1] = nodo.llaves[i]
                nodo.llaves[nodo.num_llaves - 1] = None
                nodo.num_llaves -= 1
            else:
                # Caso A2: Nodo interno
                if nodo.hijos[idx].num_llaves >= ORDEN_B:
                    pred = self._get_predecesor(nodo, idx)
                    nodo.llaves[idx] = pred
                    self._eliminar_recursivo(nodo.hijos[idx], pred.fecha_vencimiento)
                elif nodo.hijos[idx + 1].num_llaves >= ORDEN_B:
                    suc = self._get_sucesor(nodo, idx)
                    nodo.llaves[idx] = suc
                    self._eliminar_recursivo(nodo.hijos[idx + 1], suc.fecha_vencimiento)
                else:
                    self._fusionar(nodo, idx)
                    self._eliminar_recursivo(nodo.hijos[idx], fecha)
        else:
            # Caso B: Buscar en el hijo
            if nodo.es_hoja:
                return  # No existe

            es_ultimo_hijo = (idx == nodo.num_llaves)

            if nodo.hijos[idx] is not None and nodo.hijos[idx].num_llaves < ORDEN_B:
                if idx != 0 and nodo.hijos[idx - 1] is not None and nodo.hijos[idx - 1].num_llaves >= ORDEN_B:
                    self._prestar_de_anterior(nodo, idx)
                elif idx != nodo.num_llaves and nodo.hijos[idx + 1] is not None and nodo.hijos[
                    idx + 1].num_llaves >= ORDEN_B:
                    self._prestar_de_siguiente(nodo, idx)
                else:
                    if idx != nodo.num_llaves:
                        self._fusionar(nodo, idx)
                    else:
                        self._fusionar(nodo, idx - 1)

            if es_ultimo_hijo and idx > nodo.num_llaves:
                self._eliminar_recursivo(nodo.hijos[idx - 1], fecha)
            else:
                if nodo.hijos[idx] is not None:
                    self._eliminar_recursivo(nodo.hijos[idx], fecha)
                else:
                    self._eliminar_recursivo(nodo.hijos[idx - 1], fecha)

    def eliminar(self, fecha: str) -> bool:
        if self.raiz is None:
            return False

        self._eliminar_recursivo(self.raiz, fecha)

        # Si la raiz quedo vacía despues de una fusin, el arbol baja un nivel
        if self.raiz.num_llaves == 0:
            if self.raiz.es_hoja:
                self.raiz = None
            else:
                self.raiz = self.raiz.hijos[0]
        return True

    # ─── Extras ───────────────────────────────────────────────

    def is_empty(self) -> bool:
        return self.raiz is None

    def get_raiz(self):
        return self.raiz

    def imprimir_inorden(self):
        self._inorden(self.raiz)

    def _inorden(self, nodo):
        if nodo is None:
            return
        for i in range(nodo.num_llaves):
            if not nodo.es_hoja:
                self._inorden(nodo.hijos[i])
            print(f"{nodo.llaves[i].nombre} | {nodo.llaves[i].fecha_vencimiento} [B-Tree]")
        if not nodo.es_hoja:
            self._inorden(nodo.hijos[nodo.num_llaves])

    def buscar_por_rango(self, desde: str, hasta: str):
        """Retorna lista de productos con fecha_vencimiento entre desde y hasta (inclusive)."""
        resultados = []
        if self.raiz is None:
            return resultados

        self._buscar_rango(self.raiz, desde, hasta, resultados)
        return resultados

    def _buscar_rango(self, nodo, desde: str, hasta: str, resultados: list):
        if nodo is None:
            return
        for i in range(nodo.num_llaves):
            if nodo.llaves[i] is None:
                continue
            if not nodo.es_hoja:
                self._buscar_rango(nodo.hijos[i], desde, hasta, resultados)
            f = nodo.llaves[i].fecha_vencimiento
            if self._comparar(f, desde) >= 0 and self._comparar(f, hasta) <= 0:
                resultados.append(nodo.llaves[i])
        if not nodo.es_hoja:
            self._buscar_rango(nodo.hijos[nodo.num_llaves], desde, hasta, resultados)