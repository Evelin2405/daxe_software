"""
Generador de la bandeja de entrada de Rapido Paisa.

Crea la carpeta bandeja_entrada/ con los archivos de pedidos tal como
los deja el cliente: nombres desordenados, formatos mezclados y errores.

Uso:
    python generar_pedidos.py            -> lote 1 (septiembre)
    python generar_pedidos.py --lote 2   -> lote 2 (octubre)

No modifiques este archivo. Tu trabajo va en tus propios scripts.
"""
import json
import random
import shutil
import sys
from pathlib import Path

SEDES = {
    "Itagui": ["Itagui", "ITAGUI", "itagui", "Itagüí", "itagüi"],
    "Envigado": ["Envigado", "ENVIGADO", "envigado", "Envigado ", "ENV"],
    "Sabaneta": ["Sabaneta", "SABANETA", "sabaneta", "Sabaneta."],
    "Bello": ["Bello", "BELLO", "bello"],
}
ESTADOS = ["entregado", "entregado", "entregado", "cancelado", "pendiente"]


def _fecha(rng, anio, mes, dia):
    estilo = rng.choice(["iso", "dmy", "barra"])
    if estilo == "iso":
        return f"{anio}-{mes:02d}-{dia:02d}"
    if estilo == "dmy":
        return f"{dia:02d}-{mes:02d}-{anio}"
    return f"{dia:02d}/{mes:02d}/{anio}"


def _valor(rng, numero, lote):
    if lote == 2 and rng.random() < 0.5:
        return "$" + f"{numero:,}".replace(",", ".")
    return str(numero)


def _contenido(ext, p):
    if ext == "json":
        return json.dumps(p, ensure_ascii=False, indent=2)
    if ext == "csv":
        return "pedido,sede,fecha,valor,estado\n" + ",".join(p.values()) + "\n"
    return "".join(f"{k}: {v}\n" for k, v in p.items())


def _nombre(rng, p, ext):
    sede = p["sede"].strip().replace(" ", "")
    fecha = p["fecha"].replace("/", "")
    plantilla = rng.choice([
        "pedido {n} {s} {f}", "PED_{n}_{s}_{f}", "factura-{n}-{s}",
        "{s}_{n}", "pedido{n}", "Copia de pedido {n} {s}",
    ])
    return plantilla.format(n=p["pedido"], s=sede, f=fecha) + "." + ext


def construir(lote=1):
    """Devuelve (archivos, verdad). archivos = lista de (nombre, contenido)."""
    rng = random.Random(3600 + lote)
    mes = 9 if lote == 1 else 10
    sedes = ["Itagui", "Envigado", "Sabaneta"] + (["Bello"] if lote == 2 else [])
    inicio = 1000 * lote
    archivos, usados = [], set()
    verdad = {"validos": 0, "duplicados": 0, "danados": 0,
              "por_sede": {s: 0 for s in sedes}, "valor_entregados": 0}

    def agregar(nombre, contenido):
        base, _, ext = nombre.rpartition(".")
        k = 2
        while nombre.lower() in usados:
            nombre = f"{base} ({k}).{ext}"
            k += 1
        usados.add(nombre.lower())
        archivos.append((nombre, contenido))

    for i in range(240):
        sede = rng.choice(sedes)
        numero = rng.randrange(8, 180) * 500
        estado = rng.choice(ESTADOS)
        p = {
            "pedido": f"{inicio + i:04d}",
            "sede": rng.choice(SEDES[sede]),
            "fecha": _fecha(rng, 2026, mes, rng.randint(1, 28)),
            "valor": _valor(rng, numero, lote),
            "estado": estado,
        }
        suerte = rng.random()
        ext = rng.choice(["txt", "csv", "json"])
        if suerte < 0.04:                      # archivo vacio
            agregar(_nombre(rng, p, ext), "")
            verdad["danados"] += 1
            continue
        if suerte < 0.07:                      # valor negativo
            p["valor"] = "-" + str(numero)
            agregar(_nombre(rng, p, ext), _contenido(ext, p))
            verdad["danados"] += 1
            continue
        if suerte < 0.10:                      # falta la sede
            p["sede"] = ""
            agregar(_nombre(rng, p, ext), _contenido(ext, p))
            verdad["danados"] += 1
            continue
        agregar(_nombre(rng, p, ext), _contenido(ext, p))
        verdad["validos"] += 1
        verdad["por_sede"][sede] += 1
        if estado == "entregado":
            verdad["valor_entregados"] += numero
        if rng.random() < 0.09:                # el mismo pedido, repetido
            otra = rng.choice(["txt", "csv", "json"])
            agregar(_nombre(rng, p, otra), _contenido(otra, p))
            verdad["duplicados"] += 1

    for basura in ["notas.tmp", "~$borrador.txt", "Thumbs.db", "LEEME viejo.doc"]:
        agregar(basura, "esto no es un pedido\n")
        verdad["danados"] += 1

    rng.shuffle(archivos)
    return archivos, verdad


def main():
    lote = 2 if "--lote" in sys.argv and sys.argv[-1] == "2" else 1
    destino = Path("bandeja_entrada")
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir()
    archivos, _ = construir(lote)
    for nombre, contenido in archivos:
        (destino / nombre).write_text(contenido, encoding="utf-8")
    print(f"Lote {lote}: se crearon {len(archivos)} archivos en {destino}/")


if __name__ == "__main__":
    main()
