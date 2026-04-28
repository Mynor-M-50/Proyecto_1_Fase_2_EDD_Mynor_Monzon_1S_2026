from modelos import Producto
from estructuras_lineales import ListaEnlazada, Pila
from arbol_avl import ArbolAVL
from arbol_b import ArbolB
from arbol_b_plus import ArbolBPlus
from tabla_hash import TablaHash


class Catalogo:
    def __init__(self):
        self.lista = ListaEnlazada()
        self.lista_ordenada = ListaEnlazada()
        self.avl = ArbolAVL()
        self.arbol_b = ArbolB()
        self.arbol_b_plus = ArbolBPlus()
        self.hash = TablaHash()
        self.historial_eliminados = Pila()

    # ─── AGREGAR ──────────────────────────────────────────────

    def agregar_producto(self, producto: Producto) -> bool:
        # Validación: evitar duplicados usando hash
        if self.hash.buscar(producto.codigo_barras) is not None:
            return False

        self.lista.insertar_al_final(producto)
        self.lista_ordenada.insertar_ordenado_por_nombre(producto)

        insertado_avl = self.avl.insertar(producto)
        if not insertado_avl:
            print(f"[WARNING] Nombre duplicado en AVL, no indexado: {producto.nombre}")

        # Árbol B y B+ indexan por claves no únicas (fecha y categoría)
        self.arbol_b.insertar(producto)
        self.arbol_b_plus.insertar(producto)

        self.hash.insertar(producto)
        return True

    # ─── ELIMINAR ─────────────────────────────────────────────

    def eliminar_producto(self, codigo: str):
        p = self.hash.buscar(codigo)
        if p is None:
            print(f"[ERROR] Producto no encontrado: {codigo}")
            return

        # Guardar copia en la pila antes de eliminar
        self.historial_eliminados.push(p)

        nombre    = p.nombre
        fecha     = p.fecha_vencimiento
        categoria = p.categoria

        self.avl.eliminar(nombre)
        self.arbol_b.eliminar(fecha)
        self.arbol_b_plus.eliminar(categoria, codigo)
        self.lista.eliminar_por_codigo(codigo)
        self.hash.eliminar(codigo)

        print(f"[INFO] Producto eliminado y guardado en historial: {nombre} [{codigo}]")

    # ─── ROLLBACK ─────────────────────────────────────────────

    def rollback(self):
        if self.historial_eliminados.esta_vacia():
            print("[ROLLBACK] No hay eliminaciones para deshacer.")
            return

        p = self.historial_eliminados.pop()
        print(f"[ROLLBACK] Restaurando: {p.nombre} [{p.codigo_barras}]")
        self.agregar_producto(p)
        print("[ROLLBACK] Producto restaurado exitosamente.")

    # ─── BÚSQUEDAS ────────────────────────────────────────────

    def buscar_por_codigo(self, codigo: str):
        return self.hash.buscar(codigo)

    def buscar_por_nombre(self, nombre: str):
        return self.avl.buscar(nombre)

    def buscar_por_categoria(self, categoria: str):
        self.arbol_b_plus.buscar_por_categoria(categoria)

    def buscar_por_rango(self, desde: str, hasta: str):
        self.arbol_b.buscar_por_rango(desde, hasta)

    # ─── RESUMEN ──────────────────────────────────────────────

    def imprimir_resumen(self):
        print("\n--- Resumen Catálogo ---")
        print(f"Total productos: {self.lista.get_size()}")

    # ─── GETTERS ──────────────────────────────────────────────

    def get_avl(self):
        return self.avl

    def get_arbol_b(self):
        return self.arbol_b

    def get_arbol_b_plus(self):
        return self.arbol_b_plus

    def get_tabla_hash(self):
        return self.hash

    def get_lista_ordenada(self):
        return self.lista_ordenada