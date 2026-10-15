import csv
import json
from pathlib import Path

def generar_reporte_mensual():
    # Estructuras de control idénticas a la lógica de Rápido Paisa
    validos = 0
    duplicados = 0
    danados = 0
    valor_entregados = 0
    por_sede = {}

    # Lista de nombres basura explícitos del cliente
    archivos_basura = ["notas.tmp", "~$borrador.txt", "Thumbs.db", "LEEME viejo.doc"]
    
    # Mapeo inverso para normalizar las variaciones de nombres de sedes
    mapeo_sedes = {
        "itagu": "Itagui", "env": "Envigado", "saba": "Sabaneta", "bell": "Bello"
    }

    ruta_bandeja = Path("bandeja_entrada")
    if not ruta_bandeja.exists():
        print("❌ Error: La carpeta 'bandeja_entrada' no existe. Ejecuta primero generar_pedidos.py")
        return

    # Set para rastrear identificadores únicos y detectar duplicados
    pedidos_procesados = set()

    # Recorrer todos los archivos del directorio de entrada
    for archivo in ruta_bandeja.iterdir():
        # Regla 1: Validar archivos basura explícitos
        if archivo.name in archivos_basura:
            danados += 1
            continue

        # Regla 2: Validar si el archivo está vacío (0 bytes)
        if archivo.stat().st_size == 0:
            danados += 1
            continue

        id_pedido = None
        sede_origen = None
        valor_str = None
        estado_pedido = None

        try:
            # Lectura según el formato del archivo
            if archivo.suffix == ".json":
                with open(archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                    id_pedido = datos.get("pedido")
                    sede_origen = datos.get("sede")
                    valor_str = datos.get("valor")
                    estado_pedido = datos.get("estado")

            elif archivo.suffix == ".csv":
                with open(archivo, "r", encoding="utf-8") as f:
                    lector = csv.DictReader(f)
                    fila = next(lector)
                    id_pedido = fila.get("pedido")
                    sede_origen = fila.get("sede")
                    valor_str = fila.get("valor")
                    estado_pedido = fila.get("estado")

            elif archivo.suffix == ".txt":
                with open(archivo, "r", encoding="utf-8") as f:
                    datos = {}
                    for linea in f:
                        if ":" in linea:
                            clave, valor = linea.split(":", 1)
                            datos[clave.strip()] = valor.strip()
                    id_pedido = datos.get("pedido")
                    sede_origen = datos.get("sede")
                    valor_str = datos.get("valor")
                    estado_pedido = datos.get("estado")

            # Regla 3: Validar datos dañados (falta de sede o valor negativo)
            if not id_pedido or not sede_origen or not valor_str or valor_str.startswith("-"):
                danados += 1
                continue

            # Regla 4: Detectar registros duplicados
            if id_pedido in pedidos_procesados:
                duplicados += 1
                continue
            
            # Registrar ID único
            pedidos_procesados.add(id_pedido)

            # Regla 5: Normalizar la sede del pedido
            sede_normalizada = None
            sede_limpia = sede_origen.strip().lower()
            for patron, nombre_oficial in mapeo_sedes.items():
                if patron in sede_limpia:
                    sede_normalizada = nombre_oficial
                    break

            if not sede_normalizada:
                danados += 1
                continue

            # Regla 6: Limpiar caracteres especiales de moneda (Lote 2 de Octubre)
            valor_numerico = valor_str.replace("$", "").replace(".", "").replace(",", "").strip()
            precio_final = int(valor_numerico)

            # Acumular registros válidos verificados
            validos += 1
            por_sede[sede_normalizada] = por_sede.get(sede_normalizada, 0) + 1

            # Calcular ingresos únicamente de los pedidos completados con éxito
            if estado_pedido.strip().lower() == "entregado":
                valor_entregados += precio_final

        except Exception:
            danados += 1

    # Escribir los resultados en la raíz del proyecto como 'resumen.txt'
    with open("resumen.txt", "w", encoding="utf-8") as salida:
        salida.write("=== RESUMEN DE LA BANDEJA DE ENTRADA ===\n")
        salida.write(f"Pedidos válidos: {validos}\n")
        salida.write(f"Pedidos duplicados: {duplicados}\n")
        salida.write(f"Pedidos dañados: {danados}\n")
        salida.write("Pedidos por sede:\n")
        for sede, conteo in sorted(por_sede.items()):
            salida.write(f"  - {sede}: {conteo}\n")
        salida.write(f"Valor total de entregados: ${valor_entregados:,}\n".replace(",", "."))

    print("✅ ¡Archivo 'resumen.txt' creado con éxito!")

if __name__ == "__main__":
    generar_reporte_mensual()
