class Producto:
    def __init__(self, sucursal_id="", nombre="", codigo_barras="", categoria="",
                fecha_vencimiento="", marca="", precio=0.0, stock=0):
        self.sucursal_id = sucursal_id
        self.nombre = nombre
        self.codigo_barras = codigo_barras
        self.categoria = categoria
        self.fecha_vencimiento = fecha_vencimiento
        self.marca = marca
        self.precio = precio
        self.stock = stock

    def __str__(self):
        return f"[{self.sucursal_id}] {self.codigo_barras} - {self.nombre} | Stock: {self.stock}"


class Sucursal:
    def __init__(self, id_sucursal, nombre, ubicacion, t_ingreso, t_traspaso, t_despacho):
        self.id = id_sucursal
        self.nombre = nombre
        self.ubicacion = ubicacion
        self.t_ingreso = t_ingreso
        self.t_traspaso = t_traspaso
        self.t_despacho = t_despacho
        self.catalogo = None