"""Castilla-La Mancha -> Castilla-La Mancha/centros_castilla_la_mancha.geojson

Fuente: buscador EDUCEN de la Consejería (Registro de Centros Docentes), aplicación PrimeFaces sin
fichero descargable. Se reproduce lo que hace el navegador: búsqueda sin filtro de naturaleza
(públicos + privados) y una petición de paginación que devuelve todas las filas de golpe.
No hay coordenadas oficiales: todos los centros se geocodifican con CartoCiudad (con caché).
"""
import html
import http.cookiejar
import os
import re
import urllib.parse
import urllib.request

from comun import SSL_CTX, Geocache, expandir_via, feature, guardar, titulo

URL = "https://educen.jccm.es/educen/public/consulta.xhtml"
SALIDA = os.path.join(os.path.dirname(__file__), "..", "Castilla-La Mancha", "centros_castilla_la_mancha.geojson")
BOTON = "form:tabsBusqueda:tabEligeBusqueda:j_idt386"
TABLA = "form:tabsBusqueda:tabEligeBusqueda:tblCentros"

# Provincia por los dos primeros dígitos del código de centro (código INE).
PROVINCIAS = {"02": "Albacete", "13": "Ciudad Real", "16": "Cuenca", "19": "Guadalajara", "45": "Toledo"}

TIPOS = {
    "CEIP": "Colegio de Educación Infantil y Primaria",
    "EMEI": "Escuela Municipal de Educación Infantil",
    "IES": "Instituto de Educación Secundaria",
    "IESO": "Instituto de Educación Secundaria Obligatoria",
    "SES": "Sección de Educación Secundaria",
    "AEPA": "Aula de Educación de Personas Adultas",
    "CEPA": "Centro de Educación de Personas Adultas",
    "CRA": "Colegio Rural Agrupado",
    "EEI": "Escuela de Educación Infantil",
    "EPMD": "Escuela Pública de Música y Danza",
    "EPM": "Escuela Pública de Música",
    "EPD": "Escuela Pública de Danza",
    "EOI": "Escuela Oficial de Idiomas",
    "EEOI": "Extensión de Escuela Oficial de Idiomas",
    "CEE": "Centro de Educación Especial",
    "CPM": "Conservatorio Profesional de Música",
    "CEM": "Conservatorio Elemental de Música",
    "CSM": "Conservatorio Superior de Música",
    "CPD": "Conservatorio Profesional de Danza",
    "CPUIFP": "Centro Público Integrado de Formación Profesional",
    "EA": "Escuela de Arte",
    "EASD": "Escuela de Arte y Superior de Diseño",
    "ESAD": "Escuela Superior de Arte Dramático",
    "PVI": "Centro Privado de Educación Infantil",
    "PVIP": "Centro Privado de Educación Infantil y Primaria",
    "PVIPS": "Centro Privado de Educación Infantil, Primaria y Secundaria",
    "PVES": "Centro Privado de Educación Secundaria",
    "PVEE": "Centro Privado de Educación Especial",
    "PVFPE": "Centro Privado de Formación Profesional Específica",
    "PVAED": "Centro Privado Autorizado de Enseñanzas Deportivas",
}


# Nombres registrales que solo repiten el tipo: se sustituyen por la localidad ("EMEI Albatana").
GENERICOS = {"ESCUELA INFANTIL MUNICIPAL", "AULA DE EDUCACIÓN DE PERSONAS ADULTAS",
             "SECCIÓN DE EDUCACIÓN SECUNDARIA OBLIGATORIA", "ESCUELA MUNICIPAL DE MÚSICA Y DANZA"}


def nombre(r):
    """Abreviatura + nombre registral (la 'Denominación' de la tabla viene truncada)."""
    abrev = r["Denominación Genérica"].strip()
    registral = " ".join(r["Denominación Centro Registral"].split())
    if registral.upper() in GENERICOS:
        return f"{abrev} {r['Localidad']}"
    if not registral:
        d = r["Denominación"]
        registral = d[len(abrev):].strip() if d.startswith(abrev) else d
    return f"{abrev} {titulo(registral, inicio=False)}"


class Educen:
    def __init__(self):
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
            urllib.request.HTTPSHandler(context=SSL_CTX))
        self.op.addheaders = [("User-Agent", "WME-centros-educativos")]

    def get(self):
        with self.op.open(URL, timeout=180) as r:
            return r.read().decode("utf-8")

    def ajax(self, datos):
        req = urllib.request.Request(URL, data=urllib.parse.urlencode(datos).encode(), headers={
            "Faces-Request": "partial/ajax", "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
        with self.op.open(req, timeout=600) as r:
            return r.read().decode("utf-8")


def formulario(pagina):
    """Valores por defecto del formulario JSF (inputs y selects)."""
    form = pagina[pagina.index('<form id="form"'):]
    form = form[:form.index("</form>")]
    datos = {}
    for t in re.findall(r"<input[^>]*>", form):
        n = re.search(r'name="([^"]+)"', t)
        tipo = (re.search(r'type="([^"]+)"', t) or [None, "text"])[1]
        if not n or tipo in ("submit", "button", "image") or (tipo in ("checkbox", "radio") and "checked" not in t):
            continue
        datos[html.unescape(n[1])] = html.unescape((re.search(r'value="([^"]*)"', t) or [None, ""])[1])
    for nombre, opciones in re.findall(r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', form, re.S):
        sel = re.search(r'<option[^>]*value="([^"]*)"[^>]*selected', opciones)
        datos[html.unescape(nombre)] = html.unescape(sel[1]) if sel else ""
    return datos


def municipios(pagina):
    """(localidad, provincia) -> municipio, del desplegable 'Localidad - Municipio(Provincia)'."""
    return {(html.unescape(loc).strip(), html.unescape(prov).strip()): html.unescape(mun).strip()
            for loc, mun, prov in re.findall(r"<option [^>]*>([^<>]+?) - ([^<>]+)\(([^()<>]+)\)</option>", pagina)}


def cabecera(xml):
    return [html.unescape(re.sub(r"<[^>]*>", "", h)).strip() for h in re.findall(r"<th [^>]*>(.*?)</th>", xml, re.S)]


def filas(xml, cab):
    for tr in re.findall(r'<tr data-ri="\d+"[^>]*>(.*?)</tr>', xml, re.S):
        celdas = [html.unescape(re.sub(r"<[^>]*>", "", td)).strip() for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        yield dict(zip(cab, celdas))


def descargar_centros():
    s = Educen()
    pagina = s.get()
    datos = formulario(pagina)
    for k in datos:
        if k.endswith("naturalezaCentro_input"):
            datos[k] = ""  # por defecto solo públicos
    datos.update({"javax.faces.partial.ajax": "true", "javax.faces.source": BOTON, BOTON: BOTON,
                  "javax.faces.partial.execute": f"form:tabsBusqueda:tabEligeBusqueda:panelFormularioCentroGcen {BOTON}",
                  "javax.faces.partial.render": "form:tabsBusqueda:tabEligeBusqueda:tablaCentros", "form": "form"})
    primera = s.ajax(datos)
    total = re.search(r"de un total de (\d+) encontrados", primera)
    if not total:
        raise SystemExit("EDUCEN no devolvió resultados: ¿ha cambiado el formulario?")
    vs = re.search(r"javax\.faces\.ViewState[^>]*><!\[CDATA\[([^\]]+)", primera)
    if vs:
        datos["javax.faces.ViewState"] = vs[1]
    datos.pop(BOTON)
    datos.update({"javax.faces.source": TABLA, "javax.faces.partial.execute": TABLA,
                  "javax.faces.partial.render": TABLA, TABLA + "_pagination": "true",
                  TABLA + "_first": "0", TABLA + "_rows": total[1], TABLA + "_encodeFeature": "true"})
    lista = list(filas(s.ajax(datos), cabecera(primera)))  # la paginación no repite la cabecera
    if len(lista) != int(total[1]):
        raise SystemExit(f"Esperaba {total[1]} centros y llegaron {len(lista)}")
    return lista, municipios(pagina)


def main():
    lista, munis = descargar_centros()
    cache = Geocache("castilla_la_mancha")
    features, sin_coords, geo = [], 0, {}
    for r in lista:
        if r.get("Situación") != "ALTA":
            continue
        abrev, nom = r["Denominación Genérica"].strip(), nombre(r)
        direccion = titulo(expandir_via(r["Domicilio"]))
        provincia, localidad = PROVINCIAS.get(r["Código"][:2], ""), r["Localidad"]
        municipio = munis.get((localidad, provincia), localidad)
        g = cache.buscar(r["Código"], nom, direccion, municipio, provincia)
        if not g:
            sin_coords += 1
            continue
        lat, lon, metodo = g
        geo[metodo] = geo.get(metodo, 0) + 1
        features.append(feature(
            codigo=r["Código"], nombre=nom, direccion=direccion,
            poblacion=localidad, municipio=municipio, codigo_postal=r["Código Postal"],
            lat=lat, lon=lon, tipo_centro=TIPOS.get(abrev, abrev), geocodificado=metodo,
        ))
    cache.guardar()
    print(f"Geocodificados: {geo} ({cache.consultas} consultados ahora). Sin coordenadas: {sin_coords}")
    # Sin fecha de actualización publicada (el registro se consulta en vivo).
    guardar(features, SALIDA, {"url": URL})


if __name__ == "__main__":
    main()
