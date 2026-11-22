"""Cataluña -> Cataluña/centros_cataluna.geojson

Fuente: "Directori de centres docents anual" de Transparència Catalunya (API Socrata), con
coordenadas oficiales. Es el mismo directorio que muestra mapaescolar.gencat.cat en cada ficha.
Se toma el curso más reciente publicado.
"""
import json
import os
import re
import urllib.parse
from datetime import datetime, timezone

from comun import VIAS_CA, descargar, expandir_via, feature, guardar

DATASET = "kvmv-ahh4"
API = f"https://analisi.transparenciacatalunya.cat/resource/{DATASET}.json"
META = f"https://analisi.transparenciacatalunya.cat/api/views/{DATASET}.json"
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Cataluña", "centros_cataluna.geojson")

# Aulas hospitalarias y unidades de salud mental: no son edificios escolares.
EXCLUIR = ("HDA ", "AH ", "URPIJ ", "UTCA ")

# En Cataluña el tipo forma parte del nombre oficial ("Institut ...", "Llar d'infants ...");
# se deduce de cómo empieza. Orden: de más a menos específico.
TIPOS = [
    ("Institut Escola", "Instituto Escuela (Infantil, Primaria y ESO)"),
    ("Institut", "Instituto"),
    ("Escola Bressol", "Escuela Infantil (0-3 años)"),
    ("EB ", "Escuela Infantil (0-3 años)"),
    ("Llar d'infants", "Escuela Infantil (0-3 años)"),
    ("Llar inf.", "Escuela Infantil (0-3 años)"),
    ("LLI ", "Escuela Infantil (0-3 años)"),
    ("Esc. de Música", "Escuela de Música"),
    ("Esc. Mús.", "Escuela de Música"),
    ("Escola de Música", "Escuela de Música"),
    ("Esc. de Dansa", "Escuela de Danza"),
    ("Escola d'Art", "Escuela de Arte"),
    ("EA ", "Escuela de Arte"),
    ("Escola Oficial d'Idiomes", "Escuela Oficial de Idiomas"),
    ("EOI ", "Escuela Oficial de Idiomas"),
    ("CFA ", "Centro de Formación de Adultos"),
    ("Centre de Formació d'Adults", "Centro de Formación de Adultos"),
    ("CEE ", "Centro de Educación Especial"),
    ("Cons. de", "Conservatorio"),
    ("Conservatori", "Conservatorio"),
]


def tipo(nombre, naturalesa):
    for prefijo, t in TIPOS:
        if nombre.startswith(prefijo):
            return t
    if nombre.startswith("Escola") and naturalesa == "Públic":
        return "Escuela (Infantil y Primaria)"
    return "Centro público" if naturalesa == "Públic" else "Centro privado"


def direccion(txt):
    """'c. Icària, 80' -> 'Carrer Icària, 80'. 'p.' se deja: la fuente lo usa tanto para plaça como para passeig."""
    d = expandir_via(txt, VIAS_CA)
    return d[:1].upper() + d[1:]


def consulta(**params):
    return json.loads(descargar(API + "?" + urllib.parse.urlencode(params)))


def main():
    curs = consulta(**{"$select": "max(curs) AS curs"})[0]["curs"]
    filas = consulta(**{"$where": f"curs='{curs}'", "$limit": "50000", "$order": "codi_centre"})
    meta = json.loads(descargar(META))
    actualizado = datetime.fromtimestamp(meta["rowsUpdatedAt"], timezone.utc).date().isoformat()

    features, sin_coords, excluidos = [], 0, 0
    for r in filas:
        nombre = " ".join(r.get("denominaci_completa", "").split())
        if nombre.startswith(EXCLUIR):
            excluidos += 1
            continue
        try:
            lat, lon = float(r["coordenades_geo_y"]), float(r["coordenades_geo_x"])
        except (KeyError, ValueError):
            sin_coords += 1
            continue
        if not (40.4 < lat < 42.95 and 0.1 < lon < 3.4):
            sin_coords += 1
            continue
        features.append(feature(
            codigo=r["codi_centre"],
            nombre=nombre,
            direccion=direccion(r.get("adre_a", "")),
            poblacion=r.get("nom_localitat", ""),
            municipio=r.get("nom_municipi", ""),
            codigo_postal=r.get("codi_postal", ""),
            lat=lat, lon=lon,
            tipo_centro=tipo(nombre, r.get("nom_naturalesa")),
            curso=curs,
        ))
    print(f"Curso {curs}. Unidades hospitalarias excluidas: {excluidos}. Sin coordenadas válidas: {sin_coords}")
    guardar(features, SALIDA, {"url": f"https://analisi.transparenciacatalunya.cat/d/{DATASET}",
                               "actualizado": actualizado})


if __name__ == "__main__":
    main()
