"""Genera _site/ (index.html, los GeoJSON y un zip con todos) para GitHub Pages."""
import glob
import json
import os
import shutil
import zipfile
from datetime import date
from html import escape

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(RAIZ, "_site")
ZIP = "centros_educativos_espana.zip"
REPO = "https://github.com/satienza/WME-centros-educativos-spain"


def miles(n):
    return f"{n:,}".replace(",", ".")


def tamano(b):
    return f"{b / 1e6:.1f} MB".replace(".", ",") if b >= 1e6 else f"{b / 1e3:.0f} kB"


def main():
    shutil.rmtree(SITE, ignore_errors=True)
    os.makedirs(SITE)
    for f in ("icono.svg", "icono.png", "favicon.svg"):
        shutil.copy(os.path.join(RAIZ, f), SITE)
    filas, total = [], 0
    with zipfile.ZipFile(os.path.join(SITE, ZIP), "w", zipfile.ZIP_DEFLATED) as z:
        for ruta in sorted(glob.glob(os.path.join(RAIZ, "*", "centros_*.geojson"))):
            nombre = os.path.basename(ruta)
            with open(ruta, encoding="utf-8") as f:
                d = json.load(f)
            n = len(d["features"])
            total += n
            fecha = (d.get("fuente", {}).get("actualizado") or "—")[:10]
            shutil.copy(ruta, os.path.join(SITE, nombre))
            z.write(ruta, nombre)
            filas.append(
                f'<tr><th scope="row">{escape(os.path.basename(os.path.dirname(ruta)))}</th>'
                f'<td>{miles(n)}</td><td>{tamano(os.path.getsize(ruta))}</td><td>{fecha}</td>'
                f'<td><a href="{escape(nombre)}" download>GeoJSON</a></td></tr>')
    zip_tam = tamano(os.path.getsize(os.path.join(SITE, ZIP)))
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Centros educativos de España para WME</title>
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<style>
:root {{ color-scheme: light dark; --acento: #0b6bcb; }}
body {{ font: 16px/1.5 system-ui, sans-serif; max-width: 52rem; margin: 0 auto; padding: 1.5rem 1rem; }}
h1 {{ font-size: 1.6rem; margin-bottom: .25rem; }}
.todo {{ display: inline-block; margin: 1rem 0 1.5rem; padding: .75rem 1.25rem; border-radius: .5rem;
  background: var(--acento); color: #fff; font-weight: 600; text-decoration: none; }}
.todo:hover, .todo:focus-visible {{ filter: brightness(1.15); }}
.tabla {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: .5rem .6rem; border-bottom: 1px solid color-mix(in srgb, currentColor 20%, transparent); text-align: left; white-space: nowrap; }}
thead th {{ font-size: .85rem; text-transform: uppercase; letter-spacing: .03em; opacity: .75; }}
:is(td, th):nth-child(2), :is(td, th):nth-child(3) {{ text-align: right; font-variant-numeric: tabular-nums; }}
tbody th {{ font-weight: 500; }}
a {{ color: var(--acento); }}
@media (prefers-color-scheme: dark) {{ :root {{ --acento: #5aa9ff; }} .todo {{ color: #000; }} }}
footer {{ margin-top: 2rem; font-size: .9rem; opacity: .8; }}
</style>
</head>
<body>
<h1>Centros educativos de España para WME</h1>
<p>GeoJSON por comunidad autónoma para editar zonas escolares en Waze Map Editor.
Para cargarlos en WME es necesario el script <a href="https://greasyfork.org/en/scripts/8129-wme-geometries">WME Geometries</a>:
abrir el fichero con él y elegir <code>nombre</code> como propiedad de etiqueta.</p>
<a class="todo" href="{ZIP}" download>⬇ Descargar todo (.zip · {zip_tam} · {miles(total)} centros)</a>
<div class="tabla">
<table>
<thead><tr><th scope="col">Comunidad</th><th scope="col">Centros</th><th scope="col">Tamaño</th>
<th scope="col">Fuente actualizada</th><th scope="col"><span hidden>Descarga</span></th></tr></thead>
<tbody>
{chr(10).join(filas)}
</tbody>
</table>
</div>
<footer>Generado el {date.today().isoformat()} · Se actualiza cada lunes ·
Fuentes y formato: <a href="{REPO}#readme">README en GitHub</a></footer>
</body>
</html>
""")
    print(f"{SITE}: {len(filas)} ficheros, {total} centros, zip {zip_tam}")


if __name__ == "__main__":
    main()
