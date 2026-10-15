"""Detección de pedidos duplicados."""


def separar_duplicados(pedidos):
    """Recibe una lista de tuplas (ruta, pedido) con pedidos ya válidos.
    Devuelve (unicos, duplicados): dos listas de tuplas (ruta, pedido).
    Se conserva el primero de cada número de pedido, ordenando por ruta."""
    vistos = set()
    unicos = []
    duplicados = []

    for ruta, pedido in sorted(pedidos, key=lambda item: str(item[0])):
        numero = str(pedido["pedido"]).strip()
        if numero in vistos:
            duplicados.append((ruta, pedido))
        else:
            vistos.add(numero)
            unicos.append((ruta, pedido))

    return unicos, duplicados
