import time


# ─── LOGGER ───────────────────────────────────────────────────────────────────

class Logger:
    def __init__(self, nombre_archivo: str = "log.txt"):
        self.conteo_errores_formato = 0
        self.conteo_errores_datos   = 0
        self.conteo_duplicados      = 0

        try:
            self.archivo = open(nombre_archivo, "w", encoding="utf-8")
        except Exception:
            print("[ERROR] No se pudo abrir log.txt")
            self.archivo = None

    def __del__(self):
        if self.archivo:
            self.archivo.close()

    def info(self, mensaje: str):
        print(f"[INFO] {mensaje}")
        if self.archivo:
            self.archivo.write(f"[INFO] {mensaje}\n")

    def error(self, mensaje: str):
        # Solo va al archivo, NO a consola
        if self.archivo:
            self.archivo.write(f"[ERROR] {mensaje}\n")
        self.conteo_errores_datos += 1

    def error_formato(self, mensaje: str):
        if self.archivo:
            self.archivo.write(f"[FORMATO] {mensaje}\n")
        self.conteo_errores_formato += 1

    def error_duplicado(self, mensaje: str):
        if self.archivo:
            self.archivo.write(f"[DUPLICADO] {mensaje}\n")
        self.conteo_duplicados += 1

    def imprimir_resumen_carga(self, cargados: int):
        total = cargados + self.conteo_errores_formato + self.conteo_errores_datos + self.conteo_duplicados
        print(f"\n[CARGA] Productos cargados  : {cargados}")
        print(f"[CARGA] Errores de formato  : {self.conteo_errores_formato}")
        print(f"[CARGA] Datos inválidos     : {self.conteo_errores_datos}")
        print(f"[CARGA] Duplicados          : {self.conteo_duplicados}")
        print(f"[CARGA] Total procesado     : {total}")
        print(f"[CARGA] Detalle completo en : log.txt\n")

    def reset_contadores(self):
        self.conteo_errores_formato = 0
        self.conteo_errores_datos   = 0
        self.conteo_duplicados      = 0


# ─── CSV LOADER ───────────────────────────────────────────────────────────────

class CSVLoader:
    def __init__(self, logger: Logger):
        self.logger = logger

    def cargar_archivo(self, ruta: str, callback) -> bool:
        """
        callback: función que recibe un Producto y retorna bool
        (True si se insertó, False si es duplicado)
        """
        try:
            archivo = open(ruta, "r", encoding="utf-8")
        except Exception:
            self.logger.error(f"No pudo abrirse el archivo: {ruta}")
            return False

        with archivo:
            lineas = archivo.readlines()

        if not lineas:
            self.logger.error(f"Archivo vacío: {ruta}")
            return False

        # Leer encabezado y detectar formato
        encabezado = lineas[0].strip().split(",")
        h1 = encabezado[0].lower().strip() if len(encabezado) > 0 else ""
        h2 = encabezado[1].lower().strip() if len(encabezado) > 1 else ""

        # Formato PDF: nombre, codigobarra,...
        # Formato normal: codigoBarras, nombre,...
        formato_pdf = (h1 == "nombre" and h2 == "codigobarra")

        for linea_num, linea in enumerate(lineas[1:], start=1):
            linea = linea.strip()
            if not linea:
                continue

            campos = linea.split(",")

            if len(campos) < 7:
                self.logger.error_formato(f"Linea {linea_num}: formato incompleto")
                continue

            try:
                from modelos import Producto
                p = Producto()

                if formato_pdf:
                    p.nombre        = campos[0].strip()
                    p.codigo_barras = campos[1].strip()
                else:
                    p.codigo_barras = campos[0].strip()
                    p.nombre        = campos[1].strip()

                p.categoria        = campos[2].strip()
                p.fecha_vencimiento = campos[3].strip()
                p.marca            = campos[4].strip()
                p.precio           = float(campos[5].strip())
                p.stock            = int(campos[6].strip())

                # Validaciones
                if not all([p.codigo_barras, p.nombre, p.categoria, p.fecha_vencimiento, p.marca]):
                    self.logger.error(f"Linea {linea_num}: campo vacío detectado")
                    continue

                if p.precio <= 0:
                    self.logger.error(f"Linea {linea_num}: precio inválido ({campos[5]})")
                    continue

                if p.stock < 0:
                    self.logger.error(f"Linea {linea_num}: stock inválido ({campos[6]})")
                    continue

                if (len(p.fecha_vencimiento) != 10 or
                        p.fecha_vencimiento[4] != '-' or p.fecha_vencimiento[7] != '-'):
                    self.logger.error(f"Linea {linea_num}: fecha inválida ({p.fecha_vencimiento})")
                    continue

                if not callback(p):
                    self.logger.error_duplicado(f"Linea {linea_num}: duplicado - {p.codigo_barras}")

            except Exception as e:
                self.logger.error(f"Error en linea {linea_num}: {linea} ({e})")

        self.logger.info(f"Archivo cargado correctamente: {ruta}")
        return True


# ─── BENCHMARK ────────────────────────────────────────────────────────────────

class Benchmark:
    def __init__(self):
        self._inicio = None
        self._nombre_tarea = ""

    def iniciar(self, tarea: str):
        self._nombre_tarea = tarea
        self._inicio = time.perf_counter()  # Equivalente a high_resolution_clock

    def finalizar(self):
        fin = time.perf_counter()
        duracion_seg = fin - self._inicio
        duracion_us  = duracion_seg * 1_000_000   # microsegundos
        duracion_ms  = duracion_seg * 1_000        # milisegundos
        print(f"[BENCHMARK] {self._nombre_tarea}: {duracion_us:.0f} microsegundos ({duracion_ms:.3f} ms)")