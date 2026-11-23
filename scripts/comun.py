"""Utilidades comunes para convertir fuentes de centros educativos al GeoJSON del repo."""
import http.client
import io
import json
import os
import re
import ssl
import time
import unicodedata
import urllib.parse
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

# Intermedios que algunos servidores no envían (p.ej. centrosdocentes.catedu.es no manda el de
# Sectigo). Se añaden a los certificados del sistema: la verificación TLS sigue activa.
SSL_CTX = ssl.create_default_context()
_DIR = os.path.dirname(os.path.abspath(__file__))
_CERTS = os.path.join(_DIR, "certs")
for _f in sorted(os.listdir(_CERTS)):
    SSL_CTX.load_verify_locations(os.path.join(_CERTS, _f))

MINUSCULAS = {"de", "del", "la", "las", "los", "el", "y", "e", "en", "a", "al", "o", "u"}
MINUSCULAS_CA = MINUSCULAS | {"i", "les", "els", "dels", "per", "amb", "sa", "ses", "es", "des"}
ROMANO = re.compile(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")
NO_ROMANO = {"MI", "DI", "CC", "DC", "MC", "CD", "CM", "CL", "LC"}  # palabras/siglas que casan con el patrón
# Palabras que deben quedar tal cual en mayúsculas aunque no sean romanos.
MAYUSCULAS = {"S/N", "IES", "CEIP", "CEO", "CEPA", "CIFP", "EOI", "EEI", "IESO", "FP", "CRA", "CEE", "CER", "FPA", "EI", "CIPFP", "CEP"}


def descargar(url, encoding="utf-8"):
    req = urllib.request.Request(url, headers={"User-Agent": "WME-centros-educativos"})
    with urllib.request.urlopen(req, timeout=120, context=SSL_CTX) as r:
        return r.read().decode(encoding)


def titulo(texto, inicio=True, catalan=False):
    """'JOSÉ SÁNCHEZ Y SÁNCHEZ' -> 'José Sánchez y Sánchez'.

    inicio=False cuando el texto va detrás de otra palabra (abreviatura del tipo de centro):
    'DE MOVERA' -> 'de Movera' (solo de/del; los artículos de un nombre propio se mantienen: 'La Moraña').
    catalan=True: 'MOLL I MARQUÉS' -> 'Moll i Marqués', "D'EIVISSA" -> "d'Eivissa", 'de sa Talaia'.

    ponytail: heurística simple; los romanos válidos (I, II, XXIII...) se mantienen en
    mayúscula. Si alguna palabra real casa con el patrón, añadirla a NO_ROMANO.
    """
    palabras, minusculas = [], MINUSCULAS_CA if catalan else MINUSCULAS
    for i, p in enumerate((texto or "").split()):
        ultima = i == len(texto.split()) - 1
        if catalan and p.upper() == "I" and i > 0 and not ultima:  # catalán 'MOLL I MARQUÉS'; romano 'PALMA I'
            palabras.append("i")
        elif p.upper() in MAYUSCULAS or ((r := p.strip(",.;:)(")) and ROMANO.match(r) and r not in NO_ROMANO):
            palabras.append(p.upper())
        elif (i > 0 and p.lower() in minusculas) or (i == 0 and not inicio and p.lower() in {"de", "del"}):
            palabras.append(p.lower())
        elif catalan and i > 0 and re.match(r"(?i)[dl]['’]\w", p):
            palabras.append(p[:2].lower() + titulo(p[2:]))
        else:
            # Capitaliza tras guion, apóstrofo, paréntesis o punto ("Fco.-Javier", "(La)").
            palabras.append(re.sub(r"(^|[-'(.\"])(\w)", lambda m: m[1] + m[2].upper(), p.lower()))
    return " ".join(palabras)


def direccion(via, nombre, numero):
    """('CALLE', 'SAN FRANCISCO', '25') -> 'Calle San Francisco, 25'."""
    calle = titulo(f"{via or ''} {nombre or ''}".strip())
    numero = (numero or "").strip()
    return f"{calle}, {numero.upper()}" if numero else calle


# Abreviaturas (y truncados a 6 letras de Andalucía) de tipo de vía -> nombre completo.
VIAS = {
    "C/": "Calle", "CALLE": "Calle", "AVDA.": "Avenida", "AVDA": "Avenida", "AV.": "Avenida",
    "CTRA.": "Carretera", "CTRA": "Carretera", "URB.": "Urbanización", "PZA.": "Plaza",
    "BCO.": "Barranco", "BDA.": "Barriada", "CMO.": "Camino", "PSJE.": "Pasaje",
    "BRR.": "Barrio", "GLOR.": "Glorieta", "TVSÍA.": "Travesía", "BLVAR.": "Bulevar",
    "RBLA.": "Rambla", "CÑA.": "Cañada", "CAÑ.": "Cañada", "CJA.": "Calleja",
    "POLÍGO": "Polígono", "CALLEJ": "Callejón", "ROTOND": "Rotonda", "ALAMED": "Alameda",
    "PARCEL": "Parcela", "CL.": "Calle", "CL": "Calle", "P.º": "Paseo", "Pº": "Paseo",
    "Pº.": "Paseo", "PS.": "Paseo", "CAMI.": "Camino", "CM": "Camino", "B.": "Barrio",
    "Bº": "Barrio", "BO.": "Barrio", "PZ.": "Plaza", "CR.": "Carretera", "RD.": "Ronda",
    "TR.": "Travesía", "LG.": "Lugar", "CJ.": "Calleja", "CM.": "Camino", "PQ.": "Parque",
    "AVD.": "Avenida", "CNO.": "Camino", "PLAZA": "Plaza", "PASEO": "Paseo", "RONDA": "Ronda",
    "TRAVESÍA": "Travesía", "PSO.": "Paseo", "AVENIDA": "Avenida",
}


# Baleares: las calles se nombran en catalán.
VIAS_CA = {"C/": "Carrer", "AV.": "Avinguda", "AV": "Avinguda", "AVDA.": "Avinguda",
           "CTRA.": "Carretera", "CTRA": "Carretera", "CAMI": "Camí", "PL.": "Plaça", "PG.": "Passeig",
           "C.": "Carrer", "PTGE.": "Passatge", "RBLA.": "Rambla", "RDA.": "Ronda", "PÇA.": "Plaça",
           "TRAV.": "Travessera"}


def expandir_via(txt, vias=VIAS):
    """'C/ Mayor, 3' -> 'Calle Mayor, 3'; 'Avda. Andalucía' -> 'Avenida Andalucía'."""
    txt = re.sub(r"^C/(?=\S)", "C/ ", " ".join((txt or "").split()))
    primera, _, resto = txt.partition(" ")
    if primera.upper() == "OTROS":  # Andalucía usa "Otros" como tipo de vía desconocido
        return resto
    return f"{vias[primera.upper()]} {resto}" if primera.upper() in vias and resto else txt


def normalizar_direccion(txt):
    """Direcciones en mayúsculas con abreviaturas pegadas (registro del Ministerio, Murcia):
    'AV.DE LA PAZ, 5' -> 'Avenida de la Paz, 5'; 'C/. ERAS N.º 60' -> 'Calle Eras, 60';
    'CTRA. VILLAFRANCA, SNº' -> 'Carretera Villafranca, S/N'."""
    txt = re.sub(r"^C/\.", "C/", " ".join((txt or "").split()))
    txt = re.sub(r"\bS\s*/?\s*N(?:\s*\.?\s*[º°])?\.?(?![A-ZÁÉÍÓÚÑ])", "S/N", txt, flags=re.I)
    txt = re.sub(r"[,\s]+(?:N\.?\s*[º°]|NÚM\.?)\s*(?=\d)", ", ", txt, flags=re.I)  # 'N.º 60' -> ', 60'
    txt = re.sub(r"\.(?=[A-ZÁÉÍÓÚÑ]{2})", ". ", txt)  # 'AV.DE' -> 'AV. DE'
    txt = re.sub(r"\s*,\s*", ", ", txt)
    txt = re.sub(r"(?<=[^\d,])\s+(\d+\w?|S/N)$", r", \1", txt)  # 'ERAS 60' -> 'ERAS, 60'
    return titulo(expandir_via(txt))


def utm_a_latlon(x, y, huso=30):
    """UTM ETRS89 (EPSG:258xx) -> (lat, lon) WGS84. Fórmulas de Snyder; error < 1 mm en España."""
    import math
    a, f, k0 = 6378137.0, 1 / 298.257222101, 0.9996
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    m = y / k0
    mu = m / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    p = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu)
         + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
         + 151 * e1 ** 3 / 96 * math.sin(6 * mu) + 1097 * e1 ** 4 / 512 * math.sin(8 * mu))
    c, t = ep2 * math.cos(p) ** 2, math.tan(p) ** 2
    n = a / math.sqrt(1 - e2 * math.sin(p) ** 2)
    r = a * (1 - e2) / (1 - e2 * math.sin(p) ** 2) ** 1.5
    d = (x - 500000) / (n * k0)
    lat = p - n * math.tan(p) / r * (d ** 2 / 2 - (5 + 3 * t + 10 * c - 4 * c ** 2 - 9 * ep2) * d ** 4 / 24
                                     + (61 + 90 * t + 298 * c + 45 * t ** 2 - 252 * ep2 - 3 * c ** 2) * d ** 6 / 720)
    lon = (d - (1 + 2 * t + c) * d ** 3 / 6
           + (5 - 2 * c + 28 * t - 3 * c ** 2 + 8 * ep2 + 24 * t ** 2) * d ** 5 / 120) / math.cos(p)
    return round(math.degrees(lat), 7), round(huso * 6 - 183 + math.degrees(lon), 7)


RCD = "https://www.educacion.gob.es/centros/exportarListadoCentrosExcel"


def registro_estatal(id_comunidad):
    """Centros de una comunidad en el Registro Estatal de Centros Docentes del Ministerio
    (exportación Excel del buscador educacion.gob.es/centros, sin coordenadas), por código.
    id_comunidad es el del buscador, no el INE: 10 Extremadura, 12 La Rioja, 14 Murcia,
    15 Navarra, 17 País Vasco."""
    import xlrd  # el Ministerio exporta .xls binario (requirements.txt)
    form = {"nivel": "0", "idComunidad": id_comunidad, "idProvincia": "00", "naturaleza": "0",
            "concertado": "0", "familia": "0", "ensenanza": "0", "modalidad": "0", "tipoCentro": "0",
            "provincial": "", "comarca": "", "pais": "", "localidad": "", "codCentro": "",
            "nombreCentro": "", "denominacion": "0", "ensenanzaFP": ""}
    req = urllib.request.Request(RCD, data=urllib.parse.urlencode(form).encode(),
                                 headers={"User-Agent": "WME-centros-educativos"})
    for intento in range(3):  # el servidor corta a veces la primera conexión sin responder
        try:
            with urllib.request.urlopen(req, timeout=120, context=SSL_CTX) as r:
                datos = r.read()
            break
        except (http.client.RemoteDisconnected, urllib.error.URLError):
            if intento == 2:
                raise
            time.sleep(5)
    hoja = xlrd.open_workbook(file_contents=datos).sheet_by_index(0)
    cab = hoja.row_values(0)
    filas = [dict(zip(cab, hoja.row_values(i))) for i in range(1, hoja.nrows)]
    # El listado termina con unos pocos centros "de ámbito estatal" de otras comunidades.
    comunidad = max(set(f["COMUNIDAD AUTÓNOMA"] for f in filas),
                    key=lambda c: sum(f["COMUNIDAD AUTÓNOMA"] == c for f in filas))
    return {f["CÓDIGO"]: f for f in filas if f["COMUNIDAD AUTÓNOMA"] == comunidad}


def leer_xlsx(datos):
    """Primera hoja de un .xlsx (bytes) -> lista de dicts por cabecera. Solo stdlib."""
    m = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    z = zipfile.ZipFile(io.BytesIO(datos))
    compartidas = []
    if "xl/sharedStrings.xml" in z.namelist():
        compartidas = ["".join(t.text or "" for t in si.iter(m + "t"))
                       for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(m + "si")]
    filas = []
    for fila in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).iter(m + "row"):
        celdas = {}
        for c in fila.iter(m + "c"):
            col = re.match(r"[A-Z]+", c.get("r"))[0]
            v = c.find(m + "v")
            if c.get("t") == "s" and v is not None:
                celdas[col] = compartidas[int(v.text)]
            elif c.get("t") == "inlineStr":
                celdas[col] = "".join(t.text or "" for t in c.iter(m + "t"))
            else:
                celdas[col] = v.text if v is not None else ""
        filas.append(celdas)
    cab = filas[0]
    return [{cab[k]: v for k, v in f.items() if k in cab} for f in filas[1:] if any(f.values())]


CARTOCIUDAD = "https://www.cartociudad.es/geocoder/api/geocoder/"


def _norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())


def _cartociudad(metodo, **params):
    time.sleep(0.15)  # servicio público: sin ráfagas
    try:
        return json.loads(descargar(CARTOCIUDAD + metodo + "?" + urllib.parse.urlencode(params)))
    except (OSError, ValueError):
        return None


def geocodificar(nombre, direccion, municipio, provincia):
    """(lat, lon, método) con CartoCiudad (IGN), o None. De más a menos preciso:
    'toponimo' (el centro está en el nomenclátor por su nombre), 'portal' (mismo número de la
    calle) y 'calle' (punto medio de la calle, para S/N). Medido en Baleares contra posiciones
    conocidas: mediana 25 m en toponimo/portal y 120 m en calle (1 de cada 4 a más de 480 m)."""
    def candidatos(q):
        r = _cartociudad("candidates", q=q, limit=10, municipio_filter=municipio) or []
        return [x for x in r if _norm(x.get("muni")) == _norm(municipio)
                and _norm(x.get("province")) == _norm(provincia)]  # hay municipios homónimos

    n = _norm(nombre)
    for x in candidatos(nombre):
        if x["type"] == "toponimo" and x.get("lat") and n in _norm(x["address"].split(",")[0]):
            return x["lat"], x["lng"], "toponimo"
    m = re.match(r"(.*?),?\s*(?:(?:n[uú]m\.?|nº)\s*)?(\d+)\b", direccion, re.I)
    if m:
        num = int(m[2])
        for x in candidatos(f"{m[1]} {num}"):
            if x["type"] == "portal" and x.get("lat") and x.get("portalNumber") == num:
                return x["lat"], x["lng"], "portal"
    via = re.split(r",|\bS/N\b", direccion, flags=re.I)[0].strip()
    calle = next((x for x in candidatos(via) if x["type"] == "callejero"), None)
    if calle:
        f = _cartociudad("find", q=calle["address"], type="callejero", id=calle["id"])
        if f and f.get("lat"):
            return f["lat"], f["lng"], "calle"
    return None


class Geocache:
    """geocodificar() con caché en scripts/cache/<nombre>.json (se versiona en el repo).

    Un centro solo se vuelve a geocodificar si es nuevo o cambia su dirección/municipio; así la
    ejecución semanal no repite miles de consultas a CartoCiudad. Guarda solo los centros usados
    en esta ejecución (los dados de baja desaparecen de la caché)."""

    def __init__(self, nombre):
        self.ruta = os.path.join(_DIR, "cache", nombre + ".json")
        try:
            with open(self.ruta, encoding="utf-8") as f:
                self.viejo = json.load(f)
        except FileNotFoundError:
            self.viejo = {}
        self.nuevo, self.consultas = {}, 0

    def buscar(self, codigo, nombre, direccion, municipio, provincia):
        clave = f"{direccion}|{municipio}"
        e = self.viejo.get(codigo)
        if not e or e["clave"] != clave:
            res = geocodificar(nombre, direccion, municipio, provincia)
            e = {"clave": clave, "res": list(res) if res else None}
            self.consultas += 1
            if self.consultas % 100 == 0:  # no perder el progreso si se corta una ejecución larga
                self.guardar(parcial=True)
        self.nuevo[codigo] = e
        return tuple(e["res"]) if e["res"] else None

    def guardar(self, parcial=False):
        datos = {**self.viejo, **self.nuevo} if parcial else self.nuevo
        os.makedirs(os.path.dirname(self.ruta), exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8") as f:
            json.dump(dict(sorted(datos.items())), f, ensure_ascii=False, indent=0)
            f.write("\n")


def feature(codigo, nombre, direccion, poblacion, municipio, codigo_postal, lat, lon,
            tipo_centro, curso=None, estado=None, geocodificado=None):
    props = {
        "nombre": nombre,
        "direccion": direccion,
        "poblacion": poblacion,
        "municipio": municipio,
        "codigo_postal": (codigo_postal or "").strip().zfill(5) if (codigo_postal or "").strip() else "",
        # texto: WME Geometries solo etiqueta con propiedades string (las numéricas salen "undefined")
        "latitud": str(lat),
        "longitud": str(lon),
        "tipo_centro": tipo_centro,
        "codigo": codigo,
    }
    if curso:
        props["curso"] = curso
    if estado:
        props["estado"] = estado
    if geocodificado:  # coordenadas calculadas por dirección, no de la fuente oficial
        props["geocodificado"] = geocodificado
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": props}


def guardar(features, ruta, fuente):
    features.sort(key=lambda f: f["properties"]["codigo"])
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "fuente": fuente, "features": features},
                  f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"{ruta}: {len(features)} centros")
