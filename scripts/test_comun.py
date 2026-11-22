from comun import VIAS_CA, direccion, expandir_via, titulo

assert titulo("JOSÉ SÁNCHEZ Y SÁNCHEZ") == "José Sánchez y Sánchez"
assert titulo("LA SALLE DE LOS ÁNGELES") == "La Salle de los Ángeles"
assert titulo("ALFONSO X EL SABIO") == "Alfonso X el Sabio"
assert titulo("JUAN XXIII") == "Juan XXIII"
assert titulo("VIRGEN DEL CAMINO (LA)") == "Virgen del Camino (La)"
assert titulo("SAN JUAN DE LA CRUZ") == "San Juan de la Cruz"
assert direccion("CALLE", "SAN FRANCISCO", "25") == "Calle San Francisco, 25"
assert direccion("FINCA", "AERÓDROMO MILITAR DE LEÓN", "s/n") == "Finca Aeródromo Militar de León, S/N"
assert direccion("CALLE", "MAYOR", "") == "Calle Mayor"
assert titulo("CRA SIERRA DE PINARES") == "CRA Sierra de Pinares"
assert expandir_via("C/LAUREADO GENERAL, 14") == "Calle LAUREADO GENERAL, 14"
assert expandir_via("Avda.  Andalucía, 70") == "Avenida Andalucía, 70"
assert expandir_via("Polígo La Magdalena, s/n") == "Polígono La Magdalena, s/n"
assert expandir_via("Otros Carrera del Mami, 110") == "Carrera del Mami, 110"
assert expandir_via("Plaza Mayor") == "Plaza Mayor"
assert titulo("DE MOVERA", inicio=False) == "de Movera"
assert titulo("LA MORAÑA", inicio=False) == "La Moraña"
assert titulo("AINA MOLL I MARQUÉS", catalan=True) == "Aina Moll i Marqués"
assert titulo("ISABEL I DE CASTILLA") == "Isabel I de Castilla"
assert titulo("PALMA I") == "Palma I"
assert titulo("ESCOLA D'ART D'EIVISSA", catalan=True) == "Escola d'Art d'Eivissa"
assert expandir_via("C/ MIQUEL SANTANDREU, 48", VIAS_CA) == "Carrer MIQUEL SANTANDREU, 48"
assert titulo("C/ PERE II, 42") == "C/ Pere II, 42"
assert titulo("SANT JOSEP DE SA TALAIA", catalan=True) == "Sant Josep de sa Talaia"
from madrid import direccion as dir_mad, municipio as muni_mad
assert dir_mad("Avda de la Paz 5") == "Avenida de la Paz, 5"
assert dir_mad("Calle Mayor s/n") == "Calle Mayor, S/N"
assert dir_mad("Cmno de Casasola") == "Camino de Casasola"
assert muni_mad("Rozas de Madrid, Las") == "Las Rozas de Madrid"
from valencia import localidad
assert localidad("ALFÀS DEL PI (L')") == "L'Alfàs del Pi"
assert localidad("CAMPELLO (EL)") == "El Campello"
assert titulo("CENTRE FPA MUNICIPAL", catalan=True) == "Centre FPA Municipal"
try:  # extremadura.py necesita xlrd (requirements.txt)
    from extremadura import direccion as dir_ext, nombre as nom_ext
    assert dir_ext("C/ ERAS N.º 60") == "Calle Eras, 60"
    assert dir_ext("AV.DE LA CONSTITUCION,70") == "Avenida de la Constitucion, 70"
    assert dir_ext("PLAZA DE SANTA S/N.º") == "Plaza de Santa, S/N"
    assert nom_ext("Colegio Rural Agrupado", "C.R.A. ALMENARA") == "CRA Almenara"
    from rioja import nombre as nom_rio
    assert nom_rio("C.R.A. Las Cuatro Villas (Arrúbal)") == "CRA Las Cuatro Villas (Arrúbal)"
except ImportError:
    pass
from murcia import localidad as loc_mur, nombre as nom_mur
assert nom_mur("IES", "IES JOSÉ LUIS MARTÍNEZ PALOMO") == "IES José Luis Martínez Palomo"
assert loc_mur("PALMAR (EL) O LUGAR DE DON JUAN") == "El Palmar o Lugar de Don Juan"
from comun import normalizar_direccion, utm_a_latlon
assert utm_a_latlon(594005.88, 4712337.04) == (42.5577144, -1.8548577)  # CPEIP Larraga (SITNA vs Google)
from navarra import localidad as loc_nav, nombre as nom_nav
assert nom_nav("CPEIP Larraga S. Miguel HLHIP", "San Miguel de Larraga") == "CPEIP San Miguel de Larraga"
assert nom_nav("Ik Lizarra", "Lizarra Ikastola") == "Lizarra Ikastola"
assert loc_nav("Elizondo (Baztan)") == ("Elizondo", "Baztan")
assert normalizar_direccion("C/. ARISTÓTELES, Nº 6") == "Calle Aristóteles, 6"
from pais_vasco import direccion as dir_pv
assert dir_pv("JOSE PABLO ULLIBARRI Z/G") == "Jose Pablo Ullibarri, S/N"
print("ok")
