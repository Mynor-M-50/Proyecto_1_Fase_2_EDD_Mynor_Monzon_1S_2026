import os
import graphviz


class ReportesGraphviz:

    def __init__(self, carpeta_salida: str = "Reportes"):
        self.carpeta = carpeta_salida
        os.makedirs(self.carpeta, exist_ok=True)

    def _escapar(self, texto: str) -> str:
        """Limpia el texto para que no rompa Graphviz."""
        return (str(texto)
                .replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace('{', '\\{')
                .replace('}', '\\}')
                .replace('|', '\\|')
                .replace('<', '\\<')
                .replace('>', '\\>'))

    def _guardar_formatos(self, dot_objeto, nombre: str) -> str:
        """Genera .dot, .png y .svg igual que en C++."""
        ruta_base = os.path.join(self.carpeta, nombre)

        # Guardar el .dot manual
        with open(ruta_base + ".dot", "w", encoding="utf-8") as f:
            f.write(dot_objeto.source)

        # Generar imágenes
        try:
            dot_objeto.render(ruta_base, format="png", cleanup=False)
            dot_objeto.render(ruta_base, format="svg", cleanup=True)
            print(f"[INFO] Imagenes de {nombre} generadas con éxito.")
        except Exception as e:
            print(f"[ERROR] No se pudo renderizar {nombre}: {e}")

        return ruta_base + ".svg"

    # ─── GRAFO DE SUCURSALES ──────────────────────────────────────────────────

    def grafo_sucursales(self, grafo, camino_resaltado=None) -> str:
        dot = graphviz.Graph("Sucursales", engine="neato")
        dot.attr(overlap="false", splines="true")
        dot.attr("node", shape="circle", style="filled", fillcolor="lightblue", fontsize="12")

        nodos_camino = set(camino_resaltado) if camino_resaltado else set()

        for nodo in grafo.adyacencia:
            color = "orange" if nodo in nodos_camino else "lightblue"
            dot.node(nodo, nodo, fillcolor=color)

        visitados = set()
        for origen in grafo.adyacencia:
            for destino, peso in grafo.adyacencia[origen]:
                arista = tuple(sorted((origen, destino)))
                if arista not in visitados:
                    en_camino = (camino_resaltado and origen in nodos_camino and destino in nodos_camino)
                    attrs = {"label": str(peso)}
                    if en_camino:
                        attrs["color"] = "red"
                        attrs["penwidth"] = "2.5"
                    dot.edge(origen, destino, **attrs)
                    visitados.add(arista)

        return self._guardar_formatos(dot, "grafo_sucursales")

    # ─── TABLA HASH ───────────────────────────────────────────────────────────

    def tabla_hash(self, hash_tabla):
        dot = graphviz.Digraph("TablaHash", engine="dot")
        dot.attr(rankdir="TB")  # ← Vertical
        dot.attr("node", shape="record")
        dot.attr(label="Tabla Hash (Encadenamiento)")

        # Cabecera de índices — vertical
        labels_indices = []
        for i in range(hash_tabla.get_tamanio()):
            if hash_tabla.get_cubeta(i).head is not None:
                labels_indices.append(f"<f{i}> [{i}]")

        if labels_indices:
            # Las llaves verticales usan {} dentro del record
            dot.node("indices", "{ { " + " | ".join(labels_indices) + " } }")

        for i in range(hash_tabla.get_tamanio()):
            actual = hash_tabla.get_cubeta(i).head
            if actual:
                prev_id = f"indices:f{i}"
                while actual:
                    nodo_id = f"node_h_{id(actual)}"
                    label = f"{{ {self._escapar(actual.valor.nombre)} | {actual.valor.codigo_barras} }}"
                    dot.node(nodo_id, label)
                    dot.edge(prev_id, nodo_id)
                    prev_id = nodo_id
                    actual = actual.siguiente

        return self._guardar_formatos(dot, "tabla_hash")

    # ─── ÁRBOL B ──────────────────────────────────────────────────────────────

    def arbol_b(self, arbol_b):
        dot = graphviz.Digraph("ArbolB", engine="dot")
        dot.attr(rankdir="TB")
        dot.attr("node", shape="record", style="filled", fillcolor="lightyellow")
        dot.attr(label="Arbol B (d=2) — por Fecha Vencimiento")

        def recorrer(nodo):
            if nodo is None:
                return
            nodo_id = f"node_{id(nodo)}"

            piezas = []
            for i in range(nodo.num_llaves):
                piezas.append(f"<f{i}> ")
                piezas.append(self._escapar(nodo.llaves[i].fecha_vencimiento))
            piezas.append(f"<f{nodo.num_llaves}> ")

            label = "{ { " + " | ".join(piezas) + " } }"
            dot.node(nodo_id, label)

            if not nodo.es_hoja:
                for i in range(nodo.num_llaves + 1):
                    if nodo.hijos[i] is not None:
                        dot.edge(f"{nodo_id}:f{i}", f"node_{id(nodo.hijos[i])}")
                        recorrer(nodo.hijos[i])

        if arbol_b.raiz is not None:
            recorrer(arbol_b.raiz)

        return self._guardar_formatos(dot, "arbol_b")

    # ─── ÁRBOL B+ ─────────────────────────────────────────────────────────────

    def arbol_b_plus(self, arbol_b_plus):
        dot = graphviz.Digraph("ArbolBPlus", engine="dot")
        dot.attr(label="Arbol B+ (d=2) — por Categoria", rankdir="TB")

        hojas = []

        def recorrer(nodo):
            if nodo is None: return
            nodo_id = f"node_{id(nodo)}"
            color = "palegreen" if nodo.es_hoja else "lightgreen"

            html_label = '<<TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0"><TR>'
            for i in range(nodo.num_llaves):
                if nodo.es_hoja:
                    # Hoja: nombre + categoría pequeña abajo
                    nombre = self._escapar(nodo.llaves[i].nombre)
                    cat = self._escapar(nodo.llaves[i].categoria)
                    texto = f'{nombre}<BR/><FONT POINT-SIZE="9">{cat}</FONT>'
                else:
                    # Interno: solo categoría (guía de navegación)
                    texto = self._escapar(nodo.llaves[i].categoria)
                html_label += f'<TD PORT="f{i}">{texto}</TD>'
            html_label += f'<TD PORT="f{nodo.num_llaves}"> </TD></TR></TABLE>>'

            dot.node(nodo_id, html_label, shape="plaintext", style="filled", fillcolor=color)

            if nodo.es_hoja:
                hojas.append(nodo)
            else:
                for i in range(nodo.num_llaves + 1):
                    if nodo.hijos[i]:
                        dot.edge(f"{nodo_id}:f{i}", f"node_{id(nodo.hijos[i])}:f0")
                        recorrer(nodo.hijos[i])

        if arbol_b_plus.raiz:
            recorrer(arbol_b_plus.raiz)

        if hojas:
            with dot.subgraph() as s:
                s.attr(rank="same")
                for h in hojas:
                    s.node(f"node_{id(h)}")

            for i in range(len(hojas) - 1):
                dot.edge(f"node_{id(hojas[i])}", f"node_{id(hojas[i + 1])}",
                        color="red", style="dashed", constraint="false")

        return self._guardar_formatos(dot, "arbol_b_plus")

    # ─── AVL ──────────────────────────────────────────────────────────────────

    def arbol_avl(self, avl):
        dot = graphviz.Digraph("AVL", engine="dot")
        dot.attr("node", shape="record", style="filled", fillcolor="lightblue")
        dot.attr(label="Arbol AVL de Productos")

        def recorrer(nodo):
            if nodo is None: return
            nodo_id = f"node_{id(nodo)}"
            label = f"{{ {self._escapar(nodo.valor.nombre)} | FE: {nodo.fe} }}"
            dot.node(nodo_id, label)

            if nodo.izq:
                dot.edge(nodo_id, f"node_{id(nodo.izq)}")
                recorrer(nodo.izq)
            if nodo.der:
                dot.edge(nodo_id, f"node_{id(nodo.der)}")
                recorrer(nodo.der)

        if avl.raiz:
            recorrer(avl.raiz)
        return self._guardar_formatos(dot, "arbol_avl")