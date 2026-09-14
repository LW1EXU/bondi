"""Router de Paradas, Búsqueda por Intersección y Telemetría "¿Cuándo llega mi micro?"."""

import os
from typing import Optional, Annotated
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from agents.realtime_client import (
    RealtimeClient,
    StopArrivalsResponse,
    ArrivalEstimate,
    StopLookupResult,
    find_stop_by_intersection,
    get_stop_by_code,
    normalize_street,
)

router = APIRouter(prefix="/stops", tags=["stops"])
realtime_client = RealtimeClient()


@router.get("/lookup", response_model=StopLookupResult)
async def lookup_stop(
    request: Request,
    street: Annotated[str, Query(..., description="Nombre o número de la calle principal (ej. 1, Calle 1)")],
    cross: Annotated[str, Query(..., description="Nombre o número de la calle transversal (ej. 42, Calle 42)")],
):
    """Permite al usuario buscar una parada tipeando las dos calles de la intersección.

    Retorna el stop_code numérico oficial, coordenadas PostGIS y líneas que pasan por la parada.
    """
    norm_s = normalize_street(street)
    norm_c = normalize_street(cross)

    # 1. Búsqueda en base de datos PostGIS si está conectada
    if getattr(request.app.state, "db", None):
        try:
            async with request.app.state.db.connection() as conn:
                sql = """
                    SELECT s.stop_code, s.name, s.street, s.cross_street, s.intersection, s.zone,
                           ST_Y(s.geom) AS lat, ST_X(s.geom) AS lon,
                           COALESCE(ARRAY_AGG(DISTINCT sr.line_code) FILTER (WHERE sr.line_code IS NOT NULL), '{}') AS lines
                    FROM stops s
                    LEFT JOIN stop_routes sr ON sr.stop_code = s.stop_code
                    WHERE (LOWER(s.street) = LOWER(%s) AND LOWER(s.cross_street) = LOWER(%s))
                       OR (LOWER(s.street) = LOWER(%s) AND LOWER(s.cross_street) = LOWER(%s))
                       OR (LOWER(s.intersection) LIKE LOWER(%s) AND LOWER(s.intersection) LIKE LOWER(%s))
                    GROUP BY s.stop_code, s.name, s.street, s.cross_street, s.intersection, s.zone, s.geom
                    LIMIT 1
                """
                pattern_s = f"%{norm_s}%"
                pattern_c = f"%{norm_c}%"
                cursor = await conn.execute(sql, (norm_s, norm_c, norm_c, norm_s, pattern_s, pattern_c))
                row = await cursor.fetchone()
                if row and row.get("stop_code"):
                    lines_list = list(row.get("lines") or [])
                    return StopLookupResult(
                        stop_code=int(row["stop_code"]),
                        name=str(row["name"]),
                        street=str(row["street"]),
                        cross_street=str(row["cross_street"]),
                        intersection=str(row["intersection"]),
                        zone=str(row["zone"]),
                        lat=float(row["lat"]),
                        lon=float(row["lon"]),
                        lines=lines_list
                    )
        except Exception:
            pass

    # 2. Búsqueda en registro local en memoria (fallback resiliente de alta disponibilidad)
    match = find_stop_by_intersection(street, cross)
    if match:
        return StopLookupResult(
            stop_code=match["stop_code"],
            name=match["name"],
            street=match["street"],
            cross_street=match["cross_street"],
            intersection=match["intersection"],
            zone=match["zone"],
            lat=match["lat"],
            lon=match["lon"],
            lines=match["lines"]
        )

    raise HTTPException(
        status_code=404,
        detail=f"Parada no encontrada para la intersección entre '{street}' y '{cross}'"
    )


@router.get("/{stop_code:int}/arrivals", response_model=StopArrivalsResponse)
async def get_arrivals_by_stop_code(
    stop_code: int,
    request: Request,
    simulate: Annotated[bool, Query(description="Simula telemetría GPS satelital activa en vivo")] = False,
):
    """Consulta de arribos idéntica a '¿Cuándo llega mi micro?'.

    Retorna los micros proyectados para la parada con tiempos estimados (ETA), distancias en metros
    y si la información proviene de telemetría GPS satelital en vivo o del Headway Estimation Engine.
    """
    # Verificar existencia en BD o registro
    stop_meta = get_stop_by_code(stop_code)

    if not stop_meta and getattr(request.app.state, "db", None):
        try:
            async with request.app.state.db.connection() as conn:
                cursor = await conn.execute(
                    "SELECT stop_code, name, intersection, zone FROM stops WHERE stop_code = %s",
                    (stop_code,)
                )
                db_row = await cursor.fetchone()
                if db_row:
                    stop_meta = {
                        "stop_code": db_row["stop_code"],
                        "name": db_row["name"],
                        "intersection": db_row["intersection"],
                        "zone": db_row["zone"],
                        "routes": []
                    }
        except Exception:
            pass

    if not stop_meta:
        raise HTTPException(
            status_code=404,
            detail=f"Parada con código unificado {stop_code} no encontrada en el sistema"
        )

    # Invocar cliente de telemetría y motor de estimación
    response = realtime_client.get_stop_arrivals(stop_code=stop_code, simulate_realtime=simulate)
    return response
