"""Comunitat Valenciana -> Comunidad Valenciana/centros.geojson

Fuente: "Centros docentes de la Comunitat Valenciana" en dadesobertes.gva.es (CKAN), con
coordenadas oficiales. Es el registro que consulta la Guía de centros docentes de la Conselleria.
"""
import csv
import io
import json
import os
import re

from comun import descargar, feature, guardar, titulo

PAQUETE = "https://dadesobertes.gva.es/api/3/action/package_show?id=edu-centros"
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Comunidad Valenciana", "centros.geojson")
# Nombres que solo dicen el tipo ("EI 1er Cicle Municipal"): se les añade la localidad.
GENERICO = re.compile(r"(MUNICIPAL|DE MÚSICA|DE DANSA|DE DANZA)$")


def localidad(txt):
    """"ALFÀS DEL PI (L')" -> "L'Alfàs del Pi"; 'CAMPELLO (EL)' -> 'El Campello'."""
    m = re.match(r"(.*) \((.+)\)$", txt)
    if m:
        art = m[2].strip()
        txt = f"{art}{'' if art.endswith(chr(39)) else ' '}{m[1]}"
    return titulo(txt, catalan=True)


def main():
    recurso = json.loads(descargar(PAQUETE))["result"]["resources"][0]
    filas = csv.DictReader(io.StringIO(descargar(recurso["url"])), delimiter=";")
    features = []
    for r in filas:
        loc = localidad(r["localidad"])
        nom = titulo(r["denominacion"], catalan=True)
        if GENERICO.search(r["denominacion"]):
            nom = f"{nom} {loc}"
        calle = titulo(f'{r["tipo_via"]} {r["direccion"]}'.strip(), catalan=True)
        num = r["numero"].strip().upper()
        features.append(feature(
            codigo=r["codigo"], nombre=nom, direccion=f"{calle}, {num}" if num else calle,
            poblacion=loc, municipio=loc,  # ponytail: la fuente solo trae localidad
            codigo_postal=r["codigo_postal"],
            lat=float(r["latitud"]), lon=float(r["longitud"]),
            tipo_centro=titulo(r["denominacion_generica_es"]),
        ))
    guardar(features, SALIDA, {"url": recurso["url"], "actualizado": recurso.get("last_modified")})


if __name__ == "__main__":
    main()
