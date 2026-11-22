"""Galicia -> Galicia/centros.geojson (abertos.xunta.gal, dataset 0257, un CSV por provincia)"""
import csv
import io
import os
import re

from comun import descargar, feature, guardar, titulo

BASE = "https://abertos.xunta.gal/catalogo/ensino-formacion/-/dataset/0257/centros-educativos-galicia"
# 001 A Coruña, 003 Lugo, 005 Ourense, 007 Pontevedra (los pares son el mismo dato en XML).
URLS = [f"{BASE}/{n}/descarga-directa-ficheiro.csv" for n in ("001", "003", "005", "007")]
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Galicia", "centros.geojson")

# La fuente solo trae la abreviatura. ponytail: los tipos que no estén aquí se quedan con la abreviatura.
TIPOS = {
    "CEIP": "Colegio de Educación Infantil y Primaria",
    "CPR": "Centro Privado",
    "IES": "Instituto de Educación Secundaria",
    "EEI": "Escuela de Educación Infantil",
    "ESMU": "Escuela de Música",
    "CPI": "Centro Público Integrado",
    "EMUSPR": "Escuela de Música Privada",
    "CMUS": "Conservatorio de Música",
    "CIFP": "Centro Integrado de Formación Profesional",
    "CRA": "Colegio Rural Agrupado",
    "CEMU": "Centro Autorizado de Música",
    "CEEPR": "Centro Privado de Educación Especial",
    "CEP": "Colegio de Educación Primaria",
    "CAD": "Centro Autorizado de Enseñanzas Deportivas",
    "CEE": "Centro de Educación Especial",
    "EOI": "Escuela Oficial de Idiomas",
    "EPAPU": "Escuela Pública de Educación de Personas Adultas",
    "CPREX": "Centro Privado Extranjero",
    "EDANPR": "Escuela de Danza Privada",
    "CFEA": "Centro de Formación y Experimentación Agroforestal",
    "CEDA": "Centro Autorizado de Danza",
    "CE.ART": "Centro Autorizado de Enseñanzas Artísticas",
    "EASD": "Escuela de Arte y Superior de Diseño",
    "EFAG": "Escuela Familiar Agraria",
    "CDAN": "Conservatorio de Danza",
    "ESDA": "Escuela de Danza",
    "CADF": "Centro Autorizado de Enseñanzas Deportivas de Fútbol",
    "EFOG": "Escuela de Formación Profesional",
    "ESAD": "Escuela Superior de Arte Dramático",
}


def sin_mayusculas(txt):
    """Solo pasa a formato título las palabras en MAYÚSCULAS; el resto ya viene bien escrito
    (aplicar titulo() a todo rompería 'A Coruña' -> 'a Coruña')."""
    return re.sub(r"\S{2,}", lambda m: titulo(m[0]) if m[0].isupper() else m[0], txt.strip())


def main():
    features, sin_coords = [], 0
    for url in URLS:
        for r in csv.DictReader(io.StringIO(descargar(url))):
            abrev, nombre = r["Tipo de centro"].strip(), r["Nome"].strip()
            resto = nombre[len(abrev):].strip() if nombre.startswith(abrev) else nombre
            # COORDENADA_X/Y vienen en orden variable según la fila; en Galicia la latitud
            # es la positiva y la longitud la negativa.
            x, y = float(r["COORDENADA_X"]), float(r["COORDENADA_Y"])
            lat, lon = max(x, y), min(x, y)
            if not (41.7 < lat < 43.9 and -9.5 < lon < -6.6):  # hay filas con 0,0
                sin_coords += 1
                continue
            features.append(feature(
                codigo=r["Código"],
                nombre=f"{abrev} {sin_mayusculas(resto)}",
                direccion=sin_mayusculas(r["Enderezo"]),
                poblacion=r["Concello"].strip(),  # la fuente no trae localidad
                municipio=r["Concello"].strip(),
                codigo_postal=r["Cód. postal"],
                lat=lat, lon=lon,
                tipo_centro=TIPOS.get(abrev, abrev),
            ))
    print(f"Sin coordenadas válidas: {sin_coords}")
    guardar(features, SALIDA, {"url": BASE})


if __name__ == "__main__":
    main()
