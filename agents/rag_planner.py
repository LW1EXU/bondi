"""Subagente RAG de Viaje para Gran La Plata.

Resuelve consultas en lenguaje natural ("cómo voy de 7 y 50 a la facultad de informática"),
interpreta nomenclatura platense (intersecciones de cuadrícula, diagonales, caminos y POIs),
calcula recorridos óptimos (directos y con transbordo) y genera instrucciones paso a paso.
"""

import json
import math
import os
import re
from typing import Literal, Optional
from pydantic import BaseModel, Field

from backend.app.transport_data import STOPS, LINES
from agents.normalizer import canonicalize


class TripLeg(BaseModel):
    kind: Literal["walk", "transit"]
    instruction: str
    line_id: Optional[str] = None
    line_name: Optional[str] = None
    headsign: Optional[str] = None
    color: Optional[str] = None
    from_stop_id: Optional[str] = None
    from_stop_name: Optional[str] = None
    to_stop_id: Optional[str] = None
    to_stop_name: Optional[str] = None
    duration_minutes: int
    distance_meters: int
    intermediate_stops: list[str] = Field(default_factory=list)


class TripPlan(BaseModel):
    origin: str
    destination: str
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    transfers: int
    total_duration_minutes: int
    walking_meters: int
    legs: list[TripLeg]
    summary_text: str
    direct: bool


class ExtractedPoints(BaseModel):
    origin: str
    destination: str


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia en metros entre dos coordenadas geográficas."""
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


# Platense grid reference points for geocoding
# La Plata center (Plaza Moreno): -34.9214, -57.9545
# Calle 50 y Calle 7: -34.9142, -57.9498
# Intersección de cuadrícula aproximada:
# Calle 1: lon ~ -57.935, Calle 31: lon ~ -57.965
# Calle 32: lat ~ -34.895, Calle 72: lat ~ -34.945
KNOWN_PLATENSE_POIS = {
    "plaza moreno": (-34.9214, -57.9545, "Plaza Moreno (12 y 51)"),
    "catedral": (-34.9214, -57.9545, "Catedral de La Plata (Plaza Moreno)"),
    "plaza san martin": (-34.9142, -57.9498, "Plaza San Martín (7 y 50)"),
    "gobernacion": (-34.9142, -57.9498, "Casa de Gobierno (7 y 50)"),
    "legislatura": (-34.9142, -57.9498, "Legislatura Provincial (7 y 50)"),
    "plaza italia": (-34.9082, -57.9576, "Plaza Italia (7 y 44)"),
    "estacion": (-34.9048, -57.9463, "Estación La Plata Ferrocarril Roca (1 y 44)"),
    "estacion la plata": (-34.9048, -57.9463, "Estación La Plata Ferrocarril Roca (1 y 44)"),
    "tren roca": (-34.9048, -57.9463, "Estación La Plata (1 y 44)"),
    "terminal": (-34.9031, -57.9507, "Terminal de Ómnibus de La Plata (4 y 42)"),
    "terminal de omnibus": (-34.9031, -57.9507, "Terminal de Ómnibus (4 y 42)"),
    "plaza rocha": (-34.9248, -57.9419, "Plaza Rocha (7 y 60)"),
    "plaza paso": (-34.9155, -57.9652, "Plaza Paso (13 y 44)"),
    "hospital de ninos": (-34.9351, -57.9462, "Hospital de Niños Sor María Ludovica (14 y 66)"),
    "hospital ninos": (-34.9351, -57.9462, "Hospital de Niños (14 y 66)"),
    "sor maria ludovica": (-34.9351, -57.9462, "Hospital Sor María Ludovica (14 y 66)"),
    "policlinico": (-34.9221, -57.9254, "Hospital Policlínico San Martín (1 y 70)"),
    "hospital san martin": (-34.9221, -57.9254, "Hospital Policlínico San Martín (1 y 70)"),
    "hospital san juan de dios": (-34.9427, -57.9490, "Hospital San Juan de Dios (27 y 70)"),
    "san juan de dios": (-34.9427, -57.9490, "Hospital San Juan de Dios (27 y 70)"),
    "hospital espanol": (-34.9002, -57.9620, "Hospital Español (9 y 36)"),
    "estadio unico": (-34.9001, -57.9892, "Estadio Diego Armando Maradona (25 y 32)"),
    "estadio maradona": (-34.9001, -57.9892, "Estadio Único (25 y 32)"),
    "cementerio": (-34.9526, -57.9622, "Cementerio Municipal de La Plata (31 y 72)"),
    "los hornos": (-34.9548, -57.9942, "Los Hornos (60 y 137)"),
    "san carlos": (-34.9282, -58.0142, "San Carlos (32 y 137)"),
    "melchor romero": (-34.9452, -58.0640, "Melchor Romero (520 y 173)"),
    "romero": (-34.9452, -58.0640, "Melchor Romero (520 y 173)"),
    "tolosa": (-34.8872, -57.9732, "Tolosa (7 y 528)"),
    "republica de los ninos": (-34.8835, -57.9982, "República de los Niños (Cno. Belgrano y 500)"),
    "gonnet": (-34.8802, -57.9904, "Gonnet (Cno. Centenario y 502)"),
    "city bell": (-34.8621, -58.0163, "Estación City Bell (Centenario y Cantilo)"),
    "villa elisa": (-34.8482, -58.0381, "Villa Elisa (Centenario y Arana)"),
    "berisso": (-34.8785, -57.8761, "Berisso Centro (Av. Montevideo y 11)"),
    "ensenada": (-34.8601, -57.9102, "Ensenada Centro (Plaza Belgrano)"),
    "astillero": (-34.8512, -57.9021, "Astillero Río Santiago"),
    "rio santiago": (-34.8512, -57.9021, "Astillero Río Santiago"),
    "villa elvira": (-34.9392, -57.9281, "Villa Elvira (7 y 80)"),
    "parque sicardi": (-34.9921, -57.8862, "Parque Sicardi (659 y 22)"),
    "sicardi": (-34.9921, -57.8862, "Parque Sicardi"),
    "facultad de informatica": (-34.9061, -57.9302, "Facultad de Informática UNLP (120 y 52)"),
    "informatica": (-34.9061, -57.9302, "Facultad de Informática UNLP (120 y 52)"),
    "facultad de naturales": (-34.9061, -57.9302, "Facultad de Ciencias Naturales y Museo UNLP (120 y 52)"),
    "facultad de medicina": (-34.9123, -57.9242, "Facultad de Medicina UNLP (60 y 120)"),
    "medicina": (-34.9123, -57.9242, "Facultad de Medicina UNLP (60 y 120)"),
    "facultades bosque": (-34.9082, -57.9412, "Facultades del Bosque (1 y 50)"),
    "museo de la plata": (-34.9082, -57.9412, "Museo de La Plata (Paseo del Bosque)"),
    "bosque": (-34.9082, -57.9412, "Paseo del Bosque UNLP (1 y 50)"),
}


def geocode_platense(text: str) -> tuple[float, float, str]:
    """Interpreta direcciones platenses numéricas (e.g. '7 y 50', '60 y 137') y puntos conocidos."""
    raw = canonicalize(text)

    # Check known POIs first
    for key, (lat, lon, label) in KNOWN_PLATENSE_POIS.items():
        if key in raw or raw in key:
            return lat, lon, label

    # Check stop names in transport_data
    for stop_id, s in STOPS.items():
        if canonicalize(s["name"]) in raw or raw in canonicalize(s["name"]):
            return s["lat"], s["lon"], s["name"]
        if canonicalize(s["address"]) in raw:
            return s["lat"], s["lon"], f"{s['name']} ({s['address']})"

    # Match numeric Platense intersection "X y Y" or "calle X y calle Y"
    # Example "7 y 50", "12 y 51", "1 y 44", "60 y 137", "32 y 137"
    match = re.search(r"\b(\d+)\s+y\s+(\d+)\b", raw)
    if match:
        n1, n2 = int(match.group(1)), int(match.group(2))
        # In La Plata casco:
        # Avenues/calles numbered 1 to 31 generally run SE-NW or SW-NE.
        # Calles 32 to 72 run perpendicular.
        # If one number is <= 31 and the other is between 32 and 72:
        calle_col, calle_row = (n1, n2) if n1 < n2 else (n2, n1)

        # Base reference: 1 y 32 is roughly -34.8950, -57.9360
        # 1 y 72 is roughly -34.9350, -57.9220
        # 31 y 32 is roughly -34.9120, -58.0050
        # 31 y 72 is roughly -34.9526, -57.9622
        # Center: 12 y 51 is -34.9214, -57.9545
        # Each block is approx 130m.
        # Lat step per block row (dlat from 32 to 72 = 40 blocks, ~0.045 lat -> ~0.00112 per block)
        # Lon step per col (dlon from 1 to 31 = 30 blocks, ~0.045 lon -> ~0.00150 per block)
        if 1 <= calle_col <= 32 and 32 <= calle_row <= 72:
            lat = -34.9214 + (calle_row - 51) * 0.00110 + (calle_col - 12) * 0.00035
            lon = -57.9545 - (calle_col - 12) * 0.00140 - (calle_row - 51) * 0.00030
            return round(lat, 5), round(lon, 5), f"Calle {n1} y Calle {n2}"

        # Outer Hornos / San Carlos (e.g. 60 y 137, 66 y 143, 32 y 137)
        if calle_row > 100 or calle_col > 100:
            high = max(n1, n2)
            low = min(n1, n2)
            if high in (137, 143, 149, 155):
                lat = -34.9548 + (low - 60) * 0.00120
                lon = -57.9942 - (high - 137) * 0.00200
                return round(lat, 5), round(lon, 5), f"Calle {low} y Calle {high}"

    # Default fallback: Center Plaza San Martín
    return -34.9142, -57.9498, text.strip()


def find_closest_stops(lat: float, lon: float, limit: int = 4) -> list[tuple[dict, float]]:
    """Encuentra las paradas más cercanas a una coordenada dada."""
    scored = []
    for stop_id, stop in STOPS.items():
        d = haversine_m(lat, lon, stop["lat"], stop["lon"])
        scored.append((stop, d))
    scored.sort(key=lambda x: x[1])
    return scored[:limit]


def plan_trip(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    origin_name: str = "Origen",
    dest_name: str = "Destino",
) -> TripPlan:
    """Calcula la mejor combinación de transporte público para Gran La Plata."""
    origin_stops = find_closest_stops(origin_lat, origin_lon, limit=4)
    dest_stops = find_closest_stops(dest_lat, dest_lon, limit=4)

    # 1. Evaluate direct routes
    best_direct: Optional[tuple[float, dict, dict, dict, float, float]] = None

    for o_stop, o_dist in origin_stops:
        for d_stop, d_dist in dest_stops:
            if o_stop["id"] == d_stop["id"]:
                continue
            for line in LINES:
                stops_in_line = line["stops"]
                if o_stop["id"] in stops_in_line and d_stop["id"] in stops_in_line:
                    idx_o = stops_in_line.index(o_stop["id"])
                    idx_d = stops_in_line.index(d_stop["id"])
                    hops = abs(idx_d - idx_o)
                    walk_o_min = o_dist / 75.0
                    wait_min = line.get("frequencyMin", 10) / 2.0
                    ride_min = hops * 3.5
                    walk_d_min = d_dist / 75.0
                    walk_penalty = 0.0
                    if o_dist > 800:
                        walk_penalty += (o_dist - 800) / 10.0
                    if d_dist > 800:
                        walk_penalty += (d_dist - 800) / 10.0
                    score = walk_o_min + wait_min + ride_min + walk_d_min + walk_penalty

                    if best_direct is None or score < best_direct[0]:
                        best_direct = (score, line, o_stop, d_stop, o_dist, d_dist)

    # 2. Evaluate 1-transfer routes
    best_transfer: Optional[tuple[float, dict, dict, dict, dict, dict, float, float, int, int]] = None

    for o_stop, o_dist in origin_stops:
        for d_stop, d_dist in dest_stops:
            if o_stop["id"] == d_stop["id"]:
                continue
            # Find lines serving origin
            origin_lines = [l for l in LINES if o_stop["id"] in l["stops"]]
            # Find lines serving destination
            dest_lines = [l for l in LINES if d_stop["id"] in l["stops"]]

            for l1 in origin_lines:
                for l2 in dest_lines:
                    if l1["id"] == l2["id"]:
                        continue
                    # Find common transfer stops between l1 and l2
                    common_stop_ids = set(l1["stops"]) & set(l2["stops"])
                    for hub_id in common_stop_ids:
                        if hub_id in (o_stop["id"], d_stop["id"]):
                            continue
                        hub = STOPS[hub_id]
                        idx_o = l1["stops"].index(o_stop["id"])
                        idx_h1 = l1["stops"].index(hub_id)
                        idx_h2 = l2["stops"].index(hub_id)
                        idx_d = l2["stops"].index(d_stop["id"])

                        hops1 = abs(idx_h1 - idx_o)
                        hops2 = abs(idx_d - idx_h2)
                        walk_o_min = o_dist / 75.0
                        wait1_min = l1.get("frequencyMin", 10) / 2.0
                        ride1_min = hops1 * 3.5
                        transfer_wait = 4.0 + (l2.get("frequencyMin", 10) / 2.0)
                        ride2_min = hops2 * 3.5
                        walk_d_min = d_dist / 75.0

                        walk_penalty = 0.0
                        if o_dist > 800:
                            walk_penalty += (o_dist - 800) / 10.0
                        if d_dist > 800:
                            walk_penalty += (d_dist - 800) / 10.0

                        score = walk_o_min + wait1_min + ride1_min + transfer_wait + ride2_min + walk_d_min + walk_penalty

                        if best_transfer is None or score < best_transfer[0]:
                            best_transfer = (score, l1, l2, o_stop, hub, d_stop, o_dist, d_dist, hops1, hops2)

    # If best_transfer has lower score than best_direct, or if best_direct required excessive walking (>1500m)
    use_transfer = False
    if best_transfer:
        if best_direct is None:
            use_transfer = True
        elif best_transfer[0] < best_direct[0] - 3.0:
            use_transfer = True
        elif (best_direct[4] + best_direct[5]) > 2000 and (best_transfer[6] + best_transfer[7]) < 1200:
            use_transfer = True

    if not use_transfer and best_direct:
        _, line, o_stop, d_stop, o_dist, d_dist = best_direct
        stops_in_line = line["stops"]
        idx_o = stops_in_line.index(o_stop["id"])
        idx_d = stops_in_line.index(d_stop["id"])
        inter = [STOPS[s]["name"] for s in stops_in_line[idx_o + 1:idx_d]]

        walk_o_min = max(1, int(round(o_dist / 75.0)))
        wait_min = int(round(line.get("frequencyMin", 10) / 2.0))
        ride_min = max(3, int(round((idx_d - idx_o) * 3.5)))
        walk_d_min = max(1, int(round(d_dist / 75.0)))
        total_duration = walk_o_min + wait_min + ride_min + walk_d_min

        legs = [
            TripLeg(
                kind="walk",
                instruction=f"Caminá {int(o_dist)} metros desde {origin_name} hasta la parada {o_stop['name']}",
                from_stop_name=origin_name,
                to_stop_id=o_stop["id"],
                to_stop_name=o_stop["name"],
                duration_minutes=walk_o_min,
                distance_meters=int(o_dist),
            ),
            TripLeg(
                kind="transit",
                instruction=f"Tomá la Línea {line['name']} (hacia {line['headsign']}) en {o_stop['name']} y viajá hasta {d_stop['name']}",
                line_id=line["id"],
                line_name=line["name"],
                headsign=line["headsign"],
                color=line.get("color"),
                from_stop_id=o_stop["id"],
                from_stop_name=o_stop["name"],
                to_stop_id=d_stop["id"],
                to_stop_name=d_stop["name"],
                duration_minutes=ride_min,
                distance_meters=int((idx_d - idx_o) * 1200),
                intermediate_stops=inter,
            ),
            TripLeg(
                kind="walk",
                instruction=f"Bajate en {d_stop['name']} y caminá {int(d_dist)} metros hasta {dest_name}",
                from_stop_id=d_stop["id"],
                from_stop_name=d_stop["name"],
                to_stop_name=dest_name,
                duration_minutes=walk_d_min,
                distance_meters=int(d_dist),
            ),
        ]

        summary = (
            f"Viaje directo en Línea {line['name']}: caminá {int(o_dist)}m a {o_stop['name']}, "
            f"viajá {ride_min} min en el micro hasta {d_stop['name']} y caminá {int(d_dist)}m a {dest_name}. "
            f"Tiempo estimado total: {total_duration} minutos."
        )

        return TripPlan(
            origin=origin_name,
            destination=dest_name,
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            destination_lat=dest_lat,
            destination_lon=dest_lon,
            transfers=0,
            total_duration_minutes=total_duration,
            walking_meters=int(o_dist + d_dist),
            legs=legs,
            summary_text=summary,
            direct=True,
        )

    if best_transfer:
        _, l1, l2, o_stop, hub, d_stop, o_dist, d_dist, hops1, hops2 = best_transfer
        walk_o_min = max(1, int(round(o_dist / 75.0)))
        ride1_min = max(3, int(round(hops1 * 3.5)))
        ride2_min = max(3, int(round(hops2 * 3.5)))
        walk_d_min = max(1, int(round(d_dist / 75.0)))
        total_duration = int(walk_o_min + ride1_min + 5 + ride2_min + walk_d_min)

        legs = [
            TripLeg(
                kind="walk",
                instruction=f"Caminá {int(o_dist)}m hasta {o_stop['name']}",
                from_stop_name=origin_name,
                to_stop_id=o_stop["id"],
                to_stop_name=o_stop["name"],
                duration_minutes=walk_o_min,
                distance_meters=int(o_dist),
            ),
            TripLeg(
                kind="transit",
                instruction=f"Tomá la Línea {l1['name']} hasta {hub['name']}",
                line_id=l1["id"],
                line_name=l1["name"],
                headsign=l1["headsign"],
                color=l1.get("color"),
                from_stop_id=o_stop["id"],
                from_stop_name=o_stop["name"],
                to_stop_id=hub["id"],
                to_stop_name=hub["name"],
                duration_minutes=ride1_min,
                distance_meters=hops1 * 1200,
            ),
            TripLeg(
                kind="transit",
                instruction=f"En {hub['name']}, transbordá a la Línea {l2['name']} hasta {d_stop['name']}",
                line_id=l2["id"],
                line_name=l2["name"],
                headsign=l2["headsign"],
                color=l2.get("color"),
                from_stop_id=hub["id"],
                from_stop_name=hub["name"],
                to_stop_id=d_stop["id"],
                to_stop_name=d_stop["name"],
                duration_minutes=ride2_min,
                distance_meters=hops2 * 1200,
            ),
            TripLeg(
                kind="walk",
                instruction=f"Bajate en {d_stop['name']} y caminá {int(d_dist)}m a {dest_name}",
                from_stop_id=d_stop["id"],
                from_stop_name=d_stop["name"],
                to_stop_name=dest_name,
                duration_minutes=walk_d_min,
                distance_meters=int(d_dist),
            ),
        ]

        summary = (
            f"Viaje con 1 transbordo: tomá Línea {l1['name']} en {o_stop['name']} hasta {hub['name']}, "
            f"hacé combinación con Línea {l2['name']} hasta {d_stop['name']} y caminá a {dest_name}. "
            f"Tiempo total: aprox {total_duration} minutos."
        )

        return TripPlan(
            origin=origin_name,
            destination=dest_name,
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            destination_lat=dest_lat,
            destination_lon=dest_lon,
            transfers=1,
            total_duration_minutes=total_duration,
            walking_meters=int(o_dist + d_dist),
            legs=legs,
            summary_text=summary,
            direct=False,
        )

    # Fallback walking if very close or isolated
    dist_direct = haversine_m(origin_lat, origin_lon, dest_lat, dest_lon)
    walk_min = max(1, int(round(dist_direct / 75.0)))
    return TripPlan(
        origin=origin_name,
        destination=dest_name,
        origin_lat=origin_lat,
        origin_lon=origin_lon,
        destination_lat=dest_lat,
        destination_lon=dest_lon,
        transfers=0,
        total_duration_minutes=walk_min,
        walking_meters=int(dist_direct),
        legs=[
            TripLeg(
                kind="walk",
                instruction=f"Caminá directamente de {origin_name} a {dest_name} ({int(dist_direct)} metros)",
                from_stop_name=origin_name,
                to_stop_name=dest_name,
                duration_minutes=walk_min,
                distance_meters=int(dist_direct),
            )
        ],
        summary_text=f"Distancia a pie: {int(dist_direct)} metros ({walk_min} min aprox). No se requiere transporte público.",
        direct=True,
    )


def extract_points_from_query(query: str) -> tuple[str, str]:
    """Extrae origen y destino de un texto como 'cómo voy de 7 y 50 a la facultad de informática' o 'de Plaza Moreno al Hospital de Niños'."""
    pattern1 = re.search(r"(?:de|desde)\s+(.+?)\s+(?:al?|hacia|hasta)\s+(.+)$", query, re.IGNORECASE)
    if pattern1:
        return pattern1.group(1).strip("?. "), pattern1.group(2).strip("?. ")

    pattern2 = re.search(r"como voy (?:al?|hacia|hasta)\s+(.+?)\s+(?:de|desde)\s+(.+)$", query, re.IGNORECASE)
    if pattern2:
        return pattern2.group(2).strip("?. "), pattern2.group(1).strip("?. ")

    parts = re.split(r"\s+(?:al?|hacia)\s+", query, flags=re.IGNORECASE)
    if len(parts) >= 2:
        return parts[0].strip("?. "), parts[1].strip("?. ")

    return "Plaza Moreno", query.strip("?. ")


def ask_travel_rag(query: str) -> TripPlan:
    """Subagente RAG de Viaje: Procesa lenguaje natural y genera la ruta completa."""
    origin_text, dest_text = extract_points_from_query(query)

    # Try Gemini extraction if available and query is complex
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            from agents.gemini import structured
            extracted = structured(
                f"Extrae origen y destino geográfico platense de esta consulta de transporte: '{query}'. "
                f"Si falta el origen, asume Plaza Moreno.",
                ExtractedPoints,
            )
            if extracted.origin and extracted.destination:
                origin_text = extracted.origin
                dest_text = extracted.destination
        except Exception:
            pass

    o_lat, o_lon, o_label = geocode_platense(origin_text)
    d_lat, d_lon, d_label = geocode_platense(dest_text)

    plan = plan_trip(
        origin_lat=o_lat,
        origin_lon=o_lon,
        dest_lat=d_lat,
        dest_lon=d_lon,
        origin_name=o_label,
        dest_name=d_label,
    )

    return plan
