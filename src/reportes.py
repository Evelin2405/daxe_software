import csv
import json
from pathlib import Path

def normalizar_fecha(fecha_str):
    """Convierte formatos de fecha mezclados (DD/MM/AAAA o DD-MM-AAAA) a AAAA-MM-DD."""
    fecha_limpia = fecha_str.strip()
    
    # Caso 1: Si ya viene en formato correcto (AAAA-MM-DD)
    if "-" in fecha_limpia and fecha_limpia.index("-") == 4:
        return fecha_limpia
        
    # Caso 2: Si viene separado por barras (DD/MM/AAAA)
    if "/" in fecha_limpia:
        partes = fecha_limpia.split("/")
        if len(partes) == 3:
            return f"{partes[2]}-{partes[1]}-{partes[0]}"
            
    # Caso 3: Si viene en formato inverso con guiones (DD-MM-AAAA)
    if "-" in fecha_limpia:
        partes = fecha_limpia.split("-")
        if len(partes) == 3 and len(partes[0]) == 2:
            return f"{partes[2]}-{partes[1]}-{partes[0]}"
            
    return fecha_limpia

def generar_reporte_csv():
    ruta_bandeja = Path("bandeja_entrada")
    if not ruta_bandeja.exists():
        print("❌ Error: La carpeta 'bandeja_entrada' no existe.")
        return

    archivos_basura = ["notas.tmp", "~$borrador.txt", "Thumbs.db", "LEEME viejo.doc"]
    mapeo_sedes = {"itagu": "Itagui", "env": "Envigado", "saba": "Sabaneta", "bell": "Bello"}
    
    pedidos_procesados = set()
    lista_validos = []

    # Recorrer ordenadamente los archivos
    for archivo in sorted(ruta_bandeja.iterdir()):
        if archivo.name in archivos_basura or archivo.stat().st_size == 0:
            continue

        id_pedido, sede_origen, fecha_origen, valor_str, estado_pedido = None, None, None, None, None

        try:
            if archivo.suffix == ".json":
                with open(archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                    id_pedido = datos.get("pedido")
                    sede_origen = datos.get("sede")
                    fecha_origen = datos.get("fecha")
                    valor_str = datos.get("valor")
                    estado_pedido = datos.get("estado")

            elif archivo.suffix == ".csv":
                with open(archivo, "r", encoding="utf-8") as f:
                    lector = csv.DictReader(f)
                    fila = next(lector)
                    id_pedido = fila.get("pedido")
                    sede_origen = fila.get("sede")
                    fecha_origen = fila.get("fecha")
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
                    fecha_origen = datos.get("fecha")
                    valor_str = datos.get("valor")
                    estado_pedido = datos.get("estado")

            # Validar si el registro está dañado
            if not id_pedido or not sede_origen or not valor_str or valor_str.startswith("-"):
                continue
                
            # Omitir si es un ID duplicado
            if id_pedido in pedidos_procesados:
                continue

            pedidos_procesados.add(id_pedido)

            # Normalizar Sede
            sede_normalizada = None
            sede_limpia = sede_origen.strip().lower()
            for patron, nombre_oficial in mapeo_sedes.items():
                if patron in sede_limpia:
                    sede_normalizada = nombre_oficial
                    break

            if not sede_normalizada:
                continue

            # Formatear la fecha
            fecha_normalizada = normalizar_fecha(fecha_origen)

            # Limpiar valor monetario
            valor_numerico = valor_str.replace("$", "").replace(".", "").replace(",", "").strip()

            lista_validos.append({
                "pedido": id_pedido,
                "sede": sede_normalizada,
                "fecha": fecha_normalizada,
                "valor": valor_numerico,
                "estado": estado_pedido.strip()
            })

        except Exception:
            continue

    # Guardar los datos limpios en la raíz como reporte.csv
    campos = ["pedido", "sede", "fecha", "valor", "estado"]
    with open("reporte.csv", "w", encoding="utf-8", newline="") as salida_csv:
        escritor = csv.DictWriter(salida_csv, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(lista_validos)

    print("✅ ¡Archivo 'reporte.csv' creado exitosamente en la raíz!")

if __name__ == "__main__":
    generar_reporte_csv()
