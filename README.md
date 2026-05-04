#  Sistema de Gestión de Supermercado
### Red de Sucursales con Estructuras de Datos Avanzadas

> Proyecto académico — Estructura de Datos, Sección A  
> Universidad de San Carlos de Guatemala · CUNOC

---

##  Descripción

Sistema web desarrollado en **Python + Flask** que gestiona un catálogo de productos distribuido en múltiples sucursales interconectadas. Implementa estructuras de datos avanzadas **desde cero**:

| Estructura  | Propósito |
|-------------|---|
| Lista Enlazada | Almacenamiento básico (ordenada y no ordenada) |
| Árbol AVL   | Búsqueda por nombre — `O(log n)` |
| Árbol B     | Búsqueda por rango de fechas — `O(log n + k)` |
| Árbol B+    | Búsqueda por categoría — `O(log n + k)` |
| Tabla Hash  | Búsqueda por código de barras — `O(1)` promedio |
| Pila        | Rollback / deshacer eliminaciones |
| Colas      | Simulación de flujo de productos |
| Grafo     | Red de sucursales con Dijkstra y Floyd-Warshall |

---

##  Documentación

| Documento | Enlace                                           |
|---|--------------------------------------------------|
|  Manual de Usuario | [Ver PDF](./Manual_De_Usuario_Proyecto_2.pdf)             |
|  TADs de Estructuras | [Ver PDF](./Reporte_TAD's_Proyecto_Fase_2.pdf)   |
|  Reporte Técnico | [Ver PDF](./Reporte_Tecnico_Proyecto_Fase_2.pdf) |

##  Diagrama de Clases (UML)

![Diagrama UML](./UML_Proyecto_Fase_2.png)

##  Características Principales

-  **Múltiples sucursales** — cada una con su propio inventario independiente
-  **Búsqueda optimizada** por 4 criterios distintos
-  **Transferencia** de productos entre sucursales con simulación de tiempos reales
-  **Rollback** para deshacer eliminaciones mediante pila
-  **Benchmark** de todas las estructuras con métricas de tiempo
-  **Visualizaciones gráficas** con Graphviz (AVL, B, B+, Hash, Grafo)
-  **Carga masiva** desde archivos CSV con validaciones robustas
-  **Logs detallados** de errores y duplicados

---

##  Tecnologías

| Tecnología | Propósito |
|---|---|
| Python 3.8+ | Lenguaje principal |
| Flask | Framework web |
| Graphviz | Visualización de estructuras |
| Threading | Simulación asíncrona de transferencias |
| HTML / CSS / Bootstrap | Interfaz de usuario responsive |

---

##  Instalación

### Requisitos previos

- Python 3.8+
- Graphviz instalado en el sistema

```bash
# Ubuntu / Debian
sudo apt install graphviz

# macOS
brew install graphviz

# Windows — descargar desde https://graphviz.org/download/
```

### Pasos

```bash
# 1. Entrar al directorio del proyecto
cd Proyecto_1_Fase_2_EDD_Mynor_Monzon_1S_2026-main

# 2. Crear entorno virtual
python3 -m venv venv

# 3. Activar entorno virtual
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Ejecutar la aplicación
python3 app.py
```

Abrir en el navegador → http://localhost:5000

---

##  Archivos CSV de Ejemplo

**`sucursales.csv`**
```csv
ID,Nombre,Ubicacion,t_ingreso,t_traspaso,t_despacho
CEN,Central,Zona 1,2,3,1
NTE,Norte,Zona 4,1,2,1
SUR,Sur,Zona 7,3,4,2
```

**`conexiones.csv`**
```csv
OrigenID,DestinoID,Tiempo,Costo
CEN,NTE,5,10
CEN,SUR,8,15
NTE,EST,4,8
```

**`productos.csv`**
```csv
SucursalID,Nombre,CodigoBarra,Categoria,FechaCaducidad,Marca,Precio,Stock
CEN,Leche Entera,7501001234567,Lácteos,2026-05-15,Lala,18.50,100
CEN,Pan Integral,7501001234568,Panadería,2026-04-30,Bimbo,22.00,50
```

---

##  Uso Básico

1. **Cargar datos** — clic en "Cargar Archivos Masivos" y seleccionar los CSV
2. **Explorar sucursales** — clic en cualquier sucursal para ver su catálogo
3. **Buscar productos** — elegir criterio (código, nombre, categoría o rango de fechas)
4. **Transferir productos** — ir a "Ver Red de Rutas", calcular ruta y enviar producto
5. **Ver rendimiento** — entrar a una sucursal y hacer clic en "Benchmark"
6. **Ver estructuras** — clic en AVL, Árbol B, Árbol B+ o Hash para ver la visualización

---

##  Complejidades

| Estructura | Operación | Complejidad |
|---|---|---|
| Lista Enlazada | Búsqueda | `O(n)` |
| Árbol AVL | Búsqueda por nombre | `O(log n)` |
| Árbol B (d=2) | Rango de fechas | `O(log n + k)` |
| Árbol B+ (d=2) | Búsqueda por categoría | `O(log n + k)` |
| Tabla Hash | Búsqueda por código | `O(1)` promedio |
| Pila / Cola | Inserción y extracción | `O(1)` |
| Dijkstra | Ruta individual | `O((V+E) log V)` |
| Floyd-Warshall | Precálculo todas las rutas | `O(V³)` |

---

##  Visualizaciones Generadas

Las imágenes se guardan automáticamente en `Fronted/static/`:

| Archivo | Estructura |
|---|---|
| `arbol_avl.png` | Árbol AVL |
| `arbol_b.png` | Árbol B |
| `arbol_b_plus.png` | Árbol B+ |
| `tabla_hash.png` | Tabla Hash |
| `grafo_sucursales.png` | Red de sucursales |

---

##  Solución de Problemas

| Problema | Solución |
|---|---|
| `ModuleNotFoundError: flask` | Activar el entorno virtual y correr `pip install -r requirements.txt` |
| No se generan imágenes PNG | Instalar Graphviz en el sistema |
| Puerto 5000 en uso | Cambiar el puerto en `app.py` o cerrar la otra aplicación |
| Las transferencias no avanzan | Esperar según los tiempos `t_ingreso`, `t_traspaso`, `t_despacho` del CSV |
| Producto duplicado | El código de barras debe ser único por sucursal |

---

##  Autor

**Mynor Miguel Monzón Martínez**  
Carnet: `202230884`  
Curso: Estructura de Datos — Sección A  
Docente: Mario Moisés Ramírez Tobar

---

##  Licencia

Proyecto académico — Universidad de San Carlos de Guatemala · CUNOC