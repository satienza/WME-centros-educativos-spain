"""Región de Murcia -> Región de Murcia/centros_murcia.geojson

Fuente: "Sedes de los Centros Educativos de la Región de Murcia" (datosabiertos.regiondemurcia.es,
CKAN), que apunta a la API del Mapa Escolar de MurciaEduca, con coordenadas.
La API no incluye unos 100 centros del Registro Estatal de Centros Docentes (sobre todo escuelas
infantiles privadas y municipales): se añaden del registro y se geocodifican con CartoCiudad.
"""
import json
import os
import re

from comun import (_norm, Geocache, descargar, feature, guardar, normalizar_direccion, registro_estatal,
                   titulo)

PAQUETE = ("https://datosabiertos.regiondemurcia.es/api/3/action/package_show"
           "?id=sedes-de-los-centros-educativos-de-la-region-de-murcia")
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Región de Murcia", "centros_murcia.geojson")
EXCLUIR = {"AHOS"}  # aulas hospitalarias
ABREV = {"CE INF-PRI": "CEIP", "CP PRI": "CEP", "EXT.DE E.O.I.": "Extensión EOI", "C.Prv.": "CPR"}
GENERICAS = {  # registro del Ministerio -> sigla de la API
    "Centro Privado de Educación Infantil": "CPR INF", "Escuela Municipal de Educación Infantil": "EMEI",
    "Escuela Infantil": "EEI", "Colegio de Educación Infantil y Primaria": "CEIP",
}


def sigla(corta):
    if not corta:
        return ""
    return ABREV.get(corta, corta if " " in corta else corta.replace(".", ""))  # 'I.E.S.O.' -> 'IESO'


def nombre(abrev, txt):
    """('IES', 'IES JOSÉ LUIS MARTÍNEZ') -> 'IES José Luis Martínez' (sin repetir la sigla)."""
    if abrev:
        txt = re.sub(rf"^{re.escape(abrev)}\s+", "", txt.strip(), flags=re.I)
    txt = titulo(txt, inicio=not abrev)
    return f"{abrev} {txt}" if abrev else txt


def localidad(txt):
    """'ARBOLEJA (LA)' -> 'La Arboleja'; 'PALMAR (EL) O LUGAR DE DON JUAN' -> 'El Palmar o Lugar de Don Juan'."""
    m = re.match(r"(.*?)\s*\((EL|LA|LOS|LAS|LUGAR DE)\)(.*)", txt.strip(), re.I)
    return titulo(f"{m[2]} {m[1]}{m[3]}" if m else txt)


def main():
    recurso = json.loads(descargar(PAQUETE))["result"]["resources"][0]
    sedes = json.loads(descargar(recurso["url"]))
    rcd = registro_estatal("14")
    # El registro solo trae la localidad (a menudo una pedanía); la API da su municipio.
    municipio_de = {_norm(s["loccen"]): titulo(s["muncen"]) for s in sedes}

    features, vistos, excluidos, geo, sin_coords = [], set(), 0, {}, 0
    cache = Geocache("murcia")

    def anadir(codigo, nom, direc, loc, muni, cp, tipo, punto):
        nonlocal sin_coords
        metodo = None
        if not punto:
            g = cache.buscar(codigo, nom, direc, muni, "Murcia")
            if not g:
                sin_coords += 1
                return
            *punto, metodo = g
            geo[metodo] = geo.get(metodo, 0) + 1
        features.append(feature(codigo=codigo, nombre=nom, direccion=direc, poblacion=loc,
                                municipio=muni, codigo_postal=cp, lat=punto[0], lon=punto[1],
                                tipo_centro=tipo, geocodificado=metodo))

    for s in sedes:
        if s.get("denCorta") in EXCLUIR:
            excluidos += 1
            continue
        vistos.add(s["codcen"])
        g = s.get("geo-referencia") or {}
        anadir(s["codcen"], nombre(sigla(s.get("denCorta")), s["dencen"]),
               normalizar_direccion(s["domcen"]), localidad(s["loccen"]), titulo(s["muncen"]),
               s["cpcen"], s.get("denLarga") or s.get("tipo"),
               (g["lat"], g["lon"]) if g.get("lat") else None)

    for codigo, r in rcd.items():
        if codigo in vistos:
            continue
        gen = r["DENOMINACIÓN GENÉRICA"]
        if gen == "Aula Hospitalaria":
            excluidos += 1
            continue
        loc = localidad(r["LOCALIDAD"])
        muni = municipio_de.get(_norm(r["LOCALIDAD"]), loc)
        anadir(codigo, nombre(GENERICAS.get(gen, ""), r["DENOMINACIÓN ESPECÍFICA"]) if gen in GENERICAS
               else nombre("", f'{gen} {r["DENOMINACIÓN ESPECÍFICA"]}'),
               normalizar_direccion(r["DOMICILIO"]), loc, muni, r["CÓD POSTAL"], gen, None)

    cache.guardar()
    print(f"Excluidos: {excluidos}. Geocodificados con CartoCiudad: {geo} "
          f"({cache.consultas} consultados ahora). Sin coordenadas: {sin_coords}")
    guardar(features, SALIDA, {"url": recurso["url"], "actualizado": recurso.get("last_modified")})


if __name__ == "__main__":
    main()
