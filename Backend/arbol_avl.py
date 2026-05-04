class NodoAVL:
    def __init__(self, producto):
        self.valor = producto
        self.izq = None
        self.der = None
        self.fe = 0  # Factor de equilibrio


class ArbolAVL:
    def __init__(self):
        self.raiz = None

    # ─── Utilidades ───────────────────────────────────────────

    def _to_lower(self, s: str) -> str:
        return s.lower()

    def _altura(self, nodo) -> int:
        if nodo is None:
            return 0
        return 1 + max(self._altura(nodo.izq), self._altura(nodo.der))

    def _actualizar_fe(self, nodo):
        if nodo is None:
            return
        nodo.fe = self._altura(nodo.der) - self._altura(nodo.izq)

    # ─── Rotaciones ───────────────────────────────────────────

    def _rotacion_II(self, nodo):
        nodo1 = nodo.izq
        nodo.izq = nodo1.der
        nodo1.der = nodo
        self._actualizar_fe(nodo)
        self._actualizar_fe(nodo1)
        return nodo1

    def _rotacion_DD(self, nodo):
        nodo1 = nodo.der
        nodo.der = nodo1.izq
        nodo1.izq = nodo
        self._actualizar_fe(nodo)
        self._actualizar_fe(nodo1)
        return nodo1

    def _rotacion_ID(self, nodo):
        nodo1 = nodo.izq
        nodo2 = nodo1.der

        nodo1.der = nodo2.izq
        nodo2.izq = nodo1
        nodo.izq = nodo2.der
        nodo2.der = nodo

        self._actualizar_fe(nodo)
        self._actualizar_fe(nodo1)
        self._actualizar_fe(nodo2)
        return nodo2

    def _rotacion_DI(self, nodo):
        nodo1 = nodo.der
        nodo2 = nodo1.izq

        nodo1.izq = nodo2.der
        nodo2.der = nodo1
        nodo.der = nodo2.izq
        nodo2.izq = nodo

        self._actualizar_fe(nodo)
        self._actualizar_fe(nodo1)
        self._actualizar_fe(nodo2)
        return nodo2

    # ─── Balancear ────────────────────────────────────────────

    def _balancear(self, nodo):
        self._actualizar_fe(nodo)

        if nodo.fe == 2:  # Desbalance a la derecha
            if nodo.der.fe >= 0:
                return self._rotacion_DD(nodo)
            else:
                return self._rotacion_DI(nodo)

        if nodo.fe == -2:  # Desbalance a la izquierda
            if nodo.izq.fe <= 0:
                return self._rotacion_II(nodo)
            else:
                return self._rotacion_ID(nodo)

        return nodo  # Ya está balanceado

    # ─── Insertar ─────────────────────────────────────────────

    def _insertar(self, nodo, producto, resultado):
        if nodo is None:
            resultado[0] = True
            return NodoAVL(producto)

        nuevo_nombre = self._to_lower(producto.nombre)
        actual_nombre = self._to_lower(nodo.valor.nombre)

        if nuevo_nombre < actual_nombre:
            nodo.izq = self._insertar(nodo.izq, producto, resultado)
        elif nuevo_nombre > actual_nombre:
            nodo.der = self._insertar(nodo.der, producto, resultado)
        else:
            # Nombre duplicado, no se inserta
            resultado[0] = False
            return nodo

        return self._balancear(nodo)

    def insertar(self, producto) -> bool:
        resultado = [False]  # Lista para pasar por referencia (como bool& en C++)
        self.raiz = self._insertar(self.raiz, producto, resultado)
        return resultado[0]

    # ─── Buscar ───────────────────────────────────────────────

    def _buscar(self, nodo, nombre: str):
        if nodo is None:
            return None

        buscar_nombre = self._to_lower(nombre)
        actual_nombre = self._to_lower(nodo.valor.nombre)

        if buscar_nombre == actual_nombre:
            return nodo
        if buscar_nombre < actual_nombre:
            return self._buscar(nodo.izq, nombre)
        return self._buscar(nodo.der, nombre)

    def buscar(self, nombre: str):
        resultado = self._buscar(self.raiz, nombre)
        if resultado is None:
            return None
        return resultado.valor  # Retorna el Producto directamente

    # ─── Eliminar ─────────────────────────────────────────────

    def _minimo_nodo(self, nodo):
        while nodo.izq is not None:
            nodo = nodo.izq
        return nodo

    def _eliminar(self, nodo, nombre: str, resultado):
        if nodo is None:
            resultado[0] = False
            return None

        buscar_nombre = self._to_lower(nombre)
        actual_nombre = self._to_lower(nodo.valor.nombre)

        if buscar_nombre < actual_nombre:
            nodo.izq = self._eliminar(nodo.izq, nombre, resultado)
        elif buscar_nombre > actual_nombre:
            nodo.der = self._eliminar(nodo.der, nombre, resultado)
        else:
            resultado[0] = True

            # Caso 1: hoja
            if nodo.izq is None and nodo.der is None:
                return None
            # Caso 2: solo hijo derecho
            if nodo.izq is None:
                return nodo.der
            # Caso 3: solo hijo izquierdo
            if nodo.der is None:
                return nodo.izq
            # Caso 4: dos hijos
            sucesor = self._minimo_nodo(nodo.der)
            nodo.valor = sucesor.valor
            aux = [False]
            nodo.der = self._eliminar(nodo.der, sucesor.valor.nombre, aux)

        return self._balancear(nodo)

    def eliminar(self, nombre: str) -> bool:
        resultado = [False]
        self.raiz = self._eliminar(self.raiz, nombre, resultado)
        return resultado[0]

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
        self._inorden(nodo.izq)
        print(f"{nodo.valor.nombre} (FE: {nodo.fe})")
        self._inorden(nodo.der)