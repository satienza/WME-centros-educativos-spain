"""Canarias -> Canarias/centros.geojson"""
import csv
import io
import json
import os

from comun import descargar, expandir_via, feature, guardar, titulo

URL = ("https://datos.canarias.es/catalogos/general/dataset/f6b15811-014b-46f7-a858-fe48b062ed05"
       "/resource/b5e08adf-841b-4ba5-a599-4339e772d792/download/centros.csv")
# API CKAN: da la fecha de actualización del recurso sin descargar el CSV.
META = ("https://datos.canarias.es/catalogos/general/api/3/action/resource_show"
        "?id=b5e08adf-841b-4ba5-a599-4339e772d792")
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Canarias", "centros.geojson")

def main():
    actualizado = json.loads(descargar(META))["result"]["last_modified"]
    features, sin_coords = [], 0
    for r in csv.DictReader(io.StringIO(descargar(URL))):
        if not r["Latitud"] or not r["Longitud"]:
            sin_coords += 1
            continue
        abrev, denom = r["DesEtapaCentro"], r["Denominacion"]
        if denom.startswith(abrev + " "):
            denom = denom[len(abrev) + 1:]
        lat, lon = float(r["Latitud"]), float(r["Longitud"])
        features.append(feature(
            codigo=r["Codigo"],
            nombre=f"{abrev} {titulo(denom, inicio=False)}",
            direccion=titulo(expandir_via(r["Direccion"])),
            poblacion=titulo(r["Localidad"]),
            municipio=titulo(r["Municipio"]),
            codigo_postal=r["CodigoPostal"],
            lat=lat, lon=lon,
            tipo_centro=r["DescripcionEtapaCentro"],
        ))
    print(f"Sin coordenadas: {sin_coords}")
    guardar(features, SALIDA, {"url": URL, "actualizado": actualizado})


if __name__ == "__main__":
    main()
