"""Aragón -> Aragón/centros.geojson (centrosdocentes.catedu.es, botón "Exportar" sin filtros)"""
import csv
import io
import os
import re
import urllib.parse
import urllib.request

from comun import SSL_CTX, descargar, expandir_via, feature, guardar, titulo

URL = "https://centrosdocentes.catedu.es/ee/php/export/export_centros.php"
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Aragón", "centros.geojson")

# Las abreviaturas que muestra la web (C.E.I.P., C.P.E.P.A., E.E.O.I...) son las iniciales de las
# palabras con mayúscula del tipo; el CSV solo trae el tipo completo. Excepciones:
SIGLAS = {"Escuela Superior de Conservación y Restauración de Bienes Culturales": "ESCR"}


def siglas(tipo):
    return SIGLAS.get(tipo) or "".join(p[0] for p in re.findall(r"\w+", tipo) if p[0].isupper())


class _SinRedireccion(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


_opener = urllib.request.build_opener(_SinRedireccion, urllib.request.HTTPSHandler(context=SSL_CTX))


def coordenadas(emaps):
    """(lat, lon) del enlace de Google Maps; los cortos (maps.app.goo.gl) se resuelven leyendo
    la redirección: '!3d<lat>!4d<lon>' (punto del sitio), '/search/<lat>,+<lon>' o '/@<lat>,<lon>,' (vista)."""
    if "maps.app.goo.gl" in emaps:
        try:
            _opener.open(emaps, timeout=30)
            return None
        except urllib.error.HTTPError as e:
            emaps = urllib.parse.unquote(e.headers.get("Location") or "")
        except OSError:
            return None
    m = (re.search(r"!3d(-?[\d.]+)!4d(-?[\d.]+)", emaps) or re.search(r"(?:[?&]q=|/search/)(-?[\d.]+),\s*\+?(-?[\d.]+)", emaps)
         or re.search(r"/@(-?[\d.]+),(-?[\d.]+)", emaps))
    return (float(m[1]), float(m[2])) if m else None


def main():
    features, sin_coords = [], 0
    for r in csv.DictReader(io.StringIO(descargar(URL, "utf-8-sig")), delimiter=";"):
        coords = coordenadas(r["emaps"].strip())
        if not coords or not (39.8 < coords[0] < 43 and -2.3 < coords[1] < 0.9):
            sin_coords += 1
            continue
        tipo = r["tipo_centro"].strip()
        features.append(feature(
            codigo=r["codcentro"],
            nombre=f'{siglas(tipo)} {titulo(r["nombre"], inicio=False)}',
            direccion=titulo(expandir_via(r["direccion"])),
            poblacion=r["localidad"].strip(),
            municipio=titulo(r["municipio"]),
            codigo_postal=r["cod_postal"],
            lat=coords[0], lon=coords[1],
            tipo_centro=tipo,
        ))
    print(f"Sin coordenadas válidas: {sin_coords}")
    # La fuente no publica fecha de actualización.
    guardar(features, SALIDA, {"url": URL})


if __name__ == "__main__":
    main()
