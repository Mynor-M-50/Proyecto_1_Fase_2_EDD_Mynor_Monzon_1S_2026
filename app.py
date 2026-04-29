import os
from flask import Flask, render_template, request, redirect, url_for, flash
from Backend.modelos import Producto, Sucursal
from Backend.catalogo import Catalogo
from Backend.grafo import Grafo
from Backend.utils import CSVLoader, CSVLoaderSucursales, CSVLoaderConexiones, Logger

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

    # Obtenemos la lista de productos para mostrar en una tabla
    productos = []
    actual = s.catalogo.get_lista_ordenada().get_head()
    while actual:
        productos.append(actual.get_valor())
        actual = actual.get_siguiente()

    return render_template('sucursal.html', sucursal=s, productos=productos)


if __name__ == '__main__':
    # Debug=True para que se reinicie solo al guardar cambios
    app.run(debug=True, port=5000)