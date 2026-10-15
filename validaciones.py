"""Validacion de la bandeja: mueve los archivos danados a revisar/danados/.

Un archivo se considera DANADO (issue #36) si:
  - esta vacio,
  - no es un pedido (extension ajena, temporal, sin campos de pedido,
    JSON/CSV roto...),
  - no tiene sede (o la sede no es reconocible),
  - tiene un valor menor o igual a cero (o sin valor numerico).

Los archivos buenos no se tocan. Nada se sobrescribe ni se borra: si ya
existe un archivo con el mismo nombre en revisar/danados/, el nuevo se
guarda como "nombre (2).ext". Cada movimiento queda registrado, con su
motivo, en revisar/motivos_danados.csv.

Uso:
    python validacion.py                 # valida y mueve
    python validacion.py --simulacro     # solo muestra que haria, sin mover

Desde otro modulo (por ejemplo organizar.py):
    from validacion import validar_bandeja
    resultado = validar_bandeja()

Depende de sedes.py (lectura de pedidos y reconocimiento de la sede).
"""

import argparse
import csv
import math
import re
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from sedes import ArchivoInvalido, leer_pedido, sede_de_datos

CARPETA_ENTRADA = "bandeja_entrada"
CARPETA_REVISAR = "revisar"
SUBCARPETA_DANADOS = "danados"
ARCHIVO_MOTIVOS = "motivos_danados.csv"

CLAVES_VALOR = ("valor", "total", "monto")


# --------------------------------------------------------------------------
# Lectura del valor
# --------------------------------------------------------------------------
def parsear_valor(crudo):
    """Convierte el valor de un pedido a float; None si no es un numero.

    Entiende los formatos del cliente y variantes comunes:
    '5000', '-4500', '$1.500', '$ 12.000', '1.500,50', '4500.50', '(300)'.
    Un punto o coma seguido de exactamente 3 digitos se toma como separador
    de miles ('1.500' = 1500), que es la convencion colombiana.
    """
    if crudo is None or isinstance(crudo, bool):
        return None
    if isinstance(crudo, (int, float)):
        return float(crudo) if math.isfinite(crudo) else None

    texto = str(crudo).strip().lower()
    for basura in ("$", "cop", "pesos", "'", " ", "\u00a0"):
        texto = texto.replace(basura, "")
    if not texto:
        return None

    negativo = False
    if texto.startswith("(") and texto.endswith(")"):  # contabilidad: (300)
        negativo, texto = True, texto[1:-1]
    if texto and texto[0] in "-\u2212":  # '-' o signo menos unicode
        negativo, texto = True, texto[1:]
    elif texto.startswith("+"):
        texto = texto[1:]
    if not re.fullmatch(r"\d[\d.,]*", texto):
        return None

    if "." in texto and "," in texto:
        # el separador que aparece ultimo es el decimal
        decimal = "." if texto.rfind(".") > texto.rfind(",") else ","
        miles = "," if decimal == "." else "."
        texto = texto.replace(miles, "").replace(decimal, ".")
    else:
        sep = "." if "." in texto else ("," if "," in texto else None)
        if sep:
            antes, _, despues = texto.rpartition(sep)
            es_miles = texto.count(sep) > 1 or (
                len(despues) == 3 and 0 < len(antes) <= 3 and antes != "0"
            )
            texto = texto.replace(sep, "") if es_miles else antes.replace(sep, "") + "." + despues
    try:
        valor = float(texto)
    except ValueError:
        return None
    return -valor if negativo else valor


# --------------------------------------------------------------------------
# Clasificacion de un archivo
# --------------------------------------------------------------------------
def clasificar_archivo(ruta):
    """Devuelve None si el archivo es un pedido valido, o el motivo si esta danado.

    Nunca lanza excepciones por el contenido de un archivo: lo que no se
    pueda leer se considera danado, con el motivo explicado.
    """
    try:
        datos = leer_pedido(ruta)

        sede, motivo = sede_de_datos(datos)
        if sede is None:
            return motivo

        crudo = next((datos[c] for c in CLAVES_VALOR if c in datos), None)
        valor = parsear_valor(crudo)
        if valor is None:
            return "valor ausente o no numerico"
        if valor <= 0:
            return f"valor menor o igual a cero ({crudo})"
        return None

    except ArchivoInvalido as e:
        return str(e)
    except (OSError, UnicodeError, ValueError, csv.Error) as e:
        return f"no se pudo leer ({type(e).__name__})"
    except Exception as e:  # red de seguridad: un archivo raro no frena el lote
        return f"error inesperado ({type(e).__name__})"


# --------------------------------------------------------------------------
# Movimiento seguro
# --------------------------------------------------------------------------
def _destino_libre(carpeta, nombre):
    """Ruta dentro de 'carpeta' que no existe aun ('a.txt' -> 'a (2).txt')."""
    destino = carpeta / nombre
    base, ext = Path(nombre).stem, Path(nombre).suffix
    k = 2
    while destino.exists():
        destino = carpeta / f"{base} ({k}){ext}"
        k += 1
    return destino


def _registrar(ruta_log, movimientos):
    """Agrega los movimientos al CSV de motivos (se acumula entre corridas)."""
    nuevo = not ruta_log.exists()
    with open(ruta_log, "a", newline="", encoding="utf-8-sig" if nuevo else "utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["fecha", "nombre_original", "nombre_en_danados", "motivo"])
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for original, final, motivo in movimientos:
            w.writerow([ahora, original, final, motivo])


def validar_bandeja(entrada=CARPETA_ENTRADA, revisar=CARPETA_REVISAR, simulacro=False):
    """Mueve a revisar/danados/ los archivos danados de la bandeja.

    Devuelve un dict con:
      movidos      lista de (nombre_original, nombre_final, motivo)
      errores      lista de (nombre, descripcion) de los que no se pudieron mover
      conservados  cantidad de archivos validos que se dejaron en la bandeja
    Con simulacro=True no mueve ni crea nada: solo informa.
    """
    entrada, revisar = Path(entrada), Path(revisar)
    if not entrada.is_dir():
        raise FileNotFoundError(
            f"No existe la carpeta '{entrada}'. Genérala con: python generar_pedidos.py"
        )
    carpeta_danados = revisar / SUBCARPETA_DANADOS
    # Si 'revisar' estuviera dentro de la bandeja, se validaria a si misma.
    if entrada.resolve() in carpeta_danados.resolve().parents or entrada.resolve() == revisar.resolve():
        raise ValueError(f"'{revisar}' no puede estar dentro de '{entrada}'.")

    movidos, errores, conservados = [], [], 0
    archivos = sorted((p for p in entrada.iterdir() if p.is_file()),
                      key=lambda p: p.name.lower())

    for ruta in archivos:
        motivo = clasificar_archivo(ruta)
        if motivo is None:
            conservados += 1
            continue
        if simulacro:
            movidos.append((ruta.name, ruta.name, motivo))
            continue
        try:
            carpeta_danados.mkdir(parents=True, exist_ok=True)
            destino = _destino_libre(carpeta_danados, ruta.name)
            shutil.move(str(ruta), str(destino))
            movidos.append((ruta.name, destino.name, motivo))
        except OSError as e:  # archivo abierto en otro programa, sin permisos, etc.
            errores.append((ruta.name, f"{type(e).__name__}: {e.strerror or e}"))

    if movidos and not simulacro:
        _registrar(revisar / ARCHIVO_MOTIVOS, movidos)
    return {"movidos": movidos, "errores": errores, "conservados": conservados}


# --------------------------------------------------------------------------
# Linea de comandos
# --------------------------------------------------------------------------
def _imprimir_resumen(res, simulacro, revisar):
    total = len(res["movidos"]) + len(res["errores"]) + res["conservados"]
    verbo = "Se moverian" if simulacro else "Movidos"
    print(f"Archivos analizados : {total}")
    print(f"Validos (se quedan) : {res['conservados']}")
    print(f"{verbo:<20}: {len(res['movidos'])}  -> {Path(revisar) / SUBCARPETA_DANADOS}/")
    por_motivo = Counter(re.sub(r"\s*\(.*\)$", "", m) for _, _, m in res["movidos"])
    for motivo, n in por_motivo.most_common():
        print(f"    {motivo:<45} {n}")
    if res["errores"]:
        print(f"NO se pudieron mover: {len(res['errores'])}")
        for nombre, desc in res["errores"]:
            print(f"    {nombre}: {desc}")
    if simulacro:
        print("(simulacro: no se movio ningun archivo)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mueve los pedidos danados a revisar/danados/.")
    ap.add_argument("--entrada", default=CARPETA_ENTRADA, help="carpeta con los pedidos")
    ap.add_argument("--revisar", default=CARPETA_REVISAR, help="carpeta de revision")
    ap.add_argument("--simulacro", action="store_true", help="solo mostrar, sin mover")
    args = ap.parse_args(argv)

    try:
        res = validar_bandeja(args.entrada, args.revisar, args.simulacro)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    _imprimir_resumen(res, args.simulacro, args.revisar)
    return 1 if res["errores"] else 0


if __name__ == "__main__":
    sys.exit(main())