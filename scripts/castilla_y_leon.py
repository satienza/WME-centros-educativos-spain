"""Castilla y León -> Castilla y León/centros_castilla_y_leon.geojson"""
import csv
import io
import os

from comun import descargar, direccion, feature, guardar, titulo

URL = "https://directorio.educa.jcyl.es/es/datos-abiertos-centros-docentes"
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Castilla y León", "centros_castilla_y_leon.geojson")


# La fuente escribe los tipos sin tildes.
TILDES = {"EDUCACION": "EDUCACIÓN", "FORMACION": "FORMACIÓN", "MUSICA": "MÚSICA",
          "PUBLICO": "PÚBLICO", "ESPECIFICA": "ESPECÍFICA", "DRAMATICO": "DRAMÁTICO"}


def tipo(txt):
    return titulo(" ".join(TILDES.get(p, p) for p in txt.split()))


def numero(txt):
    return float(txt.replace(",", ".")) if txt.strip() else None


def main():
    filas = csv.DictReader(io.StringIO(descargar(URL, "latin-1")), delimiter=";")
    features, sin_coords = [], 0
    for r in filas:
        lat, lon = numero(r["COORD. LATITUD"]), numero(r["COORD. LONGITUD"])
        if lat is None or lon is None:
            sin_coords += 1
            continue
        features.append(feature(
            codigo=r["CÓDIGO"],
            nombre=f'{r["DENOMINACIÓN GENÉRICA BREVE"]} {titulo(r["DENOMINACIÓN ESPECÍFICA"], inicio=False)}',
            direccion=direccion(r["VÍA"], r["NOMBRE DE LA VÍA"], r["NÚMERO"] or r["NÚMERO(EXT)"]),
            poblacion=titulo(r["LOCALIDAD"]),
            municipio=titulo(r["MUNICIPIO"]),
            codigo_postal=r["C.POSTAL"],
            lat=lat, lon=lon,
            tipo_centro=tipo(r["DENOMINACIÓN GENÉRICA"]),
            curso=r["CURSO ACADÉMICO"],
            estado=r["SITUACIÓN"].capitalize(),
        ))
    print(f"Sin coordenadas: {sin_coords}")
    # Sin fecha: la fuente no la publica y poner la de hoy generaría un commit en cada ejecución.
    guardar(features, SALIDA, {"url": URL})


if __name__ == "__main__":
    main()
