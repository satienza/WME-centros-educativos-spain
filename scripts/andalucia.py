"""Andalucía -> Andalucía/centros.geojson (datos abiertos Junta, "Directorio de centros docentes no universitarios")"""
import csv
import io
import json
import os
import re

from comun import descargar, expandir_via, feature, guardar

API = ("https://www.juntadeandalucia.es/datosabiertos/portal/api/3/action/package_show"
       "?id=directorio-de-centros-docentes-de-andalucia")
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Andalucía", "centros.geojson")

# La fuente solo da el tipo completo. Abreviaturas oficiales sacadas de los listados PDF de
# educaweb (C.E.I.P., S.E.P., ...) sin puntos; los tipos que no estén aquí usan el nombre completo.
ABREV = {
    "Colegio de Educación Infantil y Primaria": "CEIP",
    "Centro de Educación Infantil": "CEI",
    "Instituto de Educación Secundaria": "IES",
    "Escuela Infantil": "EI",
    "Centro Docente Privado": "CDP",
    "Sección de Educación Permanente": "SEP",
    "Centro de Educación Permanente": "CEPER",
    "Colegio Público Rural": "CPR",
    "Escuela Municipal de Música": "EMM",
    "Colegio de Educación Primaria": "CEPR",
    "Escuela Oficial de Idiomas": "EOI",
    "Centro Docente Privado de Educación Especial": "CDPEE",
    "Conservatorio Elemental de Música": "CEM",
    "Conservatorio Profesional de Música": "CPM",
    "Escuela Municipal de Música y Danza": "EMMD",
    "Centro Específico de Educación Especial": "CEEE",
    "Centro público integrado de formación profesional": "CPIFP",
    "Escuela de Arte y Superior de Diseño": "EASD",
    "Instituto Provincial de Educación Permanente": "IPEP",
    "Escuela de Arte": "EA",
    "Conservatorio Profesional de Danza": "CPD",
    "Conservatorio Superior de Música": "CSM",
    "Sección de Educación Secundaria Obligatoria": "SESO",
    "Escuela Superior de Arte Dramático": "ESAD",
    "Sección de Instituto Provincial de Educación Permanente": "SIPEP",
    "Escuela Municipal de Danza": "EMD",
    "Conservatorio Superior de Danza": "CSD",
}


def ultimo_curso():
    """Recurso CSV del curso más reciente: (url, curso '2024/2025', fecha de actualización)."""
    recursos = json.loads(descargar(API))["result"]["resources"]
    cursos = [(m[1], r) for r in recursos if (m := re.search(r"Curso (\d{4}/\d{4})", r["name"]))]
    curso, r = max(cursos)
    # La API publica las URL con un host interno que no resuelve fuera de la Junta.
    url = re.sub(r"^https://[^/]+", "https://www.juntadeandalucia.es", r["url"])
    return url, curso, r.get("last_modified") or r.get("created")


def numero(txt):
    return float(txt.replace(",", ".")) if txt.strip() else None


def main():
    url, curso, actualizado = ultimo_curso()
    features, sin_coords = [], 0
    for r in csv.DictReader(io.StringIO(descargar(url)), delimiter=";"):
        lat, lon = numero(r["N_LATITUD"]), numero(r["N_LONGITUD"])
        if lat is None or lon is None or not (35 < lat < 39 and -8 < lon < -1):  # hay filas con 0,0
            sin_coords += 1
            continue
        tipo = r["D_DENOMINA"].strip()
        features.append(feature(
            codigo=r["codigo"],
            nombre=f'{ABREV.get(tipo, tipo)} {r["D_ESPECIFICA"].strip()}',
            direccion=expandir_via(r["D_DOMICILIO"]),
            poblacion=r["D_LOCALIDAD"].strip(),
            municipio=r["D_MUNICIPIO"].strip(),
            codigo_postal=r["C_POSTAL"],
            lat=lat, lon=lon,
            tipo_centro=tipo,
            curso=curso,
        ))
    print(f"Curso {curso}. Sin coordenadas válidas: {sin_coords}")
    guardar(features, SALIDA, {"url": url, "actualizado": actualizado})


if __name__ == "__main__":
    main()
