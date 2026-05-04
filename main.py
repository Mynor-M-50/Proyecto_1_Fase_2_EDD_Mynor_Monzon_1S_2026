import os
from Backend.modelos import Producto, Sucursal
from Backend.catalogo import Catalogo
from Backend.utils import CSVLoader, CSVLoaderSucursales, CSVLoaderConexiones, Logger, Benchmark
from Backend.grafo import Grafo

# ─── Estado Glo al ────────────────────────────────────────────────────────────
logger   = Logger()
timer    = Benchmark()
grafo    = Grafo()
sucursales = {}        #{id_sucursal: Sucursal}
csv_cargado = False


# ─── Helpers ──────────────────────────────────────────────────────────────────

def leer_entero() -> int:
    try:
        return int(input())
    except Exception:
        return -1


def get_sucursal(sid: str):
    return sucursales.get(sid, None)


# ─── CCallbac CSV ────────────────────────────────────────────────────────────

def callback_sucursal(s: Sucursal) -> bool:
    if s.id in sucursales:
        return False  # Duplicado
    s.catalogo = Catalogo(sucursal_id=s.id)
    sucursales[s.id] = s
    grafo.agregar_sucursal(s.id)
    return True


def callback_conexion(origen: str, destino: str, tiempo: float, costo: float) -> bool:
    # Usamos tiempo como peso del grafo (puedes cambiar a costo si prefieres)
    grafo.agregar_camino(origen, destino, tiempo)
    return True


def callback_producto(p: Producto) -> bool:
    s = get_sucursal(p.sucursal_id)
    if s is None:
        logger.error(f"SucursalID no existe: {p.sucursal_id} — producto omitido: {p.codigo_barras}")
        return False
    return s.catalogo.agregar_producto(p)


# ─── Validacion ───────────────────────────────────────────────────────────────

def validar_consistencia(catalogo: Catalogo, sucursal_id: str):
    print(f"\n--- Validando consistencia: Sucursal {sucursal_id} ---")
    errores = 0
    total   = 0
    actual  = catalogo.get_lista_ordenada().get_head()

    while actual is not None:
        prod = actual.get_valor()

        if catalogo.get_avl().buscar(prod.nombre) is None:
            print(f"[ERROR] {prod.nombre} falta en AVL")
            errores += 1

        if catalogo.get_arbol_b().buscar(prod.fecha_vencimiento) is None:
            print(f"[WARNING] {prod.nombre} no encontrado en Árbol B")
            errores += 1

        if catalogo.get_arbol_b_plus().buscar(prod.categoria) is None:
            print(f"[WARNING] {prod.nombre} no encontrado en Árbol B+")
            errores += 1

        actual = actual.get_siguiente()
        total += 1

    print(f"Validados: {total} | Inconsistencias: {errores}")


# ─── Menu de Busqueda ────────────────────────────────────────────────────────────

def menu_busqueda(catalogo: Catalogo):
    print("\n--- Búsqueda ---")
    print("1. Por Código de Barras (Hash)")
    print("2. Por Nombre (AVL)")
    print("3. Por Categoría (Árbol B+)")
    print("4. Por Rango de Fecha (Árbol B)")
    print("Seleccione: ", end="")
    op = leer_entero()

    if op == 1:
        codigo = input("Código de barras: ")
        timer.iniciar("Búsqueda por código")
        p = catalogo.buscar_por_codigo(codigo)
        timer.finalizar()
        print(f"Encontrado: {p}" if p else "[INFO] No encontrado.")

    elif op == 2:
        nombre = input("Nombre: ")
        timer.iniciar("Búsqueda AVL")
        p = catalogo.buscar_por_nombre(nombre)
        timer.finalizar()
        print(f"Encontrado: {p}" if p else "[INFO] No encontrado.")

    elif op == 3:
        categoria = input("Categoría: ")
        timer.iniciar("Búsqueda por categoría")
        catalogo.buscar_por_categoria(categoria)
        timer.finalizar()

    elif op == 4:
        desde = input("Fecha inicio (YYYY-MM-DD): ")
        hasta = input("Fecha fin    (YYYY-MM-DD): ")
        timer.iniciar("Búsqueda por rango")
        catalogo.buscar_por_rango(desde, hasta)
        timer.finalizar()

    else:
        print("[ERROR] Opción inválida.")


# ─── Menu Busqueda ──────────────────────────────────────────────────────────

def menu_sucursales():
    print("\n--- Gestión de Sucursales ---")
    print("1. Ver todas las sucursales")
    print("2. Ver catálogo de una sucursal")
    print("3. Buscar producto en sucursal")
    print("4. Eliminar producto de sucursal")
    print("5. Rollback en sucursal")
    print("6. Encolar producto para despacho")
    print("7. Despachar siguiente producto")
    print("8. Ver cola de despacho")
    print("Seleccione: ", end="")
    op = leer_entero()

    if op == 1:
        if not sucursales:
            print("[INFO] No hay sucursales cargadas.")
            return
        for s in sucursales.values():
            total = s.catalogo.get_lista_ordenada().get_size()
            print(f"  [{s.id}] {s.nombre} | {s.ubicacion} | Productos: {total}")

    elif op in (2, 3, 4, 5, 6, 7, 8):
        sid = input("ID de sucursal: ")
        s = get_sucursal(sid)
        if s is None:
            print(f"[ERROR] Sucursal no encontrada: {sid}")
            return

        if op == 2:
            s.catalogo.imprimir_resumen()

        elif op == 3:
            menu_busqueda(s.catalogo)

        elif op == 4:
            cod = input("Código a eliminar: ")
            s.catalogo.eliminar_producto(cod)

        elif op == 5:
            s.catalogo.rollback()

        elif op == 6:
            cod = input("Código del producto a encolar: ")
            p = s.catalogo.buscar_por_codigo(cod)
            if p is None:
                print("[ERROR] Producto no encontrado.")
            else:
                s.cola.enqueue(p)
                print(f"[OK] {p.nombre} encolado para despacho.")

        elif op == 7:
            p = s.cola.dequeue()
            if p is None:
                print("[INFO] Cola vacía.")
            else:
                print(f"[DESPACHO] Despachando: {p.nombre} [{p.codigo_barras}]")

        elif op == 8:
            if s.cola.esta_vacia():
                print("[INFO] Cola vacía.")
            else:
                print(f"Cola de despacho - Sucursal {s.nombre}:")
                for i, p in enumerate(s.cola.items):
                    print(f"  {i + 1}. {p.nombre} [{p.codigo_barras}]")

    else:
        print("[ERROR] Opción inválida.")


# ─── Menu Grafo ───────────────────────────────────────────────────────────────

def menu_grafo():
    print("\n--- Rutas entre Sucursales ---")
    print("1. Ruta más corta (Dijkstra)")
    print("2. Ruta más corta (Floyd-Warshall)")
    print("3. Ver grafo completo")
    print("Seleccione: ", end="")
    op = leer_entero()

    if op == 1:
        origen  = input("Sucursal origen : ")
        destino = input("Sucursal destino: ")
        grafo.imprimir_ruta(origen, destino)

    elif op == 2:
        origen  = input("Sucursal origen : ")
        destino = input("Sucursal destino: ")
        grafo.imprimir_ruta_floyd(origen, destino)

    elif op == 3:
        grafo.imprimir_grafo()

    else:
        print("[ERROR] Opción inválida.")


# ─── Menu Principal ───────────────────────────────────────────────────────────

def menu_principal():
    global csv_cargado

    while True:
        print("\n========== MENÚ PRINCIPAL ==========")
        print("1. Cargar CSVs (sucursales + conexiones + productos)")
        print("2. Gestión de Sucursales")
        print("3. Rutas entre Sucursales (Grafo)")
        print("4. Reportes Graphviz")
        print("5. Resumen general")
        print("0. Salir")
        print("Seleccione: ", end="")

        opcion = leer_entero()

        if opcion == 1:
            ruta_s = input("Ruta sucursales.csv  : ")
            ruta_c = input("Ruta conexiones.csv  : ")
            ruta_p = input("Ruta productos.csv   : ")

            # Normalizar rutas
            for ruta in [ruta_s, ruta_c, ruta_p]:
                if not os.path.exists(ruta):
                    ruta = os.path.join("data", ruta)

            # Normalizar rutas correctamente
            if not os.path.exists(ruta_s):
                ruta_s = os.path.join("data", ruta_s)
            if not os.path.exists(ruta_c):
                ruta_c = os.path.join("data", ruta_c)
            if not os.path.exists(ruta_p):
                ruta_p = os.path.join("data", ruta_p)

            loader_s = CSVLoaderSucursales(logger)
            loader_c = CSVLoaderConexiones(logger)
            loader_p = CSVLoader(logger)

            print("\n[1/3] Cargando sucursales...")
            timer.iniciar("Carga sucursales")
            loader_s.cargar_archivo(ruta_s, callback_sucursal)
            timer.finalizar()

            print("[2/3] Cargando conexiones...")
            timer.iniciar("Carga conexiones")
            loader_c.cargar_archivo(ruta_c, callback_conexion)
            timer.finalizar()

            print("[3/3] Cargando productos...")
            timer.iniciar("Carga productos")
            loader_p.cargar_archivo(ruta_p, callback_producto)
            timer.finalizar()

            # Validar consistencia por sucursal
            for s in sucursales.values():
                validar_consistencia(s.catalogo, s.id)

            logger.imprimir_resumen_carga(
                sum(s.catalogo.get_lista_ordenada().get_size() for s in sucursales.values())
            )
            logger.reset_contadores()
            csv_cargado = True

        elif opcion == 2:
            if not csv_cargado:
                print("[INFO] Cargue los CSVs primero.")
            else:
                menu_sucursales()

        elif opcion == 3:
            if grafo.is_empty():
                print("[INFO] Cargue los CSVs primero.")
            else:
                menu_grafo()


        elif opcion == 4:
            if not csv_cargado:
                print("[INFO] Cargue los CSVs primero.")
            else:
                from Backend.reportes import ReportesGraphviz
                rep = ReportesGraphviz(carpeta_salida="Reportes")
                print("\n--- Generando Reportes Graphviz ---")
                print("1. Grafo de Sucursales")
                print("2. Tabla Hash (primera sucursal)")
                print("3. Árbol AVL (primera sucursal)")
                print("4. Árbol B   (primera sucursal)")
                print("5. Árbol B+  (primera sucursal)")
                print("6. Todos")
                print("Seleccione: ", end="")
                op_rep = leer_entero()

                # Tomar la primera sucursal como referencia
                primera = next(iter(sucursales.values()), None)
                if primera is None:
                    print("[ERROR] No hay sucursales cargadas.")
                else:
                    cat = primera.catalogo
                    if op_rep in (1, 6):
                        ruta = rep.grafo_sucursales(grafo)
                        print(f"[OK] Grafo guardado: {ruta}")
                    if op_rep in (2, 6):
                        ruta = rep.tabla_hash(cat.get_tabla_hash())
                        print(f"[OK] Hash guardado : {ruta}")
                    if op_rep in (3, 6):
                        ruta = rep.arbol_avl(cat.get_avl())
                        print(f"[OK] AVL guardado  : {ruta}")
                    if op_rep in (4, 6):
                        ruta = rep.arbol_b(cat.get_arbol_b())
                        print(f"[OK] Árbol B guardado : {ruta}")
                    if op_rep in (5, 6):
                        ruta = rep.arbol_b_plus(cat.get_arbol_b_plus())
                        print(f"[OK] Árbol B+ guardado: {ruta}")

        elif opcion == 5:
            total = sum(s.catalogo.get_lista_ordenada().get_size() for s in sucursales.values())
            print(f"\nSucursales cargadas : {len(sucursales)}")
            print(f"Productos totales   : {total}")
            grafo.imprimir_grafo()

        elif opcion == 0:
            print("¡Adiós!")
            break

        else:
            print("[ERROR] Opción inválida.")


if __name__ == "__main__":
    menu_principal()