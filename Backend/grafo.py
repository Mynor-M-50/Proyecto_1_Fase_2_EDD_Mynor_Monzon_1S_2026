import heapq

class Grafo:
    def __init__(self):
        # Lista de adyacencia: {nombre_sucursal: [(vecino, peso), ...]}
        self.adyacencia = {}
        self.vertices = []  # Para mantener orden en Floyd

    # ─── AGREGAR VÉRTICES Y ARISTAS ───────────────────────────

    def agregar_sucursal(self, nombre: str):
        if nombre not in self.adyacencia:
            self.adyacencia[nombre] = []
            self.vertices.append(nombre)

    def agregar_camino(self, origen: str, destino: str, peso: float):
        """Grafo NO dirigido: agrega en ambos sentidos."""
        if origen not in self.adyacencia:
            self.agregar_sucursal(origen)
        if destino not in self.adyacencia:
            self.agregar_sucursal(destino)

        # Evitar duplicados
        for vecino, _ in self.adyacencia[origen]:
            if vecino == destino:
                return

        self.adyacencia[origen].append((destino, float(peso)))
        self.adyacencia[destino].append((origen, float(peso)))

    # ─── DIJKSTRA ─────────────────────────────────────────────
    # Basado en el algoritmo del documento:
    # S = conjunto de vértices ya procesados
    # D = distancias mínimas desde el origen
    # Cola de prioridad para elegir el mínimo D[v]

    def dijkstra(self, inicio: str, fin: str):
        if inicio not in self.adyacencia or fin not in self.adyacencia:
            print(f"[ERROR] Vértice no existe en el grafo.")
            return None, float('inf')

        INF = float('inf')

        # D[i] = distancia mínima desde inicio hasta i
        D = {nodo: INF for nodo in self.adyacencia}
        D[inicio] = 0

        # Para reconstruir el camino
        predecesores = {nodo: None for nodo in self.adyacencia}

        # S = conjunto de vértices ya procesados
        S = set()

        # Cola de prioridad: (D[v], v)
        cola = [(0, inicio)]

        while cola:
            distancia_actual, v = heapq.heappop(cola)

            if v in S:
                continue

            # Agregar v a S
            S.add(v)

            if v == fin:
                break

            # Para cada w en (V - S) adyacente a v:
            # D[w] = min(D[w], D[v] + M[v,w])
            for w, peso in self.adyacencia[v]:
                if w not in S:
                    nueva_dist = D[v] + peso
                    if nueva_dist < D[w]:
                        D[w] = nueva_dist
                        predecesores[w] = v
                        heapq.heappush(cola, (nueva_dist, w))

        # Reconstruir camino
        if D[fin] == INF:
            return None, INF

        camino = []
        actual = fin
        while actual is not None:
            camino.insert(0, actual)
            actual = predecesores[actual]

        return camino, D[fin]

    def imprimir_ruta(self, inicio: str, fin: str):
        camino, costo = self.dijkstra(inicio, fin)
        if camino is None:
            print(f"[INFO] No existe ruta entre {inicio} y {fin}.")
        else:
            print(f"\nRuta más corta: {' → '.join(camino)}")
            print(f"Costo total   : {costo}")

    # ─── FLOYD-WARSHALL ───────────────────────────────────────
    # Basado en Floyd_guarda_vértices del documento:
    # M[i,j] = costo mínimo entre i y j
    # T[i,j] = vértice intermedio k usado para ir de i a j

    def floyd(self):
        n = len(self.vertices)
        if n == 0:
            return None, None

        INF = float('inf')
        idx = {v: i for i, v in enumerate(self.vertices)}

        # Inicializar M con INF, 0 en diagonal
        M = [[INF] * n for _ in range(n)]
        T = [[None] * n for _ in range(n)]  # Matriz de predecesores

        for i in range(n):
            M[i][i] = 0

        # Llenar M con los pesos conocidos
        for origen in self.adyacencia:
            i = idx[origen]
            for destino, peso in self.adyacencia[origen]:
                j = idx[destino]
                M[i][j] = peso

        # Algoritmo Floyd (3 ciclos anidados)
        # Si M[i,k] + M[k,j] < M[i,j] → actualizar M y T
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if M[i][k] + M[k][j] < M[i][j]:
                        M[i][j] = M[i][k] + M[k][j]
                        T[i][j] = k  # Guardar vértice intermedio

        return M, T

    def imprimir_ruta_floyd(self, inicio: str, fin: str):
        M, T = self.floyd()
        if M is None:
            print("[ERROR] Grafo vacío.")
            return

        idx = {v: i for i, v in enumerate(self.vertices)}

        if inicio not in idx or fin not in idx:
            print(f"[ERROR] Vértice no existe.")
            return

        i, j = idx[inicio], idx[fin]

        if M[i][j] == float('inf'):
            print(f"[INFO] No existe ruta entre {inicio} y {fin}.")
            return

        # Reconstruir camino usando T
        camino = self._reconstruir_floyd(T, i, j)
        nombres = [self.vertices[x] for x in camino]

        print(f"\n[FLOYD] Ruta más corta: {' → '.join(nombres)}")
        print(f"[FLOYD] Costo total   : {M[i][j]}")

    def _reconstruir_floyd(self, T, i, j):
        if T[i][j] is None:
            return [i, j]
        k = T[i][j]
        return self._reconstruir_floyd(T, i, k)[:-1] + self._reconstruir_floyd(T, k, j)

    # ─── UTILIDADES ───────────────────────────────────────────

    def imprimir_grafo(self):
        print("\n--- Grafo de Sucursales ---")
        visitados = set()
        for origen in self.adyacencia:
            for destino, peso in self.adyacencia[origen]:
                arista = tuple(sorted((origen, destino)))
                if arista not in visitados:
                    print(f"  {origen} ── {peso} ── {destino}")
                    visitados.add(arista)

    def generar_dot(self, camino_resaltado=None):
        """Genera código DOT para Graphviz."""
        dot = "graph G {\n"
        dot += '  node [shape=circle, style=filled, fillcolor=lightblue];\n'

        # Resaltar nodos del camino si se pasa uno
        if camino_resaltado:
            for nodo in camino_resaltado:
                dot += f'  "{nodo}" [fillcolor=orange];\n'

        visitados = set()
        for origen in self.adyacencia:
            for destino, peso in self.adyacencia[origen]:
                arista = tuple(sorted((origen, destino)))
                if arista not in visitados:
                    # Resaltar aristas del camino
                    en_camino = (camino_resaltado and
                                origen in camino_resaltado and
                                destino in camino_resaltado)
                    color = 'color=red, penwidth=2.0' if en_camino else ''
                    dot += f'  "{origen}" -- "{destino}" [label="{peso}" {color}];\n'
                    visitados.add(arista)

        dot += "}"
        return dot

    def is_empty(self) -> bool:
        return len(self.adyacencia) == 0

    # ─── WRAPPERS PARA FLASK ──────────────────────────────────────

    def obtener_ruta(self, inicio: str, fin: str):
        """Devuelve lista de IDs del camino (Dijkstra) o None si no existe."""
        camino, costo = self.dijkstra(inicio, fin)
        return camino  # None si no hay ruta

    def obtener_ruta_floyd(self, inicio: str, fin: str):
        """Devuelve lista de IDs del camino (Floyd-Warshall) o None si no existe."""
        M, T = self.floyd()
        if M is None:
            return None
        idx = {v: i for i, v in enumerate(self.vertices)}
        if inicio not in idx or fin not in idx:
            return None
        i, j = idx[inicio], idx[fin]
        if M[i][j] == float('inf'):
            return None
        camino_idx = self._reconstruir_floyd(T, i, j)
        return [self.vertices[x] for x in camino_idx]

    def costo_ruta(self, inicio, fin):
        camino, costo = self.dijkstra(inicio, fin)
        return costo

    # En la clase Grafo
    def get_peso(self, origen, destino):
        if origen in self.adyacencia:
            for vecino, peso in self.adyacencia[origen]:
                if vecino == destino:
                    return peso
        return 0