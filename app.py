import os
import time
import statistics
import random
import threading
from flask import Flask, render_template, request, redirect, url_for, flash

from Backend.estructuras_lineales import Cola
from Backend.modelos import Producto
from Backend.catalogo import Catalogo
from Backend.grafo import Grafo
from Backend.utils import CSVLoader, CSVLoaderSucursales, CSVLoaderConexiones, Logger, Benchmark
from Backend.reportes import ReportesGraphviz

app = Flask(__name__,
            template_folder="Fronted/templates",
            static_folder="Fronted/static")

app.secret_key = "super_secret_key_proy2"

# ─── ESTADO GLOBAL ───────────────────────────────────────────────────────────
logger = Logger(nombre_archivo=os.path.join(os.path.dirname(__file__), "log.txt"))
grafo = Grafo()
sucursales = {}


# ─── HELPER ──────────────────────────────────────────────────────────────────
def get_cola_items(s):
    return {
        "ingreso":  list(s.cola_ingreso.items)  if not s.cola_ingreso.esta_vacia()  else [],
        "traspaso": list(s.cola_traspaso.items) if not s.cola_traspaso.esta_vacia() else [],
        "salida":   list(s.cola_salida.items)   if not s.cola_salida.esta_vacia()   else []
    }

def get_productos(s):
    productos = []
    actual = s.catalogo.get_lista_ordenada().get_head()
    while actual:
        productos.append(actual.get_valor())
        actual = actual.get_siguiente()
    return productos

def extraer_producto_de_cola(cola, codigo):
    nueva_cola = Cola()
    producto_encontrado = None

    while not cola.esta_vacia():
        p = cola.dequeue()
        if producto_encontrado is None and str(p.codigo_barras) == str(codigo):
            producto_encontrado = p
        else:
            nueva_cola.enqueue(p)

    return producto_encontrado, nueva_cola


def devolver_producto_a_origen(producto):
    origen_id = getattr(producto, 'origen_traslado', None)
    if not origen_id:
        return False

    s_origen = sucursales.get(origen_id)
    if not s_origen:
        return False

    existente = s_origen.catalogo.buscar_por_codigo(producto.codigo_barras)
    if not existente:
        s_origen.catalogo.agregar_producto(producto)

    return True

def limpiar_traspaso_async(sucursal, codigo, delay):
    """Hilo que limpia la cola de traspaso después de t_traspaso segundos."""
    def _limpiar():
        time.sleep(delay)
        _, nueva = extraer_producto_de_cola(sucursal.cola_traspaso, codigo)
        sucursal.cola_traspaso = nueva
    t = threading.Thread(target=_limpiar, daemon=True)
    t.start()

# ─── INDEX ───────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    total_productos = sum(s.catalogo.get_lista_ordenada().get_size() for s in sucursales.values())
    return render_template('index.html',
                        sucursales=sucursales,
                        total_sucursales=len(sucursales),
                        total_productos=total_productos)


# ─── CARGAR DATOS ────────────────────────────────────────────────────────────
import tempfile

@app.route('/cargar_datos', methods=['POST'])
def cargar_datos():
    archivos = {
        'sucursales': request.files.get('archivo_sucursales'),
        'conexiones': request.files.get('archivo_conexiones'),
        'productos':  request.files.get('archivo_productos'),
    }

    rutas_tmp = {}
    try:
        for key, f in archivos.items():
            if f and f.filename:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
                f.save(tmp.name)
                rutas_tmp[key] = tmp.name
            else:
                nombres = {'sucursales':'sucursales.csv','conexiones':'conexiones.csv','productos':'productos.csv'}
                rutas_tmp[key] = os.path.join("data", nombres[key])

        loader_s = CSVLoaderSucursales(logger)
        loader_c = CSVLoaderConexiones(logger)
        loader_p = CSVLoader(logger)

        def cb_s(s):
            if s.id in sucursales: return False
            s.catalogo = Catalogo(sucursal_id=s.id)
            sucursales[s.id] = s
            grafo.agregar_sucursal(s.id)
            return True

        def cb_c(orig, dest, t, c):
            return grafo.agregar_camino(orig, dest, t, c)

        def cb_p(p):
            s = sucursales.get(p.sucursal_id)
            if s: return s.catalogo.agregar_producto(p)
            return False

        loader_s.cargar_archivo(rutas_tmp['sucursales'], cb_s)
        loader_c.cargar_archivo(rutas_tmp['conexiones'], cb_c)
        loader_p.cargar_archivo(rutas_tmp['productos'],  cb_p)

        flash("¡Datos cargados exitosamente!", "success")

    except Exception as e:
        flash(f"Error al cargar datos: {e}", "danger")
    finally:
        for ruta in rutas_tmp.values():
            if 'tmp' in ruta or tempfile.gettempdir() in ruta:
                try:
                    os.remove(ruta)
                except:
                    pass

    return redirect(url_for('index'))

# ─── VER SUCURSAL ─────────────────────────────────────────────────────────────
@app.route('/sucursal/<sid>')
def ver_sucursal(sid):
    s = sucursales.get(sid)
    if not s:
        flash("Sucursal no encontrada", "danger")
        return redirect(url_for('index'))

    return render_template('sucursal.html',
                        sucursal=s,
                        productos=get_productos(s),
                        cola_items=get_cola_items(s))


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
    print("DEBUG: tipo:", tipo, "query:", query, "desde:", desde, "hasta:", hasta)
    print("DEBUG: resultados (repr):", repr(resultados))
    try:
        print("DEBUG: len(resultados):", len(resultados))
    except Exception:
        print("DEBUG: resultados no es una lista")

    return render_template('sucursal.html',
                        sucursal=s,
                        productos=get_productos(s),
                        cola_items=get_cola_items(s),
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
        s.cola_salida.enqueue(p)
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

    p = s.cola_salida.dequeue()
    if p:
        p.estado = "despachado"
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
    criterio  = request.args.get('criterio', 'tiempo')   # ← NUEVO
    ruta_resultado = None
    grafo_img = False

    if origen and destino:
        try:
            if algoritmo == 'floyd':
                ruta_resultado = grafo.obtener_ruta_floyd(origen, destino)
            else:
                ruta_resultado = grafo.obtener_ruta(origen, destino, criterio=criterio)  # ← NUEVO

            if ruta_resultado:
                ruta_resultado = [sucursales[x] for x in ruta_resultado if x in sucursales]
        except Exception as e:
            flash(f"Error al calcular ruta: {e}", "danger")

    if ruta_resultado:  # ← Solo genera imagen si hay ruta calculada
        try:
            camino_ids = [s.id for s in ruta_resultado]
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
                        criterio=criterio,
                        ruta_resultado=ruta_resultado,
                        grafo_img=grafo_img)


# ─── TRASLADAR ───────────────────────────────────────────────────────────────
@app.route('/trasladar', methods=['POST'])
def trasladar():
    origen_id  = request.form['origen']
    destino_id = request.form['destino']
    codigo     = request.form['codigo']

    s_origen  = sucursales.get(origen_id)
    s_destino = sucursales.get(destino_id)

    if not s_origen or not s_destino:
        flash("Sucursal inválida", "danger")
        return redirect(url_for('ver_rutas'))

    producto = s_origen.catalogo.buscar_por_codigo(codigo)
    if not producto:
        flash("Producto no encontrado en la sucursal origen", "warning")
        return redirect(url_for('ver_rutas'))

    ruta_ids = grafo.obtener_ruta(origen_id, destino_id)
    if not ruta_ids:
        flash("No existe una ruta entre estas sucursales", "danger")
        return redirect(url_for('ver_rutas'))

    # Calcular ETA
    tiempo_total = 0
    for i in range(len(ruta_ids)):
        suc_actual = sucursales[ruta_ids[i]]
        tiempo_total += suc_actual.t_ingreso + suc_actual.t_traspaso + suc_actual.t_despacho
        if i < len(ruta_ids) - 1:
            peso = grafo.get_peso(ruta_ids[i], ruta_ids[i + 1])
            if peso is not None:
                tiempo_total += peso

    # Guardar origen para posible rollback/cancelación
    producto.origen_traslado = origen_id
    producto.estado = "en_transito"

    # Eliminar del catálogo origen
    s_origen.catalogo.eliminar_producto(codigo)

    # Quitar de cola_salida del origen si estaba ahí
    _, nueva_salida = extraer_producto_de_cola(s_origen.cola_salida, codigo)
    s_origen.cola_salida = nueva_salida

    # Solo llega a ingreso del destino
    producto.estado = "en_cola_ingreso"
    s_destino.cola_ingreso.enqueue(producto)

    flash(f"🚚 Producto '{producto.nombre}' enviado de {origen_id} → {destino_id}.", "success")
    flash(f"📥 El producto ya está esperando en la sucursal {destino_id}, en Cola de Ingreso.", "info")
    flash(f"⏱️ ETA Total: {tiempo_total:.2f} segundos", "info")
    flash(f"📍 Ruta: {' → '.join(ruta_ids)}", "secondary")

    return redirect(url_for('ver_rutas'))

# ─── PROCESAR COLA INGRESO ────────────────────────────────────────────────────────
@app.route('/sucursal/<sid>/procesar_ingreso', methods=['POST'])
def procesar_ingreso(sid):
    s = sucursales.get(sid)
    if not s:
        flash("Sucursal no encontrada", "danger")
        return redirect(url_for('index'))

    producto = s.cola_ingreso.dequeue()
    if not producto:
        flash("Cola de ingreso vacía.", "warning")
        return redirect(url_for('ver_sucursal', sid=sid))

    # ── Estado: pasa a traspaso ──
    producto.estado = "en_cola_traspaso"
    s.cola_traspaso.enqueue(producto)

    # ── Entra al catálogo ──
    existente = s.catalogo.buscar_por_codigo(producto.codigo_barras)
    if not existente:
        s.catalogo.agregar_producto(producto)

    flash(f"✅ '{producto.nombre}' ingresó a {sid} y está en Cola de Traspaso.", "success")

    # ── Después de t_traspaso segundos, pasa a disponible ──
    def finalizar_traspaso(prod, sucursal):
        time.sleep(min(sucursal.t_traspaso, 5))
        prod.estado = "disponible"
        sucursal.cola_traspaso  # ya está en cola, solo cambia estado

    hilo = threading.Thread(
        target=finalizar_traspaso,
        args=(producto, s),
        daemon=True
    )
    hilo.start()

    return redirect(url_for('ver_sucursal', sid=sid))


# ─── PROCESAR COLA TRASPASO ──────────────────────────────────────────────────
"""@app.route('/sucursal/<sid>/procesar_traspaso', methods=['POST'])
def procesar_traspaso(sid):
    s = sucursales.get(sid)
    if not s:
        flash("Sucursal no encontrada", "danger")
        return redirect(url_for('index'))

    p = s.cola_traspaso.dequeue()
    if p:
        s.catalogo.agregar_producto(p)   # ✅ recién entra al catálogo
        flash(f"✅ '{p.nombre}' confirmado — ya está en el catálogo de {sid}.", "success")
    else:
        flash("Cola de traspaso vacía.", "warning")

    return redirect(url_for('ver_sucursal', sid=sid))
    
    """

@app.route('/benchmark/<sid>')
def benchmark(sid):
    s = sucursales.get(sid)
    if not s:
        return "Sucursal no encontrada", 404

    # Preparar muestras (usar items reales si existen)
    nodo = s.catalogo.get_lista_ordenada().get_head()
    items = []
    while nodo:
        items.append(nodo.get_valor())
        nodo = nodo.get_siguiente()

    if not items:
        return render_template("benchmark.html", resultados={}, sucursal=s)

    # Elegir varias muestras (hasta 20 o menos si hay pocos)
    random.seed(0)
    muestras = random.sample(items, min(20, len(items)))

    # Funciones que vamos a medir
    def lista_search(code):
        actual = s.catalogo.get_lista_ordenada().get_head()
        while actual:
            if actual.get_valor().codigo_barras == code:
                return actual.get_valor()
            actual = actual.get_siguiente()
        return None

    def avl_search(name):
        return s.catalogo.buscar_por_nombre(name)

    def hash_search(code):
        return s.catalogo.buscar_por_codigo(code)

    def bplus_search(categoria):
        return s.catalogo.buscar_por_categoria(categoria)

    # Para rango: tomar fecha mínima y máxima de la muestra y crear sub-rangos
    fechas = sorted([p.fecha_vencimiento for p in items if p.fecha_vencimiento])
    if fechas:
        mid = len(fechas) // 2
        rango_ejemplo = (fechas[0], fechas[-1])  # rango amplio
    else:
        rango_ejemplo = (None, None)

    def b_range_search(desde, hasta):
        if not desde or not hasta:
            return []
        return s.catalogo.buscar_por_rango(desde, hasta)

    # Helper de tiempo
    def medir(func, args=(), iteraciones=100):
        # warm-up
        try:
            func(*args)
        except Exception:
            pass
        tiempos = []
        for _ in range(iteraciones):
            t0 = time.perf_counter()
            func(*args)
            t1 = time.perf_counter()
            tiempos.append((t1 - t0) * 1000.0)  # ms
        return {
            "avg": round(statistics.mean(tiempos), 6),
            "min": round(min(tiempos), 6),
            "max": round(max(tiempos), 6),
            "stdev": round(statistics.pstdev(tiempos), 6),
            "n": len(tiempos)
        }

    iteraciones = 100

    # Medir: usar una muestra distinta para cada prueba
    sample = muestras[0]
    code_sample = sample.codigo_barras
    name_sample = sample.nombre
    cat_sample = sample.categoria or ""

    resultados = {}
    resultados['lista'] = medir(lambda: lista_search(code_sample), (), iteraciones)
    resultados['avl']   = medir(lambda: avl_search(name_sample), (), iteraciones)
    resultados['hash']  = medir(lambda: hash_search(code_sample), (), iteraciones)
    resultados['bplus'] = medir(lambda: bplus_search(cat_sample), (), iteraciones)
    if rango_ejemplo[0] and rango_ejemplo[1]:
        resultados['b_range'] = medir(lambda: b_range_search(rango_ejemplo[0], rango_ejemplo[1]), (), iteraciones)
    else:
        resultados['b_range'] = {"avg":0,"min":0,"max":0,"stdev":0,"n":0}

    # Añadir conteos para contexto
    resultados['counts'] = {
        "total_productos": len(items),
        "muestras_usadas": len(muestras)
    }

    return render_template("benchmark.html", resultados=resultados, sucursal=s)


# ─── ESTRUCTURAS ─────────────────────────────────────────────────────────────
@app.route('/estructura/<sid>/<tipo>')
def ver_estructura(sid, tipo):
    s = sucursales.get(sid)
    if not s:
        flash("Sucursal no encontrada", "danger")
        return redirect(url_for('index'))

    img = None
    try:
        rep = ReportesGraphviz(carpeta_extra="Fronted/static")
        if tipo == 'avl':
            rep.arbol_avl(s.catalogo.avl)
            img = "arbol_avl.png"
        elif tipo == 'b':
            rep.arbol_b(s.catalogo.arbol_b)
            img = "arbol_b.png"
        elif tipo == 'bplus':
            rep.arbol_b_plus(s.catalogo.arbol_b_plus)
            img = "arbol_b_plus.png"
        elif tipo == 'hash':
            rep.tabla_hash(s.catalogo.get_tabla_hash())
            img = "tabla_hash.png"
    except Exception as e:
        flash(f"Error generando estructura: {e}", "danger")

    return render_template('sucursal.html',
                        sucursal=s,
                        productos=get_productos(s),
                        cola_items=get_cola_items(s),
                        estructura_img=img)

# ─── CANCELAR INGRESO ────────────────────────────────────────────────────────
@app.route('/sucursal/<sid>/cancelar_ingreso/<codigo>', methods=['POST'])
def cancelar_ingreso(sid, codigo):
    s = sucursales.get(sid)
    if not s:
        flash("Sucursal no encontrada", "danger")
        return redirect(url_for('index'))

    producto, nueva_ingreso = extraer_producto_de_cola(s.cola_ingreso, codigo)
    s.cola_ingreso = nueva_ingreso

    # También limpiar de traspaso por seguridad
    producto_traspaso, nueva_traspaso = extraer_producto_de_cola(s.cola_traspaso, codigo)
    s.cola_traspaso = nueva_traspaso

    if not producto:
        producto = producto_traspaso

    if not producto:
        flash("Producto no encontrado en cola de ingreso.", "warning")
        return redirect(url_for('ver_sucursal', sid=sid))

    # Quitar del catálogo destino por si llegó a entrar
    if s.catalogo.buscar_por_codigo(codigo):
        s.catalogo.eliminar_producto(codigo)

    if devolver_producto_a_origen(producto):
        flash(f"↩️ '{producto.nombre}' fue cancelado en ingreso y regresó a su sucursal de origen.", "warning")
    else:
        flash("Se canceló el ingreso, pero no se pudo devolver automáticamente al origen.", "danger")

    return redirect(url_for('ver_sucursal', sid=sid))


# ─── CANCELAR TRASPASO ───────────────────────────────────────────────────────
@app.route('/sucursal/<sid>/cancelar_traspaso/<codigo>', methods=['POST'])
def cancelar_traspaso(sid, codigo):
    s = sucursales.get(sid)
    if not s:
        flash("Sucursal no encontrada", "danger")
        return redirect(url_for('index'))

    producto, nueva_traspaso = extraer_producto_de_cola(s.cola_traspaso, codigo)
    s.cola_traspaso = nueva_traspaso

    if not producto:
        flash("Producto no encontrado en cola de traspaso.", "warning")
    else:
        # Solo limpia la cola visualmente, el producto YA está en el catálogo
        flash(f"✅ '{producto.nombre}' confirmado en catálogo de {sid}.", "success")

    return redirect(url_for('ver_sucursal', sid=sid))

# ─── LOGS ────────────────────────────────────────────────────────────────────
@app.route('/logs')
def ver_logs():
    ruta_log = os.path.join(os.path.dirname(__file__), "log.txt")
    lineas = []
    try:
        with open(ruta_log, "r", encoding="utf-8") as f:
            lineas = f.readlines()
    except FileNotFoundError:
        flash("No se encontró el archivo log.txt", "warning")
    return render_template('logs.html', lineas=lineas)

if __name__ == '__main__':
    app.run(debug=True, port=5000)