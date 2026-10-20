"""Baja la hoja "LISTA WEB" publicada como CSV y escribe data/precios.json.

La hoja tiene que tener estas columnas, con estos títulos (como en LISTAS):
    DESCRIPCION | TAMAÑO EN CM | MINORISTA | BRONCE | PLATA | ORO
BRONCE/PLATA/ORO son opcionales: se leen de las filas "BASE" (precio por base).

Se toman las filas cuya DESCRIPCION empieza con:
    "BASE"        -> precio por unidad
    "PACK X 30"   -> pack de 30
    "PACK X 50"   -> pack de 50
    "PACK X 100"  -> pack de 100
Como todas las formas tienen el mismo precio por medida, alcanza con la primera
fila de cada medida. Las filas sin medida (notas internas) o con medidas tipo
"15 X 22" (tablas) se ignoran. Si una medida no tiene pack, queda en null.

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
COLUMNA_PRECIO = os.environ.get("COLUMNA_PRECIO", "MINORISTA")
TIPOS = [("PACK X 100", "x100"), ("PACK X 50", "x50"), ("PACK X 30", "x30"), ("BASE", "unidad")]
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
        pass
    try:
        return float(texto.replace(".", "").replace(",", "."))
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
        desc = (fila.get("DESCRIPCION") or "").strip().upper()
        cm = numero(fila.get("TAMAÑO EN CM") or "")
        precio = numero(fila.get(COLUMNA_PRECIO.upper()) or "")
        if not desc or cm is None or precio is None:
            continue
        clave = next((k for prefijo, k in TIPOS if desc.startswith(prefijo)), None)
        if not clave:
            continue
        m = medidas.setdefault(int(cm), {"cm": int(cm)})
        m.setdefault(clave, round(precio))
        if clave == "unidad":  # precio por base en cada nivel mayorista
            for nivel in NIVELES:
                valor = numero(fila.get(nivel.upper()) or "")
                if valor is not None:
                    m.setdefault(nivel, round(valor))

    # Toda medida con precio por unidad entra; los packs que no existan quedan en null ("Consultar").
    completas = [{"cm": m["cm"], **{k: m.get(k) for _, k in reversed(TIPOS)}, **{n: m.get(n) for n in NIVELES}}
                 for m in sorted(medidas.values(), key=lambda m: m["cm"]) if "unidad" in m]
    if len(completas) < 5:
        sys.exit(f"Muy pocas medidas con precio ({len(completas)}): no piso el archivo. Revisá la hoja.")

    SALIDA.write_text(json.dumps({
        "actualizado": date.today().isoformat(),
        "mock": False,
        "medidas": completas,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: {len(completas)} medidas -> {SALIDA}")


if __name__ == "__main__":
    main()
