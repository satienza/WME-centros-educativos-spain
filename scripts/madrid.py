"""Comunidad de Madrid -> Comunidad de Madrid/centros.geojson

Fuente: capa WFS "WPAD_V_CENTROS_GIS" de la IDEM (geoservidor de la Comunidad). Es la que pinta
el mapa del buscador de centros (gestiona.comunidad.madrid/wpad_pub) y contiene los mismos
centros que su listado, con coordenadas. Los pocos sin coordenadas se geocodifican con CartoCiudad.
"""
import json
import os
import re
import urllib.parse

from comun import VIAS, Geocache, descargar, expandir_via, feature, guardar, titulo

WFS = "https://idem.comunidad.madrid/geosrvg/wfs?" + urllib.parse.urlencode({
    "service": "WFS", "version": "2.0.0", "request": "GetFeature",
    "typeNames": "WPAD_V_CENTROS_GIS", "outputFormat": "application/json",
    # ponytail: GeoServer redondea a 4 decimales (±5 m); EPSG:25830 + conversión UTM si hace falta más
    "srsName": "EPSG:4326",
})
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Comunidad de Madrid", "centros.geojson")

# Servicios sin edificio escolar propio: orientación, formación del profesorado, aulas
# hospitalarias, zonas de casas de niños, oficinas, centros en el extranjero, universidades.
EXCLUIR = {"A. HOSP.", "A. HOSP. PRIV.", "C. DOC. EN EXTRANJ.", "CTIF", "EOEP ATEN-TEMPR",
           "EOEP ESPECÍFICO", "EOEP GENERAL", "EST ADMI", "ZNAS.CN.", "ISMIE", "CFII", "CREACIM",
           "UNIVERSIDAD"}
# La Comunidad usa "CP INF-PRI" en el registro; en el nombre se usa la sigla habitual.
ABREV = {"CP INF-PRI": "CEIP", "CP INF-PRI-SEC": "CEIPSO", "CP EE": "CEE"}
VIAS_MAD = {**VIAS, "CMNO": "Camino", "SECT": "Sector", "TRVA": "Travesía", "GTA": "Glorieta",
            "PSAJE": "Pasaje", "URB": "Urbanización", "BULEV": "Bulevar", "CLLON": "Callejón",
            "POLIG": "Polígono", "CUSTA": "Cuesta", "VREDA": "Vereda", "PQUE": "Parque",
            "DISEM": "Diseminado", "PARCE": "Parcela", "PRAJE": "Paraje", "COL": "Colonia",
            "CRA": "Carrera"}
NUMERO = re.compile(r"\s+(\d+\w?(?:-\d+\w?)?|s/n)$", re.I)


def direccion(txt):
    """'Avda de la Paz 5' -> 'Avenida de la Paz, 5'; 'Calle Mayor s/n' -> 'Calle Mayor, S/N'."""
    d = expandir_via(txt, VIAS_MAD)
    return NUMERO.sub(lambda m: ", " + m[1].upper(), d)


def municipio(txt):
    """'Rozas de Madrid, Las' -> 'Las Rozas de Madrid'."""
    nombre, _, art = txt.partition(", ")
    return f"{art} {nombre}" if art else txt


def main():
    centros = json.loads(descargar(WFS))["features"]
    features, excluidos, sin_coords, geo, cache = [], 0, 0, {}, Geocache("madrid")
    for c in centros:
        p = c["properties"]
        gen = p["DS_GEN"]
        if gen in EXCLUIR:
            excluidos += 1
            continue
        nom = f'{ABREV.get(gen, gen)} {titulo(p["DS_CENTRO"][len(gen):].strip())}'
        direc, muni, metodo = direccion(p["DOMICILIO"] or ""), municipio(p["DSMUNI"]), None
        if c["geometry"]:
            lon, lat = c["geometry"]["coordinates"]
        else:
            g = cache.buscar(p["CD_CENTRO"], nom, direc, muni, "Madrid")
            if not g:
                sin_coords += 1
                continue
            lat, lon, metodo = g
            geo[metodo] = geo.get(metodo, 0) + 1
        features.append(feature(
            codigo=p["CD_CENTRO"], nombre=nom, direccion=direc, poblacion=muni, municipio=muni,
            codigo_postal=p["CDPOSTAL"], lat=lat, lon=lon,
            tipo_centro=titulo(p["DSEXTEND"]), geocodificado=metodo,
        ))
    cache.guardar()
    print(f"Servicios excluidos: {excluidos}. Geocodificados con CartoCiudad: {geo} "
          f"({cache.consultas} consultados ahora). Sin coordenadas: {sin_coords}")
    guardar(features, SALIDA, {"url": WFS, "actualizado": None})


if __name__ == "__main__":
    main()
