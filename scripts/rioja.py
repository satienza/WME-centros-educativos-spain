"""La Rioja -> La Rioja/centros_rioja.geojson

Coordenadas y direcciones: capa WFS "iderioja:centros_educativos" de IDERioja (ogc.larioja.org).
Trae un punto por sede, así que los CRA aparecen con cada escuela de sus pueblos.
Código postal y centros que faltan en la capa: Registro Estatal de Centros Docentes del Ministerio
(exportación Excel); los que faltan se geocodifican con CartoCiudad.
El buscador de larioja.org está detrás de Cloudflare y no se puede consultar desde un script.
"""
import json
import os
import re
import urllib.parse

from comun import Geocache, descargar, feature, guardar, registro_estatal, titulo

WFS = "https://ogc.larioja.org/wfs?" + urllib.parse.urlencode({
    "SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
    "TYPENAMES": "iderioja:centros_educativos", "OUTPUTFORMAT": "application/json",
    "SRSNAME": "EPSG:4326",  # ponytail: GeoServer redondea a 4 decimales (±5 m)
})
SALIDA = os.path.join(os.path.dirname(__file__), "..", "La Rioja", "centros_rioja.geojson")
# Sin tipo en la capa: universidades, academias, seminario, oficinas. Más servicios sin alumnos.
EXCLUIR = {None, "Servicios Centrales", "Equipo de Orientación Educativa y Psicopedagógica"}
PREFIJO = re.compile(r"((?:[A-Za-zÁÉÍÓÚ]+\.)+)\s*(.*)")


def nombre(txt):
    """'C.R.A. Las Cuatro Villas (Arrúbal)' -> 'CRA Las Cuatro Villas (Arrúbal)'."""
    m = PREFIJO.fullmatch(" ".join(txt.split()))
    return f"{m[1].replace('.', '').upper()} {m[2]}" if m else txt


def main():
    capa = json.loads(descargar(WFS))["features"]
    rcd = registro_estatal("12")
    features, en_capa, excluidos = [], set(), 0
    for c in capa:
        p = c["properties"]
        if p["Tipo"] in EXCLUIR or not p["Codigo"]:
            excluidos += 1
            continue
        codigo, loc = str(p["Codigo"]).zfill(8), p["Nucleo_urbano"]
        en_capa.add(codigo)
        r = rcd.get(codigo)
        num = str(p["Numero"] or p["Complemento"] or "").upper()
        lon, lat = c["geometry"]["coordinates"][:2]
        features.append(feature(
            codigo=codigo, nombre=nombre(p["Nombre"]),
            direccion=f'{p["Vial"]}, {num}' if num else p["Vial"],
            poblacion=loc, municipio=loc,  # ponytail: la capa solo trae el núcleo
            codigo_postal=r["CÓD POSTAL"] if r and r["LOCALIDAD"] == loc else "",  # otras sedes de un CRA: sin CP
            lat=lat, lon=lon, tipo_centro=p["Tipo"],
        ))

    geo, sin_coords, cache = {}, 0, Geocache("rioja")
    for codigo, r in rcd.items():
        if codigo in en_capa:
            continue
        nom, gen = titulo(r["DENOMINACIÓN ESPECÍFICA"]), r["DENOMINACIÓN GENÉRICA"]
        if not nom.lower().startswith(gen.split()[0].lower()):  # 'Escuela de Música Escuela de...'
            nom = f"{gen} {nom}"
        direc = titulo(r["DOMICILIO"].strip())
        g = cache.buscar(codigo, nom, direc, r["LOCALIDAD"], "La Rioja")
        if not g:
            sin_coords += 1
            continue
        lat, lon, metodo = g
        geo[metodo] = geo.get(metodo, 0) + 1
        features.append(feature(
            codigo=codigo, nombre=nom, direccion=direc,
            poblacion=r["LOCALIDAD"], municipio=r["LOCALIDAD"], codigo_postal=r["CÓD POSTAL"],
            lat=lat, lon=lon, tipo_centro=r["DENOMINACIÓN GENÉRICA"], geocodificado=metodo,
        ))
    cache.guardar()
    print(f"Excluidos de la capa: {excluidos}. Solo en el registro, geocodificados: {geo} "
          f"({cache.consultas} consultados ahora). Sin coordenadas: {sin_coords}")
    guardar(features, SALIDA, {"url": WFS, "actualizado": None})


if __name__ == "__main__":
    main()
