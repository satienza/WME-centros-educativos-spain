"""Navarra -> Navarra/centros.geojson

Fuente: dataset "Centros educativos" de datosabiertos.navarra.es (CKAN), un CSV por curso con
coordenadas; se toma el curso más reciente. El tipo de centro y los pocos centros que faltan salen
del Registro Estatal de Centros Docentes (los que faltan se geocodifican con CartoCiudad).
"""
import csv
import io
import json
import os
import re

from comun import (Geocache, descargar, feature, guardar, normalizar_direccion, registro_estatal,
                   titulo, utm_a_latlon)

PAQUETE = "https://datosabiertos.navarra.es/api/3/action/package_show?id=centros-educativos"
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Navarra", "centros.geojson")
# Servicios sin alumnos: centros de apoyo al profesorado, unidades de orientación, recursos.
EXCLUIR = ("CAP ", "ORG ", "CREENA", "CRikasNOVA", "EIBZ", "EPA Euskarabidea")
# Primer token del "Nombre corto" -> sigla del nombre (el resto se usa tal cual: CPEIP, IES, EI...).
TIPOS = ("Instituto", "Colegio", "Escuela", "Centro", "Conservatorio", "Ikastola")
SIGLAS = {"C.Con.": "Colegio", "C.": "Colegio", "Cons.": "Conservatorio", "Ik": "Ikastola"}


def sigla(corto):
    tokens = corto.split()
    if tokens[0] == "Esc.":
        return "Escuela de Música" if tokens[1:2] == ["Mús."] else "Escuela"
    return SIGLAS.get(tokens[0], tokens[0])


def nombre(corto, largo):
    """('CPEIP Larraga S. Miguel HLHIP', 'San Miguel de Larraga') -> 'CPEIP San Miguel de Larraga'."""
    s = sigla(corto)
    if s.lower() in largo.lower() or largo.startswith(TIPOS):  # el nombre ya dice el tipo
        return largo
    return f"{s} {largo}"


def localidad(txt):
    """'Elizondo (Baztan)' -> ('Elizondo', 'Baztan'); 'Pamplona / Iruña' -> ambos iguales."""
    m = re.fullmatch(r"(.+?) \((.+)\)", txt.strip())
    return (m[1], m[2]) if m else (txt.strip(), txt.strip())


def main():
    recursos = json.loads(descargar(PAQUETE))["result"]["resources"]
    recurso = max(recursos, key=lambda r: r["name"])  # "Centros educativos para el curso 2026-2027"
    curso = re.search(r"\d{4}-\d{4}", recurso["name"])[0].replace("-", "/")
    filas = csv.DictReader(io.StringIO(descargar(recurso["url"])))
    rcd = registro_estatal("15")

    features, vistos, excluidos, geo, sin_coords = [], set(), 0, {}, 0
    cache = Geocache("navarra")

    def punto(codigo, nom, direc, muni):
        nonlocal sin_coords
        g = cache.buscar(codigo, nom, direc, muni, "Navarra")
        if not g:
            sin_coords += 1
            return None
        geo[g[2]] = geo.get(g[2], 0) + 1
        return g

    for r in filas:
        codigo, corto = r["Código"], r["Nombre corto"]
        if corto.startswith(EXCLUIR) or not codigo or (codigo, r["Dirección"]) in vistos:
            excluidos += 1  # las filas "(EI1)" repiten el mismo edificio con el primer ciclo de infantil
            continue
        vistos.add((codigo, r["Dirección"]))
        loc, muni = localidad(r["Localidad"])
        nom = nombre(corto, r["Nombre"].strip())
        if r["Latitud (Google Maps)"]:
            p = float(r["Latitud (Google Maps)"]), float(r["Longitud (Google Maps)"]), None
        else:  # algunas filas solo traen la UTM de SITNA (ETRS89 huso 30)
            p = *utm_a_latlon(float(r["Coordenada X (SITNA)"]), float(r["Coordenada Y (SITNA)"])), None
        if not p:
            continue
        reg = rcd.get(codigo)
        features.append(feature(
            codigo=codigo, nombre=nom, direccion=r["Dirección"], poblacion=loc, municipio=muni,
            codigo_postal=r["CP"], lat=p[0], lon=p[1],
            tipo_centro=reg["DENOMINACIÓN GENÉRICA"] if reg else f'Centro {r["Naturaleza"].lower()}',
            curso=curso, geocodificado=p[2],
        ))

    en_csv = {c for c, _ in vistos}
    for codigo, reg in rcd.items():
        if codigo in en_csv:
            continue
        loc = reg["LOCALIDAD"].strip()
        nom = titulo(f'{reg["DENOMINACIÓN GENÉRICA"]} {reg["DENOMINACIÓN ESPECÍFICA"]}')
        direc = normalizar_direccion(reg["DOMICILIO"])
        p = punto(codigo, nom, direc, loc)
        if p:
            features.append(feature(
                codigo=codigo, nombre=nom, direccion=direc, poblacion=loc, municipio=loc,
                codigo_postal=reg["CÓD POSTAL"], lat=p[0], lon=p[1],
                tipo_centro=reg["DENOMINACIÓN GENÉRICA"], geocodificado=p[2],
            ))
    cache.guardar()
    print(f"Curso {curso}. Excluidos/duplicados: {excluidos}. Geocodificados con CartoCiudad: {geo} "
          f"({cache.consultas} consultados ahora). Sin coordenadas: {sin_coords}")
    guardar(features, SALIDA, {"url": recurso["url"], "actualizado": recurso.get("last_modified")})


if __name__ == "__main__":
    main()
