"""Bondi transport network data, stops, branches and schedule calculation for Gran La Plata."""

from datetime import datetime, timezone, timedelta
from typing import TypedDict, List, Optional

STOPS = {
    "stop_plaza_moreno": {
        "id": "stop_plaza_moreno",
        "name": "Plaza Moreno",
        "address": "Calle 12 y 51",
        "lat": -34.9214,
        "lon": -57.9545,
        "landmark": "Centro Cívico y Catedral de La Plata",
    },
    "stop_plaza_san_martin": {
        "id": "stop_plaza_san_martin",
        "name": "Plaza San Martín",
        "address": "Calle 7 y 50",
        "lat": -34.9142,
        "lon": -57.9498,
        "landmark": "Casa de Gobierno y Legislatura",
    },
    "stop_plaza_italia": {
        "id": "stop_plaza_italia",
        "name": "Plaza Italia",
        "address": "Calle 7 y 44",
        "lat": -34.9082,
        "lon": -57.9576,
        "landmark": "Nodo central de trasbordo comercial",
    },
    "stop_estacion_tren": {
        "id": "stop_estacion_tren",
        "name": "Estación La Plata (Línea Roca)",
        "address": "Calle 1 y 44",
        "lat": -34.9048,
        "lon": -57.9463,
        "landmark": "Tren Roca y transfer interurbano",
    },
    "stop_terminal_bus": {
        "id": "stop_terminal_bus",
        "name": "Terminal de Ómnibus",
        "address": "Calle 4 y 42",
        "lat": -34.9031,
        "lon": -57.9507,
        "landmark": "Salidas de larga y media distancia",
    },
    "stop_plaza_rocha": {
        "id": "stop_plaza_rocha",
        "name": "Plaza Rocha",
        "address": "Calle 7 y 60",
        "lat": -34.9248,
        "lon": -57.9419,
        "landmark": "Biblioteca de la UNLP",
    },
    "stop_plaza_paso": {
        "id": "stop_plaza_paso",
        "name": "Plaza Paso",
        "address": "Calle 13 y 44",
        "lat": -34.9155,
        "lon": -57.9652,
        "landmark": "Eje diagonal 74 hacia Gonnet",
    },
    "stop_hosp_ninos": {
        "id": "stop_hosp_ninos",
        "name": "Hospital de Niños",
        "address": "Calle 14 y 66",
        "lat": -34.9351,
        "lon": -57.9462,
        "landmark": "Hospital Sor María Ludovica",
    },
    "stop_hosp_san_martin": {
        "id": "stop_hosp_san_martin",
        "name": "Hospital Policlínico San Martín",
        "address": "Calle 1 y 70",
        "lat": -34.9221,
        "lon": -57.9254,
        "landmark": "Centro de salud provincial",
    },
    "stop_hosp_san_juan": {
        "id": "stop_hosp_san_juan",
        "name": "Hospital San Juan de Dios",
        "address": "Calle 27 y 70",
        "lat": -34.9427,
        "lon": -57.9490,
        "landmark": "Especialidades médicas y guardias",
    },
    "stop_hosp_espanol": {
        "id": "stop_hosp_espanol",
        "name": "Hospital Español",
        "address": "Calle 9 y 36",
        "lat": -34.9002,
        "lon": -57.9620,
        "landmark": "Barrio Norte / Clínicas",
    },
    "stop_estadio_unico": {
        "id": "stop_estadio_unico",
        "name": "Estadio Diego Armando Maradona",
        "address": "Av. 25 y 32",
        "lat": -34.9001,
        "lon": -57.9892,
        "landmark": "Estadio Ciudad de La Plata",
    },
    "stop_cementerio": {
        "id": "stop_cementerio",
        "name": "Cementerio La Plata",
        "address": "Calle 31 y 72",
        "lat": -34.9526,
        "lon": -57.9622,
        "landmark": "Cabecera sudoeste y acceso circunvalación",
    },
    "stop_los_hornos_60": {
        "id": "stop_los_hornos_60",
        "name": "Los Hornos (Centro)",
        "address": "Av. 60 y 137",
        "lat": -34.9548,
        "lon": -57.9942,
        "landmark": "Centro comercial Los Hornos",
    },
    "stop_los_hornos_66": {
        "id": "stop_los_hornos_66",
        "name": "Los Hornos (Sur)",
        "address": "Av. 66 y 143",
        "lat": -34.9691,
        "lon": -58.0062,
        "landmark": "Acceso a barrios del sur",
    },
    "stop_san_carlos": {
        "id": "stop_san_carlos",
        "name": "San Carlos",
        "address": "Av. 32 y 137",
        "lat": -34.9282,
        "lon": -58.0142,
        "landmark": "Centro barrial San Carlos",
    },
    "stop_melchor_romero": {
        "id": "stop_melchor_romero",
        "name": "Melchor Romero",
        "address": "Av. 520 y 173",
        "lat": -34.9452,
        "lon": -58.0640,
        "landmark": "Hospital Dr. Alejandro Korn",
    },
    "stop_tolosa": {
        "id": "stop_tolosa",
        "name": "Tolosa",
        "address": "Calle 7 y 528",
        "lat": -34.8872,
        "lon": -57.9732,
        "landmark": "Plaza Martín Iraola / Tolosa Centro",
    },
    "stop_rep_ninos": {
        "id": "stop_rep_ninos",
        "name": "República de los Niños",
        "address": "Cno. General Belgrano y 500",
        "lat": -34.8835,
        "lon": -57.9982,
        "landmark": "Parque temático y recreativo Gonnet",
    },
    "stop_gonnet": {
        "id": "stop_gonnet",
        "name": "Estación Gonnet",
        "address": "Cno. Centenario y 502",
        "lat": -34.8802,
        "lon": -57.9904,
        "landmark": "Tren Roca y centros comerciales",
    },
    "stop_city_bell": {
        "id": "stop_city_bell",
        "name": "Estación City Bell",
        "address": "Cno. Centenario y Cantilo (461)",
        "lat": -34.8621,
        "lon": -58.0163,
        "landmark": "Centro gastronómico y comercial City Bell",
    },
    "stop_villa_elisa": {
        "id": "stop_villa_elisa",
        "name": "Villa Elisa (Centro)",
        "address": "Cno. Centenario y Arana (419)",
        "lat": -34.8482,
        "lon": -58.0381,
        "landmark": "Estación Villa Elisa y Parque Ecológico",
    },
    "stop_berisso_puente_roma": {
        "id": "stop_berisso_puente_roma",
        "name": "Berisso - Puente Roma",
        "address": "Av. Génova y 158",
        "lat": -34.8722,
        "lon": -57.8862,
        "landmark": "Acceso principal a Berisso",
    },
    "stop_berisso_centro": {
        "id": "stop_berisso_centro",
        "name": "Berisso Centro",
        "address": "Av. Montevideo y 11",
        "lat": -34.8785,
        "lon": -57.8761,
        "landmark": "Parque Cívico de Berisso",
    },
    "stop_berisso_los_talas": {
        "id": "stop_berisso_los_talas",
        "name": "Berisso - Los Talas",
        "address": "Av. Montevideo y 30",
        "lat": -34.8992,
        "lon": -57.8480,
        "landmark": "Balneario y zona costera",
    },
    "stop_ensenada_centro": {
        "id": "stop_ensenada_centro",
        "name": "Ensenada - Plaza Belgrano",
        "address": "Don Bosco y La Merced",
        "lat": -34.8601,
        "lon": -57.9102,
        "landmark": "Municipalidad y centro de Ensenada",
    },
    "stop_ensenada_astillero": {
        "id": "stop_ensenada_astillero",
        "name": "Ensenada - Astillero",
        "address": "Av. Horacio Cestino y Río Santiago",
        "lat": -34.8512,
        "lon": -57.9021,
        "landmark": "Astillero Río Santiago / Zona Franca",
    },
    "stop_villa_elvira": {
        "id": "stop_villa_elvira",
        "name": "Villa Elvira",
        "address": "Calle 7 y 80",
        "lat": -34.9392,
        "lon": -57.9281,
        "landmark": "Acceso sudeste",
    },
    "stop_sicardi": {
        "id": "stop_sicardi",
        "name": "Parque Sicardi",
        "address": "Calle 659 y 22",
        "lat": -34.9921,
        "lon": -57.8862,
        "landmark": "Zona residencial Sicardi / Arana",
    },
    "stop_unlp_bosque": {
        "id": "stop_unlp_bosque",
        "name": "UNLP - Facultades Bosque Central",
        "address": "Av. 1 y 50",
        "lat": -34.9082,
        "lon": -57.9412,
        "landmark": "Facultad de Ciencias Exactas y Museo",
    },
    "stop_unlp_informatica": {
        "id": "stop_unlp_informatica",
        "name": "UNLP - Informática / Naturales",
        "address": "Calle 120 y 52",
        "lat": -34.9061,
        "lon": -57.9302,
        "landmark": "Polo universitario Bosque Este",
    },
    "stop_unlp_medicina": {
        "id": "stop_unlp_medicina",
        "name": "UNLP - Medicina / Periodismo",
        "address": "Calle 60 y 120",
        "lat": -34.9123,
        "lon": -57.9242,
        "landmark": "Facultades de Cs. Médicas, Odontología, Periodismo",
    },
    "stop_rotonda_autopista": {
        "id": "stop_rotonda_autopista",
        "name": "Rotonda Autopista La Plata-BsAs",
        "address": "Av. 120 y 32",
        "lat": -34.8912,
        "lon": -57.9442,
        "landmark": "Ingreso y egreso Autopista Dr. Balbín",
    },
}

LINES = [
    {
        "id": "506",
        "name": "506",
        "type": "comunal",
        "company": "Fuerte Barragán S.A.T.",
        "color": "#18382B",
        "headsign": "Los Hornos ↔ Ensenada por Plaza Moreno",
        "frequency_min": 10,
        "stops": [
            "stop_los_hornos_60",
            "stop_cementerio",
            "stop_plaza_moreno",
            "stop_plaza_san_martin",
            "stop_estacion_tren",
            "stop_ensenada_centro",
        ],
    },
    {
        "id": "518",
        "name": "518",
        "type": "comunal",
        "company": "Fuerte Barragán S.A.T.",
        "color": "#2E7D32",
        "headsign": "Aeropuerto ↔ Rep. de los Niños por Pza. Italia",
        "frequency_min": 12,
        "stops": [
            "stop_plaza_rocha",
            "stop_plaza_italia",
            "stop_tolosa",
            "stop_rep_ninos",
        ],
    },
    {
        "id": "520",
        "name": "520",
        "type": "comunal",
        "company": "Unión Platense S.R.L.",
        "color": "#388E3C",
        "headsign": "Parque Sicardi ↔ Estación por Los Hornos",
        "frequency_min": 15,
        "stops": [
            "stop_sicardi",
            "stop_villa_elvira",
            "stop_los_hornos_60",
            "stop_plaza_rocha",
            "stop_plaza_san_martin",
            "stop_estacion_tren",
        ],
    },
    {
        "id": "561",
        "name": "561",
        "type": "comunal",
        "company": "Empresa Línea 7 S.A.T.",
        "color": "#43A047",
        "headsign": "San Carlos ↔ Estación por Estadio Único",
        "frequency_min": 12,
        "stops": [
            "stop_san_carlos",
            "stop_estadio_unico",
            "stop_plaza_paso",
            "stop_plaza_moreno",
            "stop_estacion_tren",
        ],
    },
    {
        "id": "este",
        "name": "Este",
        "type": "comunal",
        "company": "Expreso La Plata Buenos Aires S.A.",
        "color": "#1B5E20",
        "headsign": "Villa Elvira ↔ Plaza Italia por Policlínico",
        "frequency_min": 8,
        "stops": [
            "stop_villa_elvira",
            "stop_hosp_san_martin",
            "stop_unlp_bosque",
            "stop_plaza_san_martin",
            "stop_plaza_italia",
        ],
    },
    {
        "id": "oeste",
        "name": "Oeste",
        "type": "comunal",
        "company": "Empresa Línea 7 S.A.T.",
        "color": "#00796B",
        "headsign": "Melchor Romero ↔ Estación por Hosp. Español",
        "frequency_min": 10,
        "stops": [
            "stop_melchor_romero",
            "stop_san_carlos",
            "stop_hosp_espanol",
            "stop_plaza_italia",
            "stop_estacion_tren",
        ],
    },
    {
        "id": "norte",
        "name": "Norte",
        "type": "comunal",
        "company": "Unión Platense S.R.L.",
        "color": "#004D40",
        "headsign": "City Bell ↔ Plaza Moreno por Gonnet",
        "frequency_min": 10,
        "stops": [
            "stop_city_bell",
            "stop_gonnet",
            "stop_rep_ninos",
            "stop_tolosa",
            "stop_plaza_italia",
            "stop_plaza_moreno",
        ],
    },
    {
        "id": "sur",
        "name": "Sur",
        "type": "comunal",
        "company": "Unión Platense S.R.L.",
        "color": "#00897B",
        "headsign": "Los Hornos ↔ Plaza Italia por Hospitales",
        "frequency_min": 10,
        "stops": [
            "stop_los_hornos_66",
            "stop_hosp_san_juan",
            "stop_hosp_ninos",
            "stop_plaza_moreno",
            "stop_plaza_italia",
        ],
    },
    {
        "id": "273",
        "name": "273",
        "type": "provincial",
        "company": "Unión Platense S.R.L.",
        "color": "#1565C0",
        "headsign": "Villa Elisa ↔ Cementerio por City Bell",
        "frequency_min": 8,
        "stops": [
            "stop_villa_elisa",
            "stop_city_bell",
            "stop_gonnet",
            "stop_plaza_italia",
            "stop_plaza_moreno",
            "stop_cementerio",
        ],
    },
    {
        "id": "275",
        "name": "275",
        "type": "provincial",
        "company": "Fuerte Barragán S.A.T.",
        "color": "#0D47A1",
        "headsign": "Astillero Río Santiago ↔ Plaza San Martín",
        "frequency_min": 15,
        "stops": [
            "stop_ensenada_astillero",
            "stop_ensenada_centro",
            "stop_estacion_tren",
            "stop_plaza_san_martin",
        ],
    },
    {
        "id": "214",
        "name": "214",
        "type": "provincial",
        "company": "Unión Platense S.R.L.",
        "color": "#1976D2",
        "headsign": "Berisso Los Talas ↔ Hospital San Juan de Dios",
        "frequency_min": 10,
        "stops": [
            "stop_berisso_los_talas",
            "stop_berisso_centro",
            "stop_berisso_puente_roma",
            "stop_plaza_san_martin",
            "stop_hosp_ninos",
            "stop_hosp_san_juan",
        ],
    },
    {
        "id": "307",
        "name": "307",
        "type": "provincial",
        "company": "Empresa Línea 7 S.A.T.",
        "color": "#0277BD",
        "headsign": "Río Santiago ↔ Cementerio por Estación",
        "frequency_min": 10,
        "stops": [
            "stop_ensenada_astillero",
            "stop_ensenada_centro",
            "stop_estacion_tren",
            "stop_plaza_moreno",
            "stop_cementerio",
        ],
    },
    {
        "id": "202",
        "name": "202",
        "type": "provincial",
        "company": "La Unión S.A.",
        "color": "#0288D1",
        "headsign": "Berisso Centro ↔ Estación La Plata",
        "frequency_min": 12,
        "stops": [
            "stop_berisso_centro",
            "stop_berisso_puente_roma",
            "stop_unlp_medicina",
            "stop_estacion_tren",
        ],
    },
    {
        "id": "215",
        "name": "215",
        "type": "provincial",
        "company": "Nueve de Julio S.A.T.",
        "color": "#039BE5",
        "headsign": "Tolosa ↔ Melchor Romero por San Carlos",
        "frequency_min": 15,
        "stops": [
            "stop_tolosa",
            "stop_estacion_tren",
            "stop_plaza_san_martin",
            "stop_san_carlos",
            "stop_melchor_romero",
        ],
    },
    {
        "id": "418",
        "name": "418",
        "type": "provincial",
        "company": "Unión Platense S.R.L.",
        "color": "#00838F",
        "headsign": "Berazategui ↔ Terminal La Plata por Cno. Centenario",
        "frequency_min": 20,
        "stops": [
            "stop_villa_elisa",
            "stop_city_bell",
            "stop_gonnet",
            "stop_terminal_bus",
        ],
    },
    {
        "id": "414",
        "name": "414",
        "type": "provincial",
        "company": "Nueve de Julio S.A.T.",
        "color": "#29B6F6",
        "headsign": "Florencio Varela ↔ Terminal La Plata",
        "frequency_min": 20,
        "stops": [
            "stop_estacion_tren",
            "stop_terminal_bus",
        ],
    },
    {
        "id": "129",
        "name": "129",
        "type": "provincial",
        "company": "Misión Buenos Aires",
        "color": "#D84315",
        "headsign": "CABA Retiro ↔ La Plata por Autopista",
        "frequency_min": 15,
        "stops": [
            "stop_rotonda_autopista",
            "stop_terminal_bus",
            "stop_plaza_italia",
        ],
    },
    {
        "id": "195",
        "name": "195",
        "type": "provincial",
        "company": "Costera Metropolitana",
        "color": "#C2185B",
        "headsign": "CABA Retiro ↔ Terminal y Plaza San Martín",
        "frequency_min": 15,
        "stops": [
            "stop_rotonda_autopista",
            "stop_terminal_bus",
            "stop_plaza_san_martin",
        ],
    },
    {
        "id": "unlp",
        "name": "Rondín UNLP",
        "type": "especial",
        "company": "Universidad Nacional de La Plata",
        "color": "#E65100",
        "headsign": "Circuito Facultades del Bosque UNLP",
        "frequency_min": 12,
        "stops": [
            "stop_plaza_rocha",
            "stop_plaza_san_martin",
            "stop_unlp_bosque",
            "stop_unlp_informatica",
            "stop_unlp_medicina",
        ],
    },
]

# Precompute mapping of stop_id -> list of lines passing through it
STOP_LINES = {}
for line in LINES:
    for stop_id in line["stops"]:
        if stop_id not in STOP_LINES:
            STOP_LINES[stop_id] = []
        STOP_LINES[stop_id].append({
            "id": line["id"],
            "name": line["name"],
            "type": line["type"],
            "color": line["color"],
            "headsign": line["headsign"],
            "frequency_min": line["frequency_min"],
        })


def get_all_stops():
    """Return all stops enhanced with the list of lines serving them."""
    result = []
    for sid, stop in STOPS.items():
        lines_here = STOP_LINES.get(sid, [])
        result.append({
            **stop,
            "lines": lines_here,
            "line_count": len(lines_here),
        })
    return sorted(result, key=lambda s: s["name"])


def get_stop_by_id(stop_id: str):
    """Return a stop by ID or None."""
    if stop_id not in STOPS:
        return None
    stop = STOPS[stop_id]
    lines_here = STOP_LINES.get(stop_id, [])
    return {
        **stop,
        "lines": lines_here,
        "line_count": len(lines_here),
    }


def calculate_arrivals(stop_id: str, ref_time: Optional[datetime] = None) -> List[dict]:
    """
    Calculate upcoming bus arrivals for a given stop.
    Returns sorted list of upcoming arrivals with scheduled_time and eta_seconds.
    """
    if stop_id not in STOPS:
        return []

    # Current time in Buenos Aires timezone (UTC-3)
    tz_ba = timezone(timedelta(hours=-3))
    now = ref_time or datetime.now(tz_ba)

    current_minutes = now.hour * 60 + now.minute
    current_seconds = now.second

    arrivals = []
    lines_at_stop = [l for l in LINES if stop_id in l["stops"]]

    for line in lines_at_stop:
        freq = line["frequency_min"]
        stop_seq = line["stops"].index(stop_id)
        # Offset in minutes based on stop sequence (travel time along the line)
        offset = (stop_seq * 3 + int(line["id"].encode("utf-8").hex(), 16) % 7) % freq

        # Find the next 3 departures for this line passing this stop
        for k in range(-1, 5):
            candidate_min = ((current_minutes // freq) + k) * freq + offset
            diff_min = candidate_min - current_minutes
            eta_sec = diff_min * 60 - current_seconds

            # We accept arrivals that are within the next 45 minutes and not in the far past
            if -30 <= eta_sec <= 2700:
                arrival_time = now + timedelta(seconds=eta_sec)
                arrivals.append({
                    "line_id": line["id"],
                    "line_name": line["name"],
                    "line_type": line["type"],
                    "line_color": line["color"],
                    "headsign": line["headsign"],
                    "scheduled_time": arrival_time.strftime("%H:%M"),
                    "eta_seconds": max(0, int(eta_sec)),
                    "eta_minutes": max(0, int(eta_sec // 60)),
                    "status": "arriving" if eta_sec < 60 else "scheduled",
                })

    # Sort arrivals chronologically by eta_seconds
    arrivals.sort(key=lambda a: a["eta_seconds"])
    return arrivals[:10]
