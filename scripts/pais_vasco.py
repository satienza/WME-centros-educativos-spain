"""País Vasco -> País Vasco/centros.geojson

Fuente: "Centros docentes no universitarios de Euskadi" (opendata.euskadi.eus), CSV mensual con
coordenadas UTM (ETRS89 huso 30). Los pocos centros sin coordenadas se geocodifican con CartoCiudad.
El registro estatal del Ministerio no sirve de complemento: usa otros códigos para estos centros.
"""
import csv
import io
import os
import re
import urllib.request
from email.utils import parsedate_to_datetime

from comun import (SSL_CTX, Geocache, feature, guardar, normalizar_direccion, titulo,
                   utm_a_latlon)

CSV = ("https://opendata.euskadi.eus/contenidos/ds_localizaciones/centros_docentes_no_universit/"
       "es_euskadi/adjuntos/dirgennouniv.csv")
SALIDA = os.path.join(os.path.dirname(__file__), "..", "País Vasco", "centros.geojson")
TIPOS = {
    "CEIP": "Colegio de Educación Infantil y Primaria", "EIC": "Escuela Infantil (Consorcio Haurreskolak)",
    "CPEIPS": "Centro Privado de Educación Infantil, Primaria y Secundaria",
    "IES": "Instituto de Educación Secundaria", "CPES": "Centro Privado de Educación Secundaria",
    "EIPR": "Escuela Infantil Privada", "EMPU": "Escuela de Música Pública",
    "CIFP": "Centro Integrado de Formación Profesional", "EMPR": "Escuela de Música Privada",
    "CEPA": "Centro de Educación de Personas Adultas",
    "CPIFP": "Centro Privado Integrado de Formación Profesional",
    "CPEIP": "Centro Privado de Educación Infantil y Primaria", "EIMU": "Escuela Infantil Municipal",
    "IMFPB": "Instituto Municipal de Formación Profesional Básica", "CPI": "Centro Público Integrado",
    "CPFPB": "Centro Privado de Formación Profesional Básica", "EOI": "Escuela Oficial de Idiomas",
    "CPEI": "Centro Privado de Educación Infantil", "CPEE": "Centro Privado de Educación Especial",
    "CPM": "Conservatorio Profesional de Música", "CAED": "Centro Autorizado de Enseñanzas Deportivas",
    "CAEM": "Centro Autorizado Elemental de Música", "CPE": "Centro Privado Extranjero",
    "CAPM": "Centro Autorizado Profesional de Música",
    "CPEPS": "Centro Privado de Educación Primaria y Secundaria", "EEI": "Escuela de Educación Infantil",
    "CEE": "Centro de Educación Especial", "EASD": "Escuela de Arte y Superior de Diseño",
    "IFP": "Instituto de Formación Profesional", "CPD": "Conservatorio Profesional de Danza",
    "CASM": "Centro Autorizado Superior de Música",
    "CAAPD": "Centro Autorizado de Artes Plásticas y Diseño",
    "CPED": "Centro Privado de Enseñanzas Deportivas",
    "CPEPA": "Centro Privado de Educación de Personas Adultas",
    "CPEP": "Centro Privado de Educación Primaria", "CASDI": "Centro Autorizado Superior de Diseño",
}


def direccion(txt):
    """'SAN JOSÉ Z/G 98 P.K.' -> 'San José, S/N 98 P.K.'; 'Z/G' (zenbaki gabe) = S/N."""
    return normalizar_direccion(re.sub(r"\bZ/G\b", "S/N", txt or ""))


def main():
    req = urllib.request.Request(CSV, headers={"User-Agent": "WME-centros-educativos"})
    with urllib.request.urlopen(req, timeout=120, context=SSL_CTX) as r:
        texto = r.read().decode("latin-1")
        modificado = r.headers.get("Last-Modified")
    actualizado = modificado and parsedate_to_datetime(modificado).date().isoformat()

    features, excluidos, geo, sin_coords = [], 0, {}, 0
    cache = Geocache("pais_vasco")
    for r in csv.DictReader(io.StringIO(texto), delimiter=";"):
        sigla = r["DGENRC"].strip()
        if not sigla:  # centros a distancia / virtuales, sin edificio escolar
            excluidos += 1
            continue
        nom, direc, muni = f'{sigla} {titulo(r["NOM"], inicio=False)}', direccion(r["DOMI"]), titulo(r["DMUNIC"])
        lat, lon = utm_a_latlon(float(r["COOR_X"] or 0), float(r["COOR_Y"] or 0))
        metodo = None
        if not (42.4 < lat < 43.5 and -3.5 < lon < -1.7):  # algunas filas vienen con 0,0
            g = cache.buscar(r["CCEN"], nom, direc, muni, titulo(r["DTERRC"]))
            if not g:
                sin_coords += 1
                continue
            lat, lon, metodo = g
            geo[metodo] = geo.get(metodo, 0) + 1
        features.append(feature(
            codigo=r["CCEN"], nombre=nom, direccion=direc, poblacion=muni, municipio=muni,
            codigo_postal=r["CPOS"], lat=lat, lon=lon, tipo_centro=TIPOS.get(sigla, sigla),
            geocodificado=metodo,
        ))
    cache.guardar()
    print(f"Excluidos: {excluidos}. Geocodificados con CartoCiudad: {geo} "
          f"({cache.consultas} consultados ahora). Sin coordenadas: {sin_coords}")
    guardar(features, SALIDA, {"url": CSV, "actualizado": actualizado})


if __name__ == "__main__":
    main()
