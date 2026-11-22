# WME-centros-educativos-spain
Geojson de los centros educativos en españa para la edición de zonas escolares.

## Estructura

Los ficheros GeoJSON se organizan en carpetas por comunidad autónoma:

- Andalucía
- Aragón
- Asturias
- Baleares
- Canarias
- Cantabria
- Castilla-La Mancha
- Castilla y León
- Cataluña
- Comunidad Valenciana
- Extremadura
- Galicia
- La Rioja
- Comunidad de Madrid
- Región de Murcia
- Navarra
- País Vasco

## Formato del GeoJSON

Cada comunidad tiene un `centros_<comunidad>.geojson` (WGS84), con el mismo nombre que su script (`Andalucía/centros_andalucia.geojson`, `Comunidad de Madrid/centros_madrid.geojson`…), para distinguirlos al descargar varios. Cada uno tiene un `Point` por centro y estas propiedades:

| Propiedad | Ejemplo | Notas |
|---|---|---|
| `nombre` | `CEIP José Sánchez y Sánchez` | abreviatura del tipo + nombre |
| `direccion` | `Calle San Francisco, 25` | tipo de vía + nombre + número |
| `poblacion` | `Segovia` | localidad |
| `municipio` | `Segovia` | |
| `codigo_postal` | `40001` | texto de 5 cifras |
| `latitud`, `longitud` | `40.94623`, `-4.11764` | |
| `tipo_centro` | `Colegio de Educación Infantil y Primaria` | sin abreviar |
| `codigo` | `40008561` | código oficial del centro |
| `curso` | `2026` | opcional, solo si la fuente lo trae |
| `estado` | `Alta` | opcional, solo si la fuente lo trae |
| `geocodificado` | `portal` | opcional: las coordenadas no vienen de la fuente oficial sino de [CartoCiudad](https://www.cartociudad.es) por nombre (`toponimo`) o dirección (`portal`, mismo número; `calle`, punto medio de la calle: revisar en el mapa) |

La colección incluye `fuente` con la `url` de origen y, si la fuente la publica, la fecha `actualizado`. Los centros sin coordenadas se descartan.

Para usarlo en WME: abrir el fichero con WME-Geometries y elegir `nombre` como propiedad de etiqueta.

## Fuentes y scripts

Python 3. Asturias y los scripts que usan el registro estatal del Ministerio (Extremadura, La Rioja, Murcia, Navarra) necesitan `xlrd` (`pip install -r requirements.txt`) porque sus fuentes son `.xls` binarios. Cada script descarga la fuente y genera el GeoJSON de su carpeta:

```sh
python3 scripts/test_comun.py
python3 scripts/castilla_y_leon.py
python3 scripts/canarias.py
python3 scripts/galicia.py
python3 scripts/andalucia.py
python3 scripts/aragon.py
python3 scripts/asturias.py
python3 scripts/baleares.py
python3 scripts/cantabria.py
python3 scripts/castilla_la_mancha.py
python3 scripts/cataluna.py
python3 scripts/madrid.py
python3 scripts/valencia.py
python3 scripts/extremadura.py
python3 scripts/rioja.py
python3 scripts/murcia.py
python3 scripts/navarra.py
python3 scripts/pais_vasco.py
```

| Comunidad | Fuente | Fecha de actualización |
|---|---|---|
| Andalucía | [Junta de Andalucía, datos abiertos](https://www.juntadeandalucia.es/datosabiertos/portal/dataset/directorio-de-centros-docentes-de-andalucia) (un CSV por curso; el script elige el más reciente) | API CKAN `package_show` → `last_modified` del recurso |
| Aragón | [centrosdocentes.catedu.es](https://centrosdocentes.catedu.es/ee/) (botón Exportar sin filtros: `php/export/export_centros.php`) | no publicada |
| Asturias | [educastur, directorio de centros](https://www.educastur.es/directorio-de-centros) (`.xls` sin coordenadas) + coordenadas de la capa [SIG Asturias "Centros Educativos"](https://sig.asturias.es/servicios/rest/services/Visor/Educacion/MapServer/0) por código; los que no están se geocodifican con CartoCiudad (propiedad `geocodificado`) | "ACTUALIZADO dd-mm-aaaa" en la página |
| Baleares | [Llistat de centres educatius](https://intranet.caib.es/sites/planificacioicentres/es/llistat_de_centres_educatius_de_les_illes_balears/) (`.xlsx` sin coordenadas) + coordenadas de la capa [IDEIB "Equipament educatiu"](https://ideib.caib.es/geoserveis/rest/services/public/GOIB_SUPE_IB/MapServer/0) por código; la capa es de 2018 y los centros que faltan se geocodifican con CartoCiudad (propiedad `geocodificado`) | fecha en el nombre del fichero |
| Canarias | [datos.canarias.es](https://datos.canarias.es/catalogos/general/dataset/centros-educativos-de-canarias/resource/b5e08adf-841b-4ba5-a599-4339e772d792) | API CKAN `resource_show` → `last_modified` |
| Cantabria | [Buscador de centros de educantabria](https://www.educantabria.es/centros/buscador-de-centros): no hay fichero; los centros (con coordenadas) van incrustados en el JavaScript del mapa de la página | no publicada |
| Castilla-La Mancha | [Buscador EDUCEN](https://educen.jccm.es/educen/public/consulta.xhtml) (Registro de Centros Docentes; la página de la Consejería lo incrusta). Sin fichero ni coordenadas: el script reproduce la búsqueda (públicos y privados) y geocodifica todos los centros con CartoCiudad | no publicada |
| Castilla y León | [directorio.educa.jcyl.es](https://directorio.educa.jcyl.es/es/datos-abiertos-centros-docentes) (la URL devuelve el CSV directamente) | no publicada |
| Cataluña | ["Directori de centres docents anual" — Transparència Catalunya](https://analisi.transparenciacatalunya.cat/d/kvmv-ahh4) (API Socrata, con coordenadas; el script toma el curso más reciente). Son los mismos datos de las fichas de [mapaescolar.gencat.cat](https://mapaescolar.gencat.cat/) | `rowsUpdatedAt` del dataset |
| Comunidad de Madrid | Capa WFS [`WPAD_V_CENTROS_GIS` de la IDEM](https://idem.comunidad.madrid/geosrvg/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=WPAD_V_CENTROS_GIS&outputFormat=application/json&srsName=EPSG:4326&count=5): la que pinta el mapa del [buscador de centros](https://gestiona.comunidad.madrid/wpad_pub/run/j/MostrarConsultaGeneral.icm), con los mismos centros que su listado y con coordenadas (4 decimales, unos ±5 m). Los que no tienen coordenadas se geocodifican con CartoCiudad | no publicada (datos al día) |
| Comunidad Valenciana | [dadesobertes.gva.es, "Centros docentes de la Comunitat Valenciana"](https://dadesobertes.gva.es/dataset/edu-centros) (CSV con coordenadas; mismo registro que la [Guía de centros docentes](https://ceice.gva.es/es/web/centros-docentes/guia-de-centros-docentes)) | API CKAN `package_show` → `last_modified` del recurso |
| Extremadura | [Registro Estatal de Centros Docentes del Ministerio](https://www.educacion.gob.es/centros/) (exportación Excel del buscador, un POST con `idComunidad=10`; sin coordenadas) + coordenadas de las capas WFS de la [IDEEX "Centros educativos"](https://mapas.ideex.es/CICTEX/centrosEducativos?REQUEST=GetCapabilities&SERVICE=WFS) por código; la cartografía es de 2015 y los centros que faltan se geocodifican con CartoCiudad (propiedad `geocodificado`) | no publicada |
| Galicia | [abertos.xunta.gal, dataset 0257](https://abertos.xunta.gal/es/catalogo/ensino-formacion/-/dataset/0257/centros-educativos-galicia) (un CSV por provincia: `001`, `003`, `005`, `007`) | diaria, en la página del dataset |
| La Rioja | Capa WFS [`iderioja:centros_educativos` de IDERioja](https://ogc.larioja.org/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=iderioja:centros_educativos&OUTPUTFORMAT=application/json&SRSNAME=EPSG:4326&COUNT=5) (un punto por sede, incluidas las de los CRA; 4 decimales) + código postal y centros que faltan del [Registro Estatal de Centros Docentes](https://www.educacion.gob.es/centros/) (`idComunidad=12`), geocodificados con CartoCiudad | no publicada |
| Navarra | [datosabiertos.navarra.es, "Centros educativos"](https://datosabiertos.navarra.es/es/dataset/centros-educativos) (un CSV por curso con coordenadas; el script toma el más reciente) + tipo de centro y centros que faltan del [Registro Estatal de Centros Docentes](https://www.educacion.gob.es/centros/) (`idComunidad=15`) | API CKAN `package_show` → `last_modified` del recurso |
| País Vasco | ["Centros docentes no universitarios de Euskadi" — opendata.euskadi.eus](https://opendata.euskadi.eus/catalogo/-/centros-docentes-no-universitarios-euskadi/) (CSV mensual con UTM ETRS89; los que vienen con 0,0 se geocodifican con CartoCiudad) | cabecera `Last-Modified` del CSV |
| Región de Murcia | ["Sedes de los Centros Educativos de la Región de Murcia"](https://datosabiertos.regiondemurcia.es/dataset/sedes-de-los-centros-educativos-de-la-region-de-murcia) (CKAN → API JSON del [Mapa Escolar de MurciaEduca](https://mapaescolar.murciaeduca.es/mapaescolar-api/api/centros), con coordenadas) + centros que faltan del [Registro Estatal de Centros Docentes](https://www.educacion.gob.es/centros/) (`idComunidad=14`), geocodificados con CartoCiudad | API CKAN `package_show` → `last_modified` del recurso |

El workflow [actualizar.yml](.forgejo/workflows/actualizar.yml) se ejecuta cada lunes (o a mano) en un Forgejo Runner con IP española (Galicia, Cantabria, Murcia y La Rioja bloquean IPs extranjeras). Regenera los GeoJSON y hace commit solo si alguno cambió. El repositorio de GitHub es una réplica (push mirror) del de Forgejo.

`scripts/cache/` guarda las coordenadas obtenidas con CartoCiudad por código de centro. Un centro solo se vuelve a geocodificar si es nuevo o cambia su dirección, así la ejecución semanal no repite miles de consultas. El workflow versiona también la caché.

`scripts/certs/` guarda certificados intermedios que algunos servidores no envían (catedu.es no manda el de Sectigo; mapas.ideex.es, el de FNMT); se añaden a los del sistema sin desactivar la verificación TLS.

`registro_estatal(id)` de `scripts/comun.py` descarga el listado de una comunidad del [Registro Estatal de Centros Docentes](https://www.educacion.gob.es/centros/) (código, dirección, CP y localidad, sin coordenadas). El `id` es el del buscador del Ministerio, no el del INE.

Para añadir una comunidad: crear `scripts/<comunidad>.py` usando `feature()` y `guardar()` de `scripts/comun.py`, y añadirlo al workflow.

## Referencias

Páginas consultadas para localizar cada fuente, incluidas las descartadas.

**Andalucía**
- [Directorio de centros docentes no universitarios (datos abiertos)](https://www.juntadeandalucia.es/datosabiertos/portal/dataset/directorio-de-centros-docentes-de-andalucia): fuente usada.
- [Buscador de centros educaweb](https://educaweb.juntadeandalucia.es/centros/index.asp): descartado. Sus listados por provincia son PDF sin coordenadas y su exportación CSV depende de la sesión. Los PDF sirvieron para comprobar las abreviaturas oficiales (C.E.I.P., S.E.P., C.E.PER.…).

**Aragón**
- [Centros docentes de Aragón (catedu)](https://centrosdocentes.catedu.es/ee/): fuente usada. Las abreviaturas se dedujeron de sus listados.

**Asturias**
- [Directorio de centros — educastur](https://www.educastur.es/directorio-de-centros): fuente usada.
- [SIG Asturias — capas de Educación](https://sig.asturias.es/servicios/rest/services/Visor/Educacion/MapServer/layers): coordenadas.
- [Actualización de la capa de centros (IDEAS)](https://ideas.asturias.es/en/w/update-geographic-information).
- [Ficha en datos.gob.es](https://datos.gob.es/es/catalogo/a03002951-centros-educacion-no-universitaria-asturias).

**Baleares**
- [Llistat de centres educatius de les Illes Balears](https://intranet.caib.es/sites/planificacioicentres/es/llistat_de_centres_educatius_de_les_illes_balears/): fuente usada, junto con su documento "Tipo de centros" (clave de abreviaturas).
- [IDEIB — servicio GOIB_SUPE_IB](https://ideib.caib.es/geoserveis/rest/services/public/GOIB_SUPE_IB/MapServer?f=pjson): coordenadas (capa "Equipament educatiu").
- [Centres educatius — GOIB](https://www.caib.es/webgoib/es/centres-educatius): revisado, sin datos descargables.

**Canarias**
- [Centros educativos de Canarias (datos.canarias.es)](https://datos.canarias.es/catalogos/general/dataset/centros-educativos-de-canarias/resource/b5e08adf-841b-4ba5-a599-4339e772d792): fuente usada.

**Cantabria**
- [Buscador de centros — educantabria](https://www.educantabria.es/centros/buscador-de-centros): fuente usada. Se leen los datos que la página incrusta para su mapa.

**Castilla-La Mancha**
- [Buscador de centros educativos — Consejería](https://educacion.castillalamancha.es/centros-educativos/buscador-de-centros-educativos): incrusta el buscador EDUCEN.
- [EDUCEN](https://educen.jccm.es/educen/public/consulta.xhtml): fuente usada. Su mapa solo carga capas base (CartoCiudad, IGN), no la posición de los centros.
- [Datos abiertos de Castilla-La Mancha](https://datosabiertos.castillalamancha.es) y [geoservicios de la Junta](https://geoservicios.castillalamancha.es/arcgis/rest/services): revisados, sin directorio de centros ni capa de educación. La única ficha educativa es la de la [red EDUCAL-CLM](https://datos.gob.es/es/catalogo/a08002880-centros-perteneciententes-a-la-red-educal-clm-castilla-la-mancha), que solo cubre unos pocos centros.

**Castilla y León**
- [Datos abiertos de centros docentes (educa.jcyl.es)](https://directorio.educa.jcyl.es/es/datos-abiertos-centros-docentes): fuente usada.

**Cataluña**
- [Directori de centres docents anual — Transparència Catalunya](https://analisi.transparenciacatalunya.cat/d/kvmv-ahh4): fuente usada.
- [Mapa escolar de Catalunya](https://mapaescolar.gencat.cat/): su Excel no tiene coordenadas, pero las fichas de cada centro sí; el directorio de datos abiertos las da todas de una vez.

**Comunidad de Madrid**
- [Buscador de centros educativos](https://gestiona.comunidad.madrid/wpad_pub/run/j/MostrarConsultaGeneral.icm): su exportación CSV no trae coordenadas, pero su mapa usa la capa WFS `WPAD_V_CENTROS_GIS` de la IDEM, que es la fuente usada.
- [Centros educativos de la Comunidad de Madrid (datos abiertos)](https://datos.comunidad.madrid/dataset/centros_educativos): descartado. Tiene coordenadas UTM pero se actualiza con meses de retraso (última versión: mayo de 2026).

**Comunidad Valenciana**
- [Guía de centros docentes — Conselleria](https://ceice.gva.es/es/web/centros-docentes/guia-de-centros-docentes): buscador; sus fichas enlazan al mismo registro.
- [Centros docentes de la Comunitat Valenciana (dadesobertes.gva.es)](https://dadesobertes.gva.es/dataset/edu-centros): fuente usada.
- [Capa WFS del ICV "12_Centros"](https://terramapas.icv.gva.es/12_Centros_wfs?service=WFS&request=GetCapabilities): revisada; no ofrece GeoJSON y el CSV ya trae las coordenadas.

**Extremadura**
- [Webs de centros educativos — educarex](https://www.educarex.es/consejeria/portales-centros.html): revisada; es un listado de webs de centros, sin datos.
- [Buscador de centros docentes del Ministerio (RCD)](https://www.educacion.gob.es/centros/): fuente usada.
- [IDEEX — Cartografía temática, centros educativos](https://metadatos.ideex.es/geonetwork/srv/api/records/spaJEXtmexCentrosEducativos): coordenadas (servicio `mapas.ideex.es/CICTEX/centrosEducativos`).
- [Centros educativos en Extremadura (datos.gob.es)](https://datos.gob.es/es/catalogo/a11002926-centros-educativos-en-extremadura): descartado. El [XLSX de la Junta](https://www.juntaex.es/documents/77055/5801338/Centros_educativos.xlsx) trae provincia, localidad, tipo y enseñanzas, pero no código ni dirección.

**Galicia**
- [Centros educativos de Galicia — abertos.xunta.gal](https://abertos.xunta.gal/es/catalogo/ensino-formacion/-/dataset/0257/centros-educativos-galicia): fuente usada.
- [Ficha en datos.gob.es](https://datos.gob.es/es/catalogo/a12002994-centros-educativos-de-galicia).
- [chavaone/centros-galicia-2](https://github.com/chavaone/centros-galicia-2): descartado. El repositorio no se actualiza desde 2019 y la web publicada solo incluye centros públicos.

**La Rioja**
- [Mapa de centros — educarioja](https://www.larioja.org/educarioja-centros/es/buscador-centros/mapa-centros): descartado. larioja.org (y su IDE en inspire.larioja.org) está tras una comprobación de Cloudflare que no deja acceder desde un script.
- [Servicios OGC de IDERioja](https://ogc.larioja.org/): fuente usada (capa `iderioja:centros_educativos`).
- [Metadatos "Centros educativos de La Rioja" (IDEE)](https://www.idee.es/csw-codsi-idee/srv/api/records/spacarcapaceneducativoswmstematica20141201).
- [Buscador de centros docentes del Ministerio (RCD)](https://www.educacion.gob.es/centros/): código postal y centros recientes.

**Navarra**
- [Centros educativos (datosabiertos.navarra.es)](https://datosabiertos.navarra.es/es/dataset/centros-educativos): fuente usada. Coordenadas de Google Maps y UTM de SITNA (se convierte cuando falta la primera).
- [Buscador de centros docentes del Ministerio (RCD)](https://www.educacion.gob.es/centros/): tipo de centro y unos pocos centros que no están en el CSV.

**País Vasco**
- [Centros docentes no universitarios de Euskadi (Open Data Euskadi)](https://opendata.euskadi.eus/catalogo/-/centros-docentes-no-universitarios-euskadi/): fuente usada. El tipo completo se deduce de la sigla (`DGENRC`).
- [Buscador de centros docentes del Ministerio (RCD)](https://www.educacion.gob.es/centros/): descartado como complemento; sus códigos no coinciden con los de Euskadi.

**Región de Murcia**
- [Sedes de los Centros Educativos de la Región de Murcia (datos abiertos)](https://datosabiertos.regiondemurcia.es/dataset/sedes-de-los-centros-educativos-de-la-region-de-murcia): fuente usada.
- [Buscador de centros docentes del Ministerio (RCD)](https://www.educacion.gob.es/centros/): unos 100 centros (escuelas infantiles privadas y municipales, sobre todo) que no están en la API.

**Geocodificación (CartoCiudad, IGN)**
- [CartoCiudad](https://www.cartociudad.es).
- [Documentación de la API (IDEESpain/Cartociudad)](https://github.com/IDEESpain/Cartociudad).
- [CartoCiudad ServiciosWeb (IDEE)](https://www.idee.es/resources/documentos/Cartociudad/CartoCiudad_ServiciosWeb.pdf).
- [Servicio REST de geocodificación — datos.gob.es](https://datos.gob.es/en/catalogo/e0dat0002-servicio-rest-de-geocodificacion-de-espana-cartociudad).
