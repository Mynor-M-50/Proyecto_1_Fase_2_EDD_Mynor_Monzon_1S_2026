from catalogo import Catalogo
from utils import CSVLoader, Logger, Benchmark

catalogo = Catalogo()
logger = Logger()
loader = CSVLoader(logger)
timer = Benchmark()
csv_cargado = False


def insertar_en_catalogo(p):
    return catalogo.agregar_producto(p)


def leer_entero() -> int:
    try:
        return int(input())
    except Exception:
        return -1


def validar_consistencia():
    print("\n--- Iniciando validación de consistencia ---")
    errores = 0
    total_validados = 0

    actual = catalogo.get_lista_ordenada().get_head()

    while actual is not None:
        prod = actual.get_valor()

        if catalogo.get_avl().buscar(prod.nombre) is None:
            print(f"[ERROR] {prod.nombre} falta en AVL")
            errores += 1

        if catalogo.get_arbol_b().buscar(prod.fecha_vencimiento) is None:
            print(f"[WARNING] {prod.nombre} no encontrado en Árbol B (posible colisión por fecha)")
            errores += 1

        if catalogo.get_arbol_b_plus().buscar(prod.categoria) is None:
            print(f"[WARNING] {prod.nombre} no encontrado en Árbol B+ (posible agrupación por categoría)")
            errores += 1

        actual = actual.get_siguiente()
        total_validados += 1

    print(f"\nTotal validados: {total_validados}")
    if errores == 0:
        print("ÉXITO: todas las estructuras responden correctamente.")
    else:
        print(f"FALLO: se encontraron {errores} inconsistencias.")


def menu_busqueda():
    print("\n--- Búsqueda ---")
    print("1. Por Código de Barras (Hash)")
    print("2. Por Nombre (AVL)")
    print("3. Por Categoría (Árbol B+)")
    print("4. Por Rango de Fecha (Árbol B)")
    print("Seleccione: ", end="")
    op = leer_entero()

    if op == 1:
        codigo = input("Ingrese código de barras: ")
        timer.iniciar("Búsqueda por código")
        p = catalogo.buscar_por_codigo(codigo)
        timer.finalizar()
        if p:
            print(f"Encontrado: {p.nombre} | ${p.precio}")
        else:
            print("[INFO] No encontrado.")

    elif op == 2:
        nombre = input("Ingrese nombre: ")

        # Búsqueda secuencial (LISTA)
        timer.iniciar("Búsqueda Lista")
        actual = catalogo.get_lista_ordenada().get_head()
        encontrado = None
        while actual is not None:
            if actual.get_valor().nombre == nombre:
                encontrado = actual.get_valor()
                break
            actual = actual.get_siguiente()
        timer.finalizar()

        # Búsqueda AVL
        timer.iniciar("Búsqueda AVL")
        p = catalogo.buscar_por_nombre(nombre)
        timer.finalizar()

        if p:
            print(f"Encontrado: {p.nombre} | {p.categoria}")
        else:
            print("[INFO] No encontrado.")

    elif op == 3:
        categoria = input("Ingrese categoría: ")
        timer.iniciar("Búsqueda por categoría")
        catalogo.buscar_por_categoria(categoria)
        timer.finalizar()

    elif op == 4:
        desde = input("Ingrese fecha inicio (YYYY-MM-DD): ")
        hasta = input("Ingrese fecha fin   (YYYY-MM-DD): ")
        timer.iniciar("Búsqueda por rango")
        catalogo.buscar_por_rango(desde, hasta)
        timer.finalizar()

    else:
        print("[ERROR] Opción inválida.")


def menu_principal():
    global csv_cargado

    while True:
        print("\n========== MENÚ PRINCIPAL ==========")
        print("1. Cargar Archivo CSV")
        print("2. Buscar Producto")
        print("3. Eliminar Producto")
        print("4. Deshacer (Rollback)")
        print("5. Reportes Graphviz")
        print("6. Resumen")
        print("7. Agregar Producto Manual")
        print("0. Salir")
        print("Seleccione: ", end="")

        opcion = leer_entero()

        if opcion == 1:
            ruta = input("Ruta CSV: ")
            timer.iniciar("Carga")
            cargado = loader.cargar_archivo(ruta, insertar_en_catalogo)
            timer.finalizar()
            if cargado:
                csv_cargado = True
                logger.imprimir_resumen_carga(catalogo.get_lista_ordenada().get_size())
                validar_consistencia()
            else:
                print("[ERROR] No se pudo cargar el archivo.")
                csv_cargado = False
            logger.reset_contadores()

        elif opcion == 2:
            if csv_cargado:
                menu_busqueda()
            else:
                print("Cargue CSV primero.")

        elif opcion == 3:
            cod = input("Código a eliminar: ")
            catalogo.eliminar_producto(cod)

        elif opcion == 4:
            catalogo.rollback()

        elif opcion == 5:
            # ReporteGraficos se implementará después
            print("[INFO] Reportes Graphviz - pendiente de implementar.")

        elif opcion == 6:
            catalogo.imprimir_resumen()

        elif opcion == 7:
            from modelos import Producto
            p = Producto()
            p.codigo_barras     = input("Código de barras  : ")
            p.nombre            = input("Nombre            : ")
            p.categoria         = input("Categoría         : ")
            p.fecha_vencimiento = input("Fecha (YYYY-MM-DD): ")
            p.marca             = input("Marca             : ")
            precio_str = input("Precio            : ")
            stock_str  = input("Stock             : ")
            try:
                p.precio = float(precio_str)
                p.stock  = int(stock_str)

                if not all([p.codigo_barras, p.nombre, p.categoria, p.fecha_vencimiento, p.marca]):
                    print("[ERROR] Campos vacíos, producto no agregado.")
                elif p.precio <= 0:
                    print("[ERROR] Precio inválido, producto no agregado.")
                elif p.stock < 0:
                    print("[ERROR] Stock inválido, producto no agregado.")
                elif not catalogo.agregar_producto(p):
                    print("[ERROR] Código duplicado, producto no agregado.")
                else:
                    print("[INFO] Producto agregado correctamente.")
            except Exception:
                print("[ERROR] Precio o stock con formato inválido.")

        elif opcion == 0:
            print("¡Adiós!")
            break

        else:
            print("Opción inválida.")


if __name__ == "__main__":
    menu_principal()