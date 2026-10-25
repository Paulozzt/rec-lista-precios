"""Baja la hoja "LISTA WEB" publicada como CSV y escribe data/precios.json.

La web es solo mayorista: se publican únicamente los precios por base de cada
nivel (BRONCE, PLATA, ORO). El precio minorista no se lee ni se escribe.

La hoja tiene que tener estas columnas, con estos títulos (como en LISTAS):
    DESCRIPCION | TAMAÑO EN CM | BRONCE | PLATA | ORO

Se toman las filas cuya DESCRIPCION empieza con "BASE". Como todas las formas
tienen el mismo precio por medida, alcanza con la primera fila de cada medida.
Las filas sin medida (notas internas), los packs y las medidas tipo "15 X 22"
(tablas) se ignoran.

También acepta la hoja PRECIOS de "Lista de precios REC" (la misma que lee el
cotizador): columnas producto | medida_cm | forma | bronce | plata | oro. Se toman
las filas con producto "Base" y sin forma (el precio mayorista es el mismo para
todas las formas).

Uso:  SHEET_CSV_URL="https://docs.google.com/.../pub?gid=...&output=csv" python scripts/actualizar_precios.py
"""

import csv
import io
import json
import os
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

SALIDA = Path(os.environ.get("SALIDA_JSON") or Path(__file__).resolve().parent.parent / "data" / "precios.json")
NIVELES = ["bronce", "plata", "oro"]


def numero(valor):
    """Acepta 1046, 1046.0, "$ 1.046" o "1.046,50". Devuelve None si no es un número."""
    texto = str(valor).replace("$", "").replace(" ", "").strip()
    if not texto:
        return None
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?|\d+,\d+", texto):  # formato argentino
        return float(texto.replace(".", "").replace(",", "."))
    try:
        return float(texto)
    except ValueError:
        return None


def main():
    url = os.environ.get("SHEET_CSV_URL")
    if not url:
        sys.exit("Falta la variable SHEET_CSV_URL")

    with urllib.request.urlopen(url, timeout=30) as resp:
        texto = resp.read().decode("utf-8")

    medidas = {}
    for fila in csv.DictReader(io.StringIO(texto)):
        fila = {(k or "").strip().upper(): v for k, v in fila.items()}
        if "MEDIDA_CM" in fila:  # hoja PRECIOS de "Lista de precios REC"
            es_base = (fila.get("PRODUCTO") or "").strip().upper() == "BASE" and not (fila.get("FORMA") or "").strip()
            cm = numero(fila.get("MEDIDA_CM") or "")
        else:
            es_base = (fila.get("DESCRIPCION") or "").strip().upper().startswith("BASE")
            cm = numero(fila.get("TAMAÑO EN CM") or "")
        if not es_base or cm is None or int(cm) in medidas:
            continue
        precios = {n: numero(fila.get(n.upper()) or "") for n in NIVELES}
        if any(v is not None for v in precios.values()):
            medidas[int(cm)] = {"cm": int(cm), **{n: (round(v) if v is not None else None) for n, v in precios.items()}}

    lista = [medidas[cm] for cm in sorted(medidas)]
    if len(lista) < 5:
        sys.exit(f"Muy pocas medidas con precio ({len(lista)}): no piso el archivo. Revisá la hoja.")

    SALIDA.write_text(json.dumps({
        "actualizado": date.today().isoformat(),
        "mock": False,
        "medidas": lista,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: {len(lista)} medidas -> {SALIDA}")


if __name__ == "__main__":
    main()
