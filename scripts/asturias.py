"""Asturias -> Asturias/centros.geojson

Datos: Excel del directorio de educastur (sin coordenadas).
Coordenadas: capa "Centros Educativos" de SIG Asturias, cruzada por código de centro. Los que no
están se geocodifican con CartoCiudad y llevan la propiedad "geocodificado".
"""
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime

import xlrd  # el directorio se publica en .xls binario; la stdlib no lo lee

from comun import SSL_CTX, descargar, expandir_via, Geocache, feature, guardar

PAGINA = "https://www.educastur.es/directorio-de-centros"
SIG = ("https://sig.asturias.es/servicios/rest/services/Visor/Educacion/MapServer/0/query"
       "?where=1%3D1&outFields=codigo,tipo&outSR=4326&f=geojson")
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Asturias", "centros.geojson")
# Nombres que llegan con el tipo escrito entero -> misma abreviatura que el resto del fichero.
LARGOS = {
    "Escuela Infantil": "EEI", "Colegio Público": "CP", "Instituto de Educación Secundaria": "IES",
    "Centro de Educación de Personas Adultas": "CEPA", "Centro de Educación Infantil": "CEI",
    "Colegio de Educación Especial": "CEE", "Colegio Rural Agrupado": "CRA",
}
PREFIJO = re.compile(r"((?:[A-Za-zÁÉÍÓÚáéíóúÑñ]+\.\s?)+)\s*(.*)")


def excel():
    """URL del .xls enlazado en la página y su fecha 'ACTUALIZADO dd-mm-aaaa'."""
    html = descargar(PAGINA)
    url = urllib.parse.urljoin(PAGINA, re.search(r'href="([^"]+\.xls[^"]*)"', html)[1])
    fecha = re.search(r"ACTUALIZADO\s+(\d{2}-\d{2}-\d{4})", html)
    return url, fecha and datetime.strptime(fecha[1], "%d-%m-%Y").date().isoformat()


def nombre(txt):
    """'C.E.E. "Castiello de Bernueces"' -> 'CEE Castiello de Bernueces'; 'Col. "X"' -> 'Colegio X'."""
    txt = " ".join(txt.replace('"', "").split())
    for largo, abrev in LARGOS.items():
        if txt.startswith(largo + " "):
            return f"{abrev} {txt[len(largo) + 1:]}"
    m = PREFIJO.match(txt)
    if not m:
        return txt
    abrev = m[1].replace(".", "").replace(" ", "")
    return f'{"Colegio" if abrev == "Col" else abrev.upper()} {m[2]}'


def texto(v):
    """Celdas numéricas (código, CP) llegan como float."""
    return str(int(v)) if isinstance(v, float) else str(v).strip()


def main():
    url, actualizado = excel()
    req = urllib.request.Request(url, headers={"User-Agent": "WME-centros-educativos"})
    with urllib.request.urlopen(req, timeout=120, context=SSL_CTX) as r:
        hoja = xlrd.open_workbook(file_contents=r.read()).sheet_by_index(0)
    sig = {f["properties"]["codigo"]: f for f in json.loads(descargar(SIG))["features"]}

    cab = hoja.row_values(0)
    features, sin_coords, geo, cache = [], 0, {}, Geocache("asturias")
    for i in range(1, hoja.nrows):
        r = dict(zip(cab, hoja.row_values(i)))
        codigo = texto(r["CÓDIGO"])
        punto = sig.get(codigo)
        nom, direc, metodo = nombre(r["CENTRO"]), expandir_via(r["DOMICILIO"]), None
        if punto and punto["geometry"]:
            lon, lat = punto["geometry"]["coordinates"][:2]
        else:
            g = cache.buscar(codigo, nom, direc, texto(r["MUNICIPIO"]), "Asturias")
            if not g:
                sin_coords += 1
                continue
            lat, lon, metodo = g
            geo[metodo] = geo.get(metodo, 0) + 1
        features.append(feature(
            codigo=codigo,
            nombre=nom,
            direccion=direc,
            poblacion=texto(r["LOCALIDAD"]),
            municipio=texto(r["MUNICIPIO"]),
            codigo_postal=texto(r["C_POSTAL"]),
            lat=lat, lon=lon,
            tipo_centro=(punto and punto["properties"]["tipo"]) or texto(r["TIPO"]),
            geocodificado=metodo,
        ))
    cache.guardar()
    print(f"Geocodificados con CartoCiudad: {geo} ({cache.consultas} consultados ahora). Sin coordenadas: {sin_coords}")
    guardar(features, SALIDA, {"url": url, "actualizado": actualizado})


if __name__ == "__main__":
    main()
