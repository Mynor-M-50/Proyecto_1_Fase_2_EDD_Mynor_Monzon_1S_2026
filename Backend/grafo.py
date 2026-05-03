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

    def agregar_camino(self, origen: str, destino: str, tiempo: float, costo: float = None):
        """Grafo NO dirigido: agrega en ambos sentidos."""
        if origen not in self.adyacencia:
            self.agregar_sucursal(origen)
        if destino not in self.adyacencia:
            self.agregar_sucursal(destino)

        # Evitar duplicados
        for vecino, _, __ in self.adyacencia[origen]:
            if vecino == destino:
                return

        costo = costo if costo is not None else tiempo
        self.adyacencia[origen].append((destino, float(tiempo), float(costo)))
        self.adyacencia[destino].append((origen, float(tiempo), float(costo)))

    # ─── DIJKSTRA ─────────────────────────────────────────────
    # Basado en el algoritmo del documento:
    # S = conjunto de vértices ya procesados
    # D = distancias mínimas desde el origen
    # Cola de prioridad para elegir el mínimo D[v]

    def dijkstra(self, inicio: str, fin: str, criterio: str = 'tiempo'):
        if inicio not in self.adyacencia or fin not in self.adyacencia:
            return None, float('inf')

        INF = float('inf')
        D = {nodo: INF for nodo in self.adyacencia}
        D[inicio] = 0
        predecesores = {nodo: None for nodo in self.adyacencia}
        S = set()
        cola = [(0, inicio)]

        while cola:
            distancia_actual, v = heapq.heappop(cola)
            if v in S:
                continue
            S.add(v)
            if v == fin:
                break

            for vecino_data in self.adyacencia[v]:
                w = vecino_data[0]
                t = vecino_data[1]
                c = vecino_data[2] if len(vecino_data) > 2 else t
                peso = c if criterio == 'costo' else t

                if w not in S:
                    nueva_dist = D[v] + peso
                    if nueva_dist < D[w]:
                        D[w] = nueva_dist
                        predecesores[w] = v
                        heapq.heappush(cola, (nueva_dist, w))

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
            for vecino_data in self.adyacencia[origen]:
                destino = vecino_data[0]
                tiempo = vecino_data[1]
                costo = vecino_data[2] if len(vecino_data) > 2 else vecino_data[1]
                j = idx[destino]
                M[i][j] = tiempo

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
            for vecino_data in self.adyacencia[origen]:
                destino = vecino_data[0]
                peso = vecino_data[1]
                arista = tuple(sorted((origen, destino)))
                if arista not in visitados:
                    print(f"  {origen} ── {peso} ── {destino}")
                    visitados.add(arista)

    def generar_dot(self, camino_resaltado=None):
        dot = "graph G {\n"
        dot += '  node [shape=circle, style=filled, fillcolor=lightblue];\n'

        if camino_resaltado:
            for nodo in camino_resaltado:
                dot += f'  "{nodo}" [fillcolor=orange];\n'

        visitados = set()
        for origen in self.adyacencia:
            for vecino_data in self.adyacencia[origen]:
                destino = vecino_data[0]
                t = vecino_data[1]
                c = vecino_data[2] if len(vecino_data) > 2 else t
                arista = tuple(sorted((origen, destino)))
                if arista not in visitados:
                    en_camino = (camino_resaltado and
                                origen in camino_resaltado and
                                destino in camino_resaltado)
                    color = 'color=red, penwidth=2.0' if en_camino else ''
                    dot += f'  "{origen}" -- "{destino}" [label="t:{t} c:{c}" {color}];\n'
                    visitados.add(arista)

        dot += "}"
        return dot

    def is_empty(self) -> bool:
        return len(self.adyacencia) == 0

    # ─── WRAPPERS PARA FLASK ──────────────────────────────────────
    def obtener_ruta(self, inicio: str, fin: str, criterio: str = 'tiempo'):
        """Devuelve lista de IDs del camino (Dijkstra) o None si no existe."""
        camino, costo = self.dijkstra(inicio, fin, criterio=criterio)
        return camino

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

    def get_peso(self, origen, destino, criterio='tiempo'):
        if origen in self.adyacencia:
            for vecino_data in self.adyacencia[origen]:
                if vecino_data[0] == destino:
                    t = vecino_data[1]
                    c = vecino_data[2] if len(vecino_data) > 2 else t
                    return c if criterio == 'costo' else t
        return 0