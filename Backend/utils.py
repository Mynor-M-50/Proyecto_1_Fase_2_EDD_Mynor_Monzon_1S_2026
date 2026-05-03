from .modelos import Producto, Sucursal
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


# ─── CSV LOADER PRODUCTOS ─────────────────────────────────────────────────────

class CSVLoader:
    def __init__(self, logger: Logger):
        self.logger = logger

    def cargar_archivo(self, ruta: str, callback) -> bool:
        """
        Formato Fase 2: SucursalID, Nombre, CodigoBarra, Categoria,
                        FechaCaducidad, Marca, Precio, Stock
        callback: función que recibe un Producto y retorna bool
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

        for linea_num, linea in enumerate(lineas[1:], start=1):
            linea = linea.strip()
            if not linea:
                continue
            if linea.startswith(',') or linea.lower().startswith('sucursalid') or linea.lower().startswith('id'):
                continue

            campos = linea.split(",")

            if len(campos) < 8:
                self.logger.error_formato(f"Linea {linea_num}: formato incompleto (esperados 8 campos)")
                continue

            try:
                p = Producto()
                p.sucursal_id       = campos[0].strip()
                p.nombre            = campos[1].strip()
                p.codigo_barras     = campos[2].strip()
                p.categoria         = campos[3].strip()
                p.fecha_vencimiento = campos[4].strip()
                p.marca             = campos[5].strip()
                p.precio            = float(campos[6].strip())
                p.stock             = int(campos[7].strip())

                # Validaciones
                if not all([p.sucursal_id, p.nombre, p.codigo_barras,
                            p.categoria, p.fecha_vencimiento, p.marca]):
                    self.logger.error(f"Linea {linea_num}: campo obligatorio vacío")
                    continue

                # Validación 10 dígitos mínimo (requisito del ingeniero)
                if len(p.codigo_barras) < 10:
                    self.logger.error(f"Linea {linea_num}: código de barras muy corto (mín. 10 dígitos) - {p.codigo_barras}")
                    continue

                if p.precio <= 0:
                    self.logger.error(f"Linea {linea_num}: precio inválido ({campos[6]})")
                    continue

                if p.stock < 0:
                    self.logger.error(f"Linea {linea_num}: stock inválido ({campos[7]})")
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


# ─── CSV LOADER SUCURSALES ────────────────────────────────────────────────────

class CSVLoaderSucursales:
    def __init__(self, logger: Logger):
        self.logger = logger

    def cargar_archivo(self, ruta: str, callback) -> bool:
        """
        Formato: ID, Nombre, Ubicacion, t_ingreso, t_traspaso, t_despacho
        callback: función que recibe una Sucursal y retorna bool
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

        for linea_num, linea in enumerate(lineas[1:], start=1):
            linea = linea.strip()
            if not linea:
                continue
            if linea.startswith(',') or linea.lower().startswith('id'):
                continue

            campos = linea.split(",")

            if len(campos) < 6:
                self.logger.error_formato(f"Linea {linea_num}: formato incompleto (esperados 6 campos)")
                continue

            try:
                s = Sucursal(
                    id_sucursal = campos[0].strip(),
                    nombre      = campos[1].strip(),
                    ubicacion   = campos[2].strip(),
                    t_ingreso   = float(campos[3].strip()),
                    t_traspaso  = float(campos[4].strip()),
                    t_despacho  = float(campos[5].strip())
                )

                # Validaciones
                if not all([s.id, s.nombre, s.ubicacion]):
                    self.logger.error(f"Linea {linea_num}: campo obligatorio vacío")
                    continue

                if s.t_ingreso < 0 or s.t_traspaso < 0 or s.t_despacho < 0:
                    self.logger.error(f"Linea {linea_num}: tiempos no pueden ser negativos")
                    continue

                if not callback(s):
                    self.logger.error_duplicado(f"Linea {linea_num}: sucursal duplicada - {s.id}")

            except Exception as e:
                self.logger.error(f"Error en linea {linea_num}: {linea} ({e})")

        self.logger.info(f"Sucursales cargadas correctamente: {ruta}")
        return True


# ─── CSV LOADER CONEXIONES ────────────────────────────────────────────────────

class CSVLoaderConexiones:
    def __init__(self, logger: Logger):
        self.logger = logger

    def cargar_archivo(self, ruta: str, callback) -> bool:
        """
        Formato: OrigenID, DestinoID, Tiempo, Costo
        callback: función que recibe (origen, destino, tiempo, costo) y retorna bool
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

        for linea_num, linea in enumerate(lineas[1:], start=1):
            linea = linea.strip()
            if not linea:
                continue
            if linea.startswith(',') or linea.lower().startswith('origen') or linea.lower().startswith('id'):
                continue

            campos = linea.split(",")

            if len(campos) < 4:
                self.logger.error_formato(f"Linea {linea_num}: formato incompleto (esperados 4 campos)")
                continue

            try:
                origen  = campos[0].strip()
                destino = campos[1].strip()
                tiempo  = float(campos[2].strip())
                costo   = float(campos[3].strip())

                if not origen or not destino:
                    self.logger.error(f"Linea {linea_num}: origen o destino vacío")
                    continue

                if tiempo < 0 or costo < 0:
                    self.logger.error(f"Linea {linea_num}: tiempo o costo negativos")
                    continue

                if not callback(origen, destino, tiempo, costo):
                    self.logger.error_duplicado(f"Linea {linea_num}: conexión duplicada {origen}→{destino}")

            except Exception as e:
                self.logger.error(f"Error en linea {linea_num}: {linea} ({e})")

        self.logger.info(f"Conexiones cargadas correctamente: {ruta}")
        return True


# ─── BENCHMARK ────────────────────────────────────────────────────────────────

class Benchmark:
    def __init__(self):
        self._inicio = None
        self._nombre_tarea = ""

    def iniciar(self, tarea: str):
        self._nombre_tarea = tarea
        self._inicio = time.perf_counter()

    def finalizar(self):
        fin = time.perf_counter()
        duracion_seg = fin - self._inicio
        duracion_us  = duracion_seg * 1_000_000
        duracion_ms  = duracion_seg * 1_000
        print(f"[BENCHMARK] {self._nombre_tarea}: {duracion_us:.0f} microsegundos ({duracion_ms:.3f} ms)")