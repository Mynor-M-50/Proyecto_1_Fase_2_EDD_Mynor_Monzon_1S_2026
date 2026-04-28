class Producto:
    def __init__(self, nombre="", codigo_barras="", categoria="", fecha_vencimiento="", marca="", precio=0.0, stock=0):
        self.nombre = nombre
        self.codigo_barras = codigo_barras
        self.categoria = categoria
        self.fecha_vencimiento = fecha_vencimiento  # Formato YYYY-MM-DD
        self.marca = marca
        self.precio = precio
        self.stock = stock

    # Este método sirve para que cuando hagas print(producto) se vea bonito
    def __str__(self):
        return f"Producto: {self.nombre} | Código: {self.codigo_barras} | Stock: {self.stock}"

class Sucursal:
    def __init__(self, id_sucursal, nombre, ubicacion, t_ingreso, t_traspaso, t_despacho):
        self.id = id_sucursal
        self.nombre = nombre
        self.ubicacion = ubicacion
        self.t_ingreso = t_ingreso
        self.t_traspaso = t_traspaso
        self.t_despacho = t_despacho
        # Aquí cada sucursal tendrá su propio inventario (Catalogo)
        self.catalogo = None