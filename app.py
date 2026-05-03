import os
import shutil
from flask import Flask, render_template, request, redirect, url_for, flash

from Backend.modelos import Producto, Sucursal
from Backend.catalogo import Catalogo
from Backend.grafo import Grafo
from Backend.utils import CSVLoader, CSVLoaderSucursales, CSVLoaderConexiones, Logger
from Backend.reportes import ReportesGraphviz

app = Flask(__name__,
            template_folder="Fronted/templates",
            static_folder="Fronted/static")

app.secret_key = "super_secret_key_proy2"

# ─── ESTADO GLOBAL DEL SISTEMA ──────────────────────────────────────────────
# (Lo mantenemos en memoria mientras el servidor esté corriendo)
logger = Logger()
grafo = Grafo()
sucursales = {}  # {id_sucursal: Sucursal}


# ─── RUTAS (ENDPOINTS) ───────────────────────────────────────────────────────

@app.route('/')
def index():
    """Página principal: Resumen del sistema"""
    total_productos = sum(s.catalogo.get_lista_ordenada().get_size() for s in sucursales.values())
    return render_template('index.html',
                        sucursales=sucursales,
                        total_sucursales=len(sucursales),
                        total_productos=total_productos)


@app.route('/cargar_datos', methods=['POST'])
def cargar_datos():
    """Procesa la carga masiva de los 3 CSVs"""
    # Archivos fijos en la carpeta 'data' para el ejemplo rápido
    ruta_s = os.path.join("data", "sucursales.csv")
    ruta_c = os.path.join("data", "conexiones.csv")
    ruta_p = os.path.join("data", "productos.csv")

    try:
        loader_s = CSVLoaderSucursales(logger)
        loader_c = CSVLoaderConexiones(logger)
        loader_p = CSVLoader(logger)

        # Callbacks similares a main.py
        def cb_s(s):
            if s.id in sucursales: return False
            s.catalogo = Catalogo(sucursal_id=s.id)
            sucursales[s.id] = s
            grafo.agregar_sucursal(s.id)  # Usamos ID para el grafo
            return True

        def cb_c(orig, dest, t, c):
            return grafo.agregar_camino(orig, dest, t)

        def cb_p(p):
            s = sucursales.get(p.sucursal_id)
            if s: return s.catalogo.agregar_producto(p)
            return False

        # Ejecutar carga
        loader_s.cargar_archivo(ruta_s, cb_s)
        loader_c.cargar_archivo(ruta_c, cb_c)
        loader_p.cargar_archivo(ruta_p, cb_p)

        flash("¡Datos cargados exitosamente!", "success")
    except Exception as e:
        flash(f"Error al cargar datos: {e}", "danger")

    return redirect(url_for('index'))


@app.route('/sucursal/<sid>')
def ver_sucursal(sid):
    """Muestra el catálogo de una sucursal específica"""
    s = sucursales.get(sid)
    if not s:
        flash("Sucursal no encontrada", "danger")
        return redirect(url_for('index'))

    productos = []
    actual = s.catalogo.get_lista_ordenada().get_head()
    while actual:
        productos.append(actual.get_valor())
        actual = actual.get_siguiente()

    cola_items = list(s.cola.items) if not s.cola.esta_vacia() else []

    return render_template('sucursal.html', sucursal=s, productos=productos, cola_items=cola_items)


# ─── AGREGAR PRODUCTO ────────────────────────────────────────────────────────

@app.route('/sucursal/<sid>/agregar', methods=['POST'])
def agregar_producto(sid):
    s = sucursales.get(sid)
    if not s:
        flash("Sucursal no encontrada", "danger")
        return redirect(url_for('index'))

    try:
        p = Producto(
            sucursal_id=sid,
            codigo_barras=request.form['codigo_barras'].strip(),
            nombre=request.form['nombre'].strip(),
            categoria=request.form['categoria'].strip(),
            marca=request.form['marca'].strip(),
            precio=float(request.form['precio']),
            stock=int(request.form['stock']),
            fecha_vencimiento=request.form['fecha_vencimiento'].strip()
        )
        if len(p.codigo_barras) < 10:
            flash("El código de barras debe tener al menos 10 dígitos.", "warning")
        elif s.catalogo.agregar_producto(p):
            flash(f"Producto '{p.nombre}' agregado correctamente.", "success")
        else:
            flash(f"El producto con código '{p.codigo_barras}' ya existe (duplicado).", "warning")
    except Exception as e:
        flash(f"Error al agregar producto: {e}", "danger")

    return redirect(url_for('ver_sucursal', sid=sid))


# ─── ELIMINAR PRODUCTO ───────────────────────────────────────────────────────

@app.route('/sucursal/<sid>/eliminar/<codigo>', methods=['POST'])
def eliminar_producto(sid, codigo):
    s = sucursales.get(sid)
    if not s:
        flash("Sucursal no encontrada", "danger")
        return redirect(url_for('index'))

    try:
        s.catalogo.eliminar_producto(codigo)
        flash(f"Producto '{codigo}' eliminado.", "success")
    except Exception as e:
        flash(f"Error al eliminar: {e}", "danger")

    return redirect(url_for('ver_sucursal', sid=sid))


# ─── ROLLBACK ────────────────────────────────────────────────────────────────

@app.route('/sucursal/<sid>/rollback', methods=['POST'])
def rollback(sid):
    s = sucursales.get(sid)
    if not s:
        flash("Sucursal no encontrada", "danger")
        return redirect(url_for('index'))

    try:
        s.catalogo.rollback()
        flash("Rollback aplicado correctamente.", "info")
    except Exception as e:
        flash(f"Error en rollback: {e}", "danger")

    return redirect(url_for('ver_sucursal', sid=sid))


# ─── BÚSQUEDA ────────────────────────────────────────────────────────────────

@app.route('/sucursal/<sid>/buscar')
def buscar_producto(sid):
    s = sucursales.get(sid)
    if not s:
        flash("Sucursal no encontrada", "danger")
        return redirect(url_for('index'))

    tipo  = request.args.get('tipo', 'codigo')
    query = request.args.get('q', '').strip()
    desde = request.args.get('desde', '').strip()
    hasta = request.args.get('hasta', '').strip()
    resultados = []

    try:
        if tipo == 'codigo' and query:
            p = s.catalogo.buscar_por_codigo(query)
            if p: resultados = [p]
        elif tipo == 'nombre' and query:
            p = s.catalogo.buscar_por_nombre(query)
            if p: resultados = [p]
        elif tipo == 'categoria' and query:
            resultados = s.catalogo.buscar_por_categoria(query) or []
        elif tipo == 'rango' and desde and hasta:
            resultados = s.catalogo.buscar_por_rango(desde, hasta) or []
    except Exception as e:
        flash(f"Error en búsqueda: {e}", "danger")

    cola_items = list(s.cola.items) if not s.cola.esta_vacia() else []
    todos_productos = []
    actual = s.catalogo.get_lista_ordenada().get_head()
    while actual:
        todos_productos.append(actual.get_valor())
        actual = actual.get_siguiente()

    return render_template('sucursal.html',
                        sucursal=s,
                        productos=todos_productos,
                        cola_items=cola_items,
                        resultados=resultados,
                        busqueda_activa=True,
                        tipo=tipo,
                        query=query)


# ─── COLA DE DESPACHO ────────────────────────────────────────────────────────

@app.route('/sucursal/<sid>/encolar/<codigo>', methods=['POST'])
def encolar_producto(sid, codigo):
    s = sucursales.get(sid)
    if not s:
        flash("Sucursal no encontrada", "danger")
        return redirect(url_for('index'))

    p = s.catalogo.buscar_por_codigo(codigo)
    if p:
        s.cola.enqueue(p)
        flash(f"'{p.nombre}' encolado para despacho.", "success")
    else:
        flash("Producto no encontrado.", "warning")

    return redirect(url_for('ver_sucursal', sid=sid))


@app.route('/sucursal/<sid>/despachar', methods=['POST'])
def despachar_producto(sid):
    s = sucursales.get(sid)
    if not s:
        flash("Sucursal no encontrada", "danger")
        return redirect(url_for('index'))

    p = s.cola.dequeue()
    if p:
        flash(f"[DESPACHO] '{p.nombre}' [{p.codigo_barras}] despachado.", "success")
    else:
        flash("La cola de despacho está vacía.", "info")

    return redirect(url_for('ver_sucursal', sid=sid))


# ─── RUTAS DEL GRAFO ─────────────────────────────────────────────────────────

@app.route('/rutas')
def ver_rutas():
    origen    = request.args.get('origen', '').strip()
    destino   = request.args.get('destino', '').strip()
    algoritmo = request.args.get('algoritmo', 'dijkstra')
    ruta_resultado = None
    grafo_img = False

    if origen and destino:
        try:
            if algoritmo == 'floyd':
                ruta_resultado = grafo.obtener_ruta_floyd(origen, destino)
            else:
                ruta_resultado = grafo.obtener_ruta(origen, destino)

            if ruta_resultado:
                ruta_resultado = [sucursales[x] for x in ruta_resultado if x in sucursales]

        except Exception as e:
            flash(f"Error al calcular ruta: {e}", "danger")

    # Generar imagen del grafo (con ruta resaltada si existe)
    if not grafo.is_empty():
        try:
            camino_ids = [s.id for s in ruta_resultado] if ruta_resultado else None
            rep = ReportesGraphviz(carpeta_extra="Fronted/static")
            rep.grafo_sucursales(grafo, camino_resaltado=camino_ids)
            grafo_img = True
        except Exception as e:
            flash(f"Error generando imagen del grafo: {e}", "warning")

    return render_template('rutas.html',
                        sucursales=sucursales,
                        origen=origen,
                        destino=destino,
                        algoritmo=algoritmo,
                        ruta_resultado=ruta_resultado,
                        grafo_img=grafo_img)

@app.route('/trasladar', methods=['POST'])
def trasladar():
    origen = request.form['origen']
    destino = request.form['destino']
    codigo = request.form['codigo']

    s_origen = sucursales.get(origen)
    s_destino = sucursales.get(destino)

    if not s_origen or not s_destino:
        flash("Sucursal inválida", "danger")
        return redirect(url_for('index'))

    producto = s_origen.catalogo.buscar_por_codigo(codigo)

    if not producto:
        flash("Producto no encontrado", "warning")
        return redirect(url_for('ver_sucursal', sid=origen))

    # quitar de origen
    s_origen.catalogo.eliminar_producto(codigo)

    # simular tiempo (solo info)
    tiempo = grafo.costo_ruta(origen, destino)

    # agregar a destino
    producto.sucursal_id = destino
    s_destino.catalogo.agregar_producto(producto)

    flash(f"Producto trasladado en {tiempo} unidades de tiempo", "success")

    return redirect(url_for('ver_sucursal', sid=destino))


if __name__ == '__main__':
    app.run(debug=True, port=5000)