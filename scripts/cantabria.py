"""Cantabria -> Cantabria/centros.geojson

No hay fichero descargable: el buscador de educantabria incrusta todos los centros en el HTML
(bloques 'var centroAux = new Object(); centroAux.latitud = ...' que alimentan su mapa Leaflet).
ponytail: depende del formato de ese JavaScript; si la página cambia, el script falla al no
encontrar centros (no genera un fichero vacío).
"""
import html
import os
import re

from comun import descargar, expandir_via, feature, guardar, titulo

URL = "https://www.educantabria.es/centros/buscador-de-centros"
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Cantabria", "centros.geojson")
CAMPO = re.compile(r"centroAux\.(\w+) = '((?:[^'\\]|\\.)*)';")

# La fuente no trae el tipo: se deduce de la abreviatura con la que empieza el nombre.
TIPOS = {
    "CEIP": "Colegio de Educación Infantil y Primaria",
    "CC": "Colegio Concertado",
    "IES": "Instituto de Educación Secundaria",
    "IESO": "Instituto de Educación Secundaria Obligatoria",
    "CEPA": "Centro de Educación de Personas Adultas",
    "EMEI": "Escuela Municipal de Educación Infantil",
    "EI": "Escuela Infantil",
    "CCEE": "Centro Concertado de Educación Especial",
    "CEE": "Centro de Educación Especial",
    "CREE": "Centro de Recursos de Educación Especial",
    "CRA": "Colegio Rural Agrupado",
    "CIFP": "Centro Integrado de Formación Profesional",
    "EOI": "Escuela Oficial de Idiomas",
    "EMM": "Escuela Municipal de Música",
    "EMD": "Escuela Municipal de Danza",
    "CPM": "Conservatorio Profesional de Música",
    "CMPM": "Conservatorio Municipal Profesional de Música",
    "EA": "Escuela de Arte",
}


def centros(pagina):
    for bloque in pagina.split("var centroAux = new Object();")[1:]:
        c = {k: html.unescape(v.replace("\\'", "'")) for k, v in CAMPO.findall(bloque)}
        c["ensenanzas"] = re.findall(r"ensenanzas\.push\('([^']*)'\)", bloque)
        yield c


def main():
    features, sin_coords, servicios = [], 0, 0
    lista = list(centros(descargar(URL)))
    if not lista:
        raise SystemExit("No se encontraron centros en la página: ¿ha cambiado su formato?")
    for c in lista:
        # Equipos de orientación, CEP, ADI... solo tienen 'Otros centros': no son centros docentes.
        if c["ensenanzas"] == ["Otros centros"]:
            servicios += 1
            continue
        if not c.get("latitud") or not c.get("longitud"):
            sin_coords += 1
            continue
        # El código oficial va en la URL de la ficha: '/39013459-mancina'.
        m = re.match(r"/(\d{8})", c.get("urlCentroEducantabria", ""))
        codigo = m[1] if m else c.get("id", "")
        titulo_web = " ".join(c["title"].split())
        abrev, _, resto = titulo_web.partition(" ")
        if abrev in TIPOS:
            # El resto ya viene en minúsculas salvo algunos; solo se corrigen los que van en MAYÚSCULAS.
            nombre = f"{abrev} {titulo(resto, inicio=False) if resto.isupper() else resto}"
            tipo = TIPOS[abrev]
        else:
            nombre = titulo(titulo_web) if titulo_web.isupper() else titulo_web
            tipo = "Centro " + c.get("titularidad", "").lower().replace(" - ", " ")
        features.append(feature(
            codigo=codigo,
            nombre=nombre,
            direccion=titulo(expandir_via(c.get("direccion", ""))),
            poblacion=titulo(c.get("localidad", "")),
            municipio=titulo(c.get("municipio", "")),
            codigo_postal=c.get("codigoPostal", ""),
            lat=float(c["latitud"]), lon=float(c["longitud"]),
            tipo_centro=tipo,
        ))
    print(f"Servicios excluidos: {servicios}. Sin coordenadas: {sin_coords}")
    # La página no publica fecha de actualización.
    guardar(features, SALIDA, {"url": URL})


if __name__ == "__main__":
    main()
