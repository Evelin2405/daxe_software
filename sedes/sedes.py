"""Funciones para reconocer la sede de un pedido.

Recorre la carpeta bandeja_entrada/ (la "base de datos" del proyecto), lee
cada archivo de pedido (.txt, .csv o .json), identifica a que sede pertenece
y genera dos CSV:

  - sedes_por_archivo.csv : archivo, sede   (solo pedidos con sede valida)
  - sedes_descartados.csv : archivo, motivo (todo lo que se dejo por fuera)

Uso:
    python sedes.py
    python sedes.py --entrada bandeja_entrada --salida sedes_por_archivo.csv

Tambien se puede importar desde organizar.py:
    from sedes import reconocer_sede, procesar_archivo, generar_csv
"""

import argparse
import codecs
import csv
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

CARPETA_ENTRADA = "bandeja_entrada"
ARCHIVO_SALIDA = "sedes_por_archivo.csv"
ARCHIVO_DESCARTADOS = "sedes_descartados.csv"

# Solo estos formatos son pedidos. Todo lo demas (.tmp, .doc, .db...) se descarta.
EXTENSIONES_VALIDAS = {".txt", ".csv", ".json"}

# Archivos que crea el sistema operativo o Office y que nunca son pedidos.
NOMBRES_DEL_SISTEMA = {"thumbs.db", "desktop.ini", ".ds_store"}

# Campos que tiene un pedido. Si un archivo no trae ninguno, no es un pedido.
CLAVES_PEDIDO = {"pedido", "sede", "fecha", "valor", "estado"}
CLAVES_SEDE = ("sede", "sucursal")

# Valores que equivalen a "no hay dato".
VALORES_NULOS = {"", "null", "none", "nan", "n/a", "na", "-", "sin sede"}

# Alias ya normalizados (minusculas, sin tildes ni signos) -> nombre oficial.
# Para agregar una sede nueva o una forma de escribirla, basta una linea aqui.
SEDES_ALIAS = {
    "itagui": "Itagui",
    "envigado": "Envigado",
    "env": "Envigado",
    "sabaneta": "Sabaneta",
    "bello": "Bello",
}


class ArchivoInvalido(Exception):
    """El archivo existe pero su contenido no sirve como pedido."""


# --------------------------------------------------------------------------
# Normalizacion y reconocimiento de la sede
# --------------------------------------------------------------------------
def normalizar_texto(texto):
    """'  Itagüí. ' -> 'itagui'  (sin tildes, minusculas, sin signos)."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(c)
    )
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes.lower()).strip()


def reconocer_sede(valor):
    """Devuelve el nombre oficial de la sede, o None si no se reconoce.

    Acepta variantes de mayusculas, tildes, espacios y puntos ('ITAGÜÍ',
    'Envigado ', 'Sabaneta.', 'ENV') y frases como 'Sede Bello'. Si el
    texto menciona dos sedes distintas es ambiguo y devuelve None.
    """
    if valor is None or isinstance(valor, (dict, list, bool)):
        return None
    limpio = normalizar_texto(valor)
    if limpio in SEDES_ALIAS:
        return SEDES_ALIAS[limpio]
    encontradas = {SEDES_ALIAS[t] for t in limpio.split() if t in SEDES_ALIAS}
    return encontradas.pop() if len(encontradas) == 1 else None


def _es_nulo(valor):
    return valor is None or normalizar_texto(valor) in VALORES_NULOS


# --------------------------------------------------------------------------
# Lectura de archivos (cada formato devuelve un dict {campo: valor})
# --------------------------------------------------------------------------
def _clave(k):
    return normalizar_texto(k).replace(" ", "_") if k is not None else ""


def _leer_texto(ruta):
    """Lee el archivo tolerando BOM y codificaciones distintas a UTF-8."""
    crudo = ruta.read_bytes()
    if not crudo.strip():
        return ""
    if crudo.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return crudo.decode("utf-16")
    try:
        return crudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        return crudo.decode("latin-1")  # nunca falla


def _parsear_txt(texto):
    datos = {}
    for linea in texto.splitlines():
        m = re.match(r"^\s*([^:=]+?)\s*[:=]\s*(.*)$", linea)
        if m:
            datos[_clave(m.group(1))] = m.group(2).strip()
    return datos


def _parsear_csv(texto):
    try:
        dialecto = csv.Sniffer().sniff(texto[:2048], delimiters=",;\t|")
    except csv.Error:
        dialecto = csv.excel
    filas = list(csv.DictReader(texto.splitlines(), dialect=dialecto))
    filas = [f for f in filas if any((v or "").strip() for v in f.values()
                                     if isinstance(v, str))]
    if not filas:
        raise ArchivoInvalido("csv sin filas de datos")
    return {_clave(k): (v.strip() if isinstance(v, str) else v)
            for k, v in filas[0].items() if k is not None}


def _parsear_json(texto):
    try:
        contenido = json.loads(texto)
    except json.JSONDecodeError:
        raise ArchivoInvalido("json mal formado")
    if isinstance(contenido, list) and contenido and isinstance(contenido[0], dict):
        contenido = contenido[0]
    if not isinstance(contenido, dict):
        raise ArchivoInvalido("json sin estructura de pedido")
    return {_clave(k): v for k, v in contenido.items()}


PARSERS = {".txt": _parsear_txt, ".csv": _parsear_csv, ".json": _parsear_json}


# --------------------------------------------------------------------------
# Lectura y procesamiento de un archivo
# --------------------------------------------------------------------------
def leer_pedido(ruta):
    """Lee un archivo de la bandeja y devuelve sus campos como dict.

    Las claves salen normalizadas ('Sede ' -> 'sede'). Lanza ArchivoInvalido
    (con el motivo) si el archivo no puede ser un pedido: temporal, extension
    no soportada, vacio, mal formado o sin ningun campo de pedido. Los errores
    de disco (OSError) los propaga quien llama.
    """
    ruta = Path(ruta)
    nombre = ruta.name
    if nombre.startswith(("~$", ".")) or nombre.lower() in NOMBRES_DEL_SISTEMA:
        raise ArchivoInvalido("archivo temporal o del sistema")

    ext = ruta.suffix.lower()
    if ext not in EXTENSIONES_VALIDAS:
        raise ArchivoInvalido(f"extension no soportada ({ext or 'sin extension'})")

    texto = _leer_texto(ruta)
    if not texto.strip():
        raise ArchivoInvalido("archivo vacio")

    datos = PARSERS[ext](texto)
    if not CLAVES_PEDIDO & datos.keys():
        raise ArchivoInvalido("no es un pedido (sin campos reconocibles)")
    return datos


def sede_de_datos(datos):
    """Devuelve (sede, motivo) a partir de los campos de un pedido ya leido."""
    crudo = next((datos[c] for c in CLAVES_SEDE if c in datos), None)
    if _es_nulo(crudo):
        return None, "sede ausente o nula"
    sede = reconocer_sede(crudo)
    if sede is None:
        return None, f"sede no reconocida ({str(crudo).strip()[:40]})"
    return sede, None


def procesar_archivo(ruta):
    """Analiza un archivo y devuelve (sede, motivo).

    Si es un pedido con sede valida -> (sede, None).
    Si hay que descartarlo         -> (None, motivo).
    Nunca lanza excepciones: cualquier problema queda como motivo.
    """
    try:
        return sede_de_datos(leer_pedido(ruta))
    except ArchivoInvalido as e:
        return None, str(e)
    except (OSError, UnicodeError, ValueError, csv.Error) as e:
        return None, f"no se pudo leer ({type(e).__name__})"
    except Exception as e:  # red de seguridad: un archivo malo no frena el lote
        return None, f"error inesperado ({type(e).__name__})"


# --------------------------------------------------------------------------
# Generacion de los CSV
# --------------------------------------------------------------------------
def _escribir_csv(ruta, encabezado, filas):
    """Escribe en un temporal y reemplaza al final: nunca deja un CSV a medias.

    Usa utf-8-sig para que Excel abra bien las tildes.
    """
    ruta = Path(ruta)
    tmp = ruta.with_name(ruta.name + ".tmp")
    try:
        with open(tmp, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(encabezado)
            writer.writerows(filas)
        os.replace(tmp, ruta)
    except PermissionError:
        if tmp.exists():
            tmp.unlink()
        raise PermissionError(
            f"No se pudo escribir {ruta}. Si esta abierto en Excel, cierralo."
        )


def generar_csv(entrada=CARPETA_ENTRADA, salida=ARCHIVO_SALIDA,
                salida_descartados=ARCHIVO_DESCARTADOS):
    """Procesa toda la carpeta y escribe los CSV. Devuelve (validos, descartados)."""
    entrada = Path(entrada)
    if not entrada.is_dir():
        raise FileNotFoundError(
            f"No existe la carpeta '{entrada}'. "
            "Genérala con: python generar_pedidos.py"
        )

    # Si el CSV quedara dentro de la bandeja, la proxima corrida lo leeria.
    for destino in (salida, salida_descartados):
        if entrada.resolve() in Path(destino).resolve().parents:
            raise ValueError(f"La salida '{destino}' no puede estar dentro de '{entrada}'.")

    validos, descartados = [], []
    archivos = sorted((p for p in entrada.iterdir() if p.is_file()),
                      key=lambda p: p.name.lower())
    for ruta in archivos:
        sede, motivo = procesar_archivo(ruta)
        if sede:
            validos.append((ruta.name, sede))
        else:
            descartados.append((ruta.name, motivo))

    _escribir_csv(salida, ["nombre", "sede"], validos)
    _escribir_csv(salida_descartados, ["nombre", "motivo"], descartados)
    return validos, descartados


def _resumen(validos, descartados, salida, salida_descartados):
    print(f"Archivos analizados : {len(validos) + len(descartados)}")
    print(f"Con sede valida     : {len(validos)}  -> {salida}")
    for sede, n in sorted(Counter(s for _, s in validos).items()):
        print(f"    {sede:<10} {n}")
    print(f"Descartados         : {len(descartados)}  -> {salida_descartados}")
    # Agrupa por motivo sin el detalle entre parentesis
    por_motivo = Counter(re.sub(r"\s*\(.*\)$", "", m) for _, m in descartados)
    for motivo, n in por_motivo.most_common():
        print(f"    {motivo:<45} {n}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extrae la sede de cada pedido de la bandeja.")
    ap.add_argument("--entrada", default=CARPETA_ENTRADA, help="carpeta con los pedidos")
    ap.add_argument("--salida", default=ARCHIVO_SALIDA, help="CSV de pedidos con sede")
    ap.add_argument("--descartados", default=ARCHIVO_DESCARTADOS, help="CSV de descartados")
    args = ap.parse_args(argv)

    try:
        validos, descartados = generar_csv(args.entrada, args.salida, args.descartados)
    except (FileNotFoundError, PermissionError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    _resumen(validos, descartados, args.salida, args.descartados)
    return 0


if __name__ == "__main__":
    sys.exit(main())