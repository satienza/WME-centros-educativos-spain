"""Baleares -> Baleares/centros.geojson

Datos: Excel "Llistat de centres educatius" de la Conselleria (sin coordenadas).
Coordenadas: capa "Equipament educatiu" de IDEIB, cruzada por código de centro.
La capa IDEIB no se edita desde 2018: los centros que no están se geocodifican con CartoCiudad
y llevan la propiedad "geocodificado" (toponimo / portal / calle).
"""
import json
import os
import re
import urllib.parse
import urllib.request

from comun import (SSL_CTX, VIAS_CA, descargar, expandir_via, Geocache, feature, guardar,
                   leer_xlsx, titulo)

PAGINA = ("https://intranet.caib.es/sites/planificacioicentres/es/"
          "llistat_de_centres_educatius_de_les_illes_balears/")
IDEIB = ("https://ideib.caib.es/geoserveis/rest/services/public/GOIB_SUPE_IB/MapServer/0/query"
         "?where=1%3D1&outFields=ID_REGISTRE,FUNCIO&outSR=4326&f=geojson")
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Baleares", "centros.geojson")

# Servicios educativos (equipos de orientación, centros de profesorado...), no son centros docentes.
SERVICIOS = {"EAP", "EOEP", "CEP", "CEFIRDE", "SAED", "EPEP", "MEIB"}
# Códigos de la fuente -> abreviatura para el nombre (según el documento TIPUS de la Conselleria).
ABREV = {"EIEL": "EI"}
# Tipos completos (castellano). Los que falten usan la función de IDEIB o el código.
TIPOS = {
    "CEIP": "Colegio de Educación Infantil y Primaria",
    "EI": "Escuela Infantil",
    "EIEL": "Escuela Infantil",
    "CEI": "Centro de Educación Infantil Privado",
    "CCEI": "Centro Concertado de Educación Infantil",
    "CC": "Colegio Concertado",
    "C": "Colegio Privado",
    "IES": "Instituto de Educación Secundaria",
    "CEPA": "Centro de Educación de Personas Adultas",
    "CPFP": "Centro Privado de Formación Profesional",
    "CCFP": "Centro Concertado de Formación Profesional",
    "CIFP": "Centro Integrado de Formación Profesional",
    "CDE": "Centro Docente Extranjero",
    "CCEE": "Centro Concertado de Educación Especial",
    "CEE": "Centro de Educación Especial",
    "EOI": "Escuela Oficial de Idiomas",
    "EA": "Escuela de Arte",
    "CA": "Campo de Aprendizaje",
    "CP": "Colegio de Educación Primaria",
    "CEIPIESO": "Colegio de Educación Infantil, Primaria y ESO",
    "CEIPIEEM": "Colegio de Educación Infantil y Primaria y Enseñanzas Elementales de Música",
    "CSMD": "Conservatorio Superior de Música y Danza",
    "EMR": "Escuela de Música Reconocida",
    "EMDR": "Escuela de Música y Danza Reconocida",
}
# Nombres que ya empiezan por el tipo escrito ("ESCOLA OFICIAL D'IDIOMES DE CALVIÀ"): sin abreviatura.
GENERICOS = ("CENTRE", "ESCOLA", "CONSERVATORI", "COL·LEGI", "CAMP", "AULA", "AMPLIACIÓ", "CIFP",
             "CAHOSPD")


def excel():
    """Enlace al .xlsx de la página; la fecha va en el nombre: Taula_centres_07-09-2026.xlsx."""
    html = descargar(PAGINA)
    url = urllib.parse.urljoin(PAGINA, re.search(r'href="(archivopub\.do\?[^"]+)">Listado', html)[1]
                               .replace("&amp;", "&"))
    req = urllib.request.Request(url, headers={"User-Agent": "WME-centros-educativos"})
    with urllib.request.urlopen(req, timeout=120, context=SSL_CTX) as r:
        fecha = re.search(r"(\d{2})-(\d{2})-(\d{4})", r.headers.get("Content-Disposition", ""))
        return url, r.read(), fecha and f"{fecha[3]}-{fecha[2]}-{fecha[1]}"


def nombre(codigo, nom):
    """('CEI', 'ANGELETS DE LLUM CAMPOS_abans Plou i Fa Sol') -> 'CEI Angelets de Llum Campos'."""
    if nom.startswith("CENTRE AUTORIT"):  # 'CENTRE AUTORIT ENSENY _ELEMENTALS DE MÚSICA, X'
        nom = nom.replace("_", " ")
    nom = re.sub(r"\s*\(.*", "", nom.split("_")[0]).strip(" ,")  # notas: '_abans ...', '(adscrita...)'
    base = re.split(r"[_\- ]", codigo)[0]
    if nom.split()[0] in GENERICOS or base == "C":
        return titulo(nom, catalan=True)
    return f"{ABREV.get(base, base)} {titulo(nom, inicio=False, catalan=True)}"


def main():
    url, datos, actualizado = excel()
    ideib = {f["properties"]["ID_REGISTRE"]: f for f in json.loads(descargar(IDEIB))["features"]}
    features, sin_coords, geo, cache = [], 0, {}, Geocache("baleares")
    for r in leer_xlsx(datos):
        codigo, tipo = r.get("CODI", "").strip(), r.get("DENOMINACIÓ GENÈRICA", "").strip()
        base = re.split(r"[_\- ]", tipo)[0]
        if not codigo or base in SERVICIOS:
            continue
        punto = ideib.get(codigo)
        nom, municipio = nombre(tipo, r["NOM"].strip()), titulo(r.get("MUNICIPI", ""), catalan=True)
        metodo = None
        if punto and punto["geometry"]:
            lon, lat = punto["geometry"]["coordinates"][:2]
        else:
            g = cache.buscar(codigo, nom, r.get("ADREÇA", ""), municipio, "Illes Balears")
            if not g:
                sin_coords += 1
                continue
            lat, lon, metodo = g
            geo[metodo] = geo.get(metodo, 0) + 1
        features.append(feature(
            codigo=codigo,
            nombre=nom,
            direccion=titulo(expandir_via(r.get("ADREÇA", ""), VIAS_CA), catalan=True),
            poblacion=titulo(r.get("LOCALITAT", ""), catalan=True),
            municipio=municipio,
            codigo_postal=r.get("CP", ""),
            lat=lat, lon=lon,
            tipo_centro=TIPOS.get(base) or (punto and punto["properties"]["FUNCIO"]) or tipo,
            geocodificado=metodo,
        ))
    cache.guardar()
    print(f"Geocodificados con CartoCiudad: {geo} ({cache.consultas} consultados ahora). Sin coordenadas: {sin_coords}")
    guardar(features, SALIDA, {"url": url, "actualizado": actualizado})


if __name__ == "__main__":
    main()
