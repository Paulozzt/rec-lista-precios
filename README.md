# REC · Lista de precios

Web estática (sin build) con la lista de precios de bases. Hoy tiene **datos de prueba**.

- `index.html`: la página.
- `data/config.json`: textos, formas, combos y contacto (WhatsApp, tienda, Instagram). Se edita a mano.
- `data/precios.json`: precios por medida (unidad, x30, x50, x100). Lo genera el cronjob.
- `scripts/actualizar_precios.py` + `.github/workflows/actualizar-precios.yml`: todos los lunes baja la hoja "LISTA WEB" publicada como CSV y reescribe `precios.json`.

## Conectar con la planilla

1. Crear un Google Sheet aparte ("REC · Lista web"). **Nunca publicar la planilla de producción.**
2. En A1: `=QUERY(IMPORTRANGE("<link planilla producción>";"LISTAS!A:F");"select Col1, Col2, Col3 where Col2 is not null";1)` y dar "Permitir acceso".
3. Archivo → Compartir → Publicar en la web → esa hoja → CSV. Copiar el link.
4. En GitHub: Settings → Secrets → Actions → `SHEET_CSV_URL` = ese link.
5. Actions → "Actualizar precios" → Run workflow (para probar sin esperar al lunes).

## Probar local

Servir la carpeta (por ejemplo `python -m http.server`) y abrir `index.html`.
