"""Extremadura -> Extremadura/centros.geojson

Datos: Registro Estatal de Centros Docentes del Ministerio (exportación Excel del buscador, sin
coordenadas). La Junta no publica un directorio con código ni dirección.
Coordenadas: capas WFS de centros de la IDEEX (cartografía de 2015) cruzadas por código; los que no
están se geocodifican con CartoCiudad y llevan la propiedad "geocodificado".
"""
import os
import re
import xml.etree.ElementTree as ET

from comun import (RCD, Geocache, descargar, feature, guardar, normalizar_direccion as direccion,
                   registro_estatal, titulo)

IDEEX = ("https://mapas.ideex.es/CICTEX/centrosEducativos?SERVICE=WFS&VERSION=1.1.0"
         "&REQUEST=GetFeature&SRSNAME=EPSG:4326&TYPENAME=ms:CICTEX_CENTROS_EDUCATIVOS_")
CAPAS = ("PUBLICO_CONCERTADO", "ARTE_IDIOMA_ADULTOS", "RECURSOS")
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Extremadura", "centros.geojson")
NS = {"gml": "http://www.opengis.net/gml", "ms": "http://mapserver.gis.umn.edu/mapserver"}

ABREV = {
    "Colegio de Educación Infantil y Primaria": "CEIP", "Colegio de Educación Primaria": "CEP",
    "Escuela Infantil": "EEI", "Escuela Municipal de Educación Infantil": "EEI",
    "Instituto de Educación Secundaria": "IES", "Sección de Instituto de Educación Secundaria": "SIES",
    "Instituto de Educación Secundaria Obligatoria": "IESO", "Centro de Educación Especial": "CEE",
    "Centro Público de Educación de Personas Adultas": "CEPA", "Aula de Educación de Adultos": "AEPA",
    "Escuela Oficial de Idiomas": "EOI", "Colegio Rural Agrupado": "CRA",
    "Conservatorio Profesional de Música": "CPM", "Centro Público Integrado de Formación Profesional": "CIFP",
}

def abreviatura(generica):
    if generica in ABREV:
        return ABREV[generica]
    return "CPR" if generica.startswith("Centro Privado") else generica


def nombre(generica, especifica):
    """('Instituto de Educación Secundaria', 'IES TIERRA DE BARROS') -> 'IES Tierra de Barros'."""
    abrev = abreviatura(generica)
    esp = re.sub(r"\.(?=[A-ZÁÉÍÓÚÑ])", ". ", especifica.strip())  # 'NTRA.SRA.' -> 'NTRA. SRA.'
    esp = re.sub(r"^" + r"\.?\s?".join(abrev) + r"\.?\s+", "", esp, flags=re.I)  # 'C.R.A. X' -> 'X'
    return f"{abrev} {titulo(esp, inicio=False)}"


def coordenadas_ideex():
    puntos = {}
    for capa in CAPAS:
        raiz = ET.fromstring(descargar(IDEEX + capa).encode("utf-8"))
        for f in raiz.iter(f"{{{NS['ms']}}}CICTEX_CENTROS_EDUCATIVOS_{capa}"):
            pos, cod = f.find(".//gml:pos", NS), f.find("ms:CODIGO", NS)
            if pos is not None and cod is not None and cod.text:
                lat, lon = map(float, pos.text.split())  # WFS 1.1 + EPSG:4326 -> lat lon
                puntos[cod.text.strip()] = (lat, lon)
    return puntos


def main():
    filas = registro_estatal("10").values()
    ideex = coordenadas_ideex()

    features, sin_coords, geo, cache = [], 0, {}, Geocache("extremadura")
    for r in filas:
        codigo, loc = r["CÓDIGO"], r["LOCALIDAD"].strip()
        nom, direc, metodo = nombre(r["DENOMINACIÓN GENÉRICA"], r["DENOMINACIÓN ESPECÍFICA"]), direccion(r["DOMICILIO"]), None
        if codigo in ideex:
            lat, lon = ideex[codigo]
        else:
            g = cache.buscar(codigo, nom, direc, loc, r["PROVINCIA"])
            if not g:
                sin_coords += 1
                continue
            lat, lon, metodo = g
            geo[metodo] = geo.get(metodo, 0) + 1
        features.append(feature(
            codigo=codigo, nombre=nom, direccion=direc,
            poblacion=loc, municipio=loc,  # ponytail: el registro solo trae localidad
            codigo_postal=r["CÓD POSTAL"], lat=lat, lon=lon,
            tipo_centro=r["DENOMINACIÓN GENÉRICA"], geocodificado=metodo,
        ))
    cache.guardar()
    print(f"Coordenadas IDEEX: {len(features) - sum(geo.values())}. Geocodificados con CartoCiudad: "
          f"{geo} ({cache.consultas} consultados ahora). Sin coordenadas: {sin_coords}")
    guardar(features, SALIDA, {"url": RCD, "actualizado": None})


if __name__ == "__main__":
    main()
