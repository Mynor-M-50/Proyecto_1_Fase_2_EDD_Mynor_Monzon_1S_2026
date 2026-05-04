from .modelos import Producto
from .estructuras_lineales import ListaEnlazada, Pila
from .arbol_avl import ArbolAVL
from .arbol_b import ArbolB
from .arbol_b_plus import ArbolBPlus
from .tabla_hash import TablaHash


class Catalogo:
    def __init__(self, sucursal_id: str = ""):
        self.sucursal_id = sucursal_id
        self.lista = ListaEnlazada()
        self.lista_ordenada = ListaEnlazada()
        self.avl = ArbolAVL()
        self.arbol_b = ArbolB()
        self.arbol_b_plus = ArbolBPlus()
        self.hash = TablaHash()
        self.historial_eliminados = Pila()

        # ─── Agregar ──────────────────────────────────────────────

    def agregar_producto(self, producto: Producto) -> bool:
        # 1. Validación inicial: El codigo de barras debe ser unico (Requisito PDF)
        if self.hash.buscar(producto.codigo_barras) is not None:
            return False

        pasos = []
        try:
            # 2. Insertar en AVL (Validamos que el nombre tambien sea único para evitar lios en ruta)
            if not self.avl.insertar(producto):
                # Si tu AVL no permite duplicados, lanzamos error para hacer rollback
                raise Exception(f"Nombre duplicado en AVL: {producto.nombre}")
            pasos.append("avl")

            # 3. Insertar en el resto de estructuras
            self.lista.insertar_al_final(producto)
            pasos.append("lista")

            self.lista_ordenada.insertar_ordenado_por_nombre(producto)
            pasos.append("lista_ordenada")

            self.arbol_b.insertar(producto)
            pasos.append("b")

            self.arbol_b_plus.insertar(producto)
            pasos.append("bplus")

            # 4. Finalizar con la Hash (donde ya validamos que no existe)
            self.hash.insertar(producto)
            pasos.append("hash")

            return True

        except Exception as e:
            # ─── Condiciones Rollback ─────────────────────────────
            print(f"[ERROR CONSISTENCIA] {e}. Ejecutando limpieza...")

            if "hash" in pasos: self.hash.eliminar(producto.codigo_barras)
            if "bplus" in pasos: self.arbol_b_plus.eliminar(producto.categoria, producto.codigo_barras)
            if "b" in pasos: self.arbol_b.eliminar(producto.fecha_vencimiento)
            if "avl" in pasos: self.avl.eliminar(producto.nombre)
            if "lista_ordenada" in pasos: self.lista_ordenada.eliminar_por_codigo(producto.codigo_barras)
            if "lista" in pasos: self.lista.eliminar_por_codigo(producto.codigo_barras)

            return False

    # ─── Eliminar ─────────────────────────────────────────────

    def eliminar_producto(self, codigo: str):
        p = self.hash.buscar(codigo)
        if p is None:
            print(f"[ERROR] Producto no encontrado: {codigo}")
            return

        self.historial_eliminados.push(p)

        self.avl.eliminar(p.nombre)
        self.arbol_b.eliminar(p.fecha_vencimiento)
        self.arbol_b_plus.eliminar(p.categoria, codigo)
        self.lista.eliminar_por_codigo(codigo)
        self.lista_ordenada.eliminar_por_codigo(codigo)
        self.hash.eliminar(codigo)

        print(f"[INFO] Producto eliminado: {p.nombre} [{codigo}]")

    # ─── Rollback ─────────────────────────────────────────────

    def rollback(self):
        if self.historial_eliminados.esta_vacia():
            print("[ROLLBACK] No hay eliminaciones para deshacer.")
            return

        p = self.historial_eliminados.pop()
        print(f"[ROLLBACK] Restaurando: {p.nombre} [{p.codigo_barras}]")
        self.agregar_producto(p)
        print("[ROLLBACK] Producto restaurado exitosamente.")

    # ─── Busquedas ────────────────────────────────────────────

    def buscar_por_codigo(self, codigo: str):
        return self.hash.buscar(codigo)

    def buscar_por_nombre(self, nombre: str):
        return self.avl.buscar(nombre)

    def buscar_por_categoria(self, categoria: str):
        return self.arbol_b_plus.buscar_por_categoria(categoria)

    def buscar_por_rango(self, desde: str, hasta: str):
        return self.arbol_b.buscar_por_rango(desde, hasta)

    # ─── Resumen ──────────────────────────────────────────────

    def imprimir_resumen(self):
        print(f"\n--- Resumen Catálogo Sucursal: {self.sucursal_id or 'General'} ---")
        print(f"Total productos: {self.lista.get_size()}")

    # ─── Getters ──────────────────────────────────────────────

    def get_avl(self):            return self.avl
    def get_arbol_b(self):        return self.arbol_b
    def get_arbol_b_plus(self):   return self.arbol_b_plus
    def get_tabla_hash(self):     return self.hash
    def get_lista_ordenada(self): return self.lista_ordenada