import json
import os
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from redis.asyncio import Redis
from redis.exceptions import RedisError

from backend.app.transport_data import (
    STOPS,
    LINES,
    get_all_stops,
    get_stop_by_id,
    calculate_arrivals,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            async with AsyncConnectionPool(db_url, open=False, kwargs={"row_factory": dict_row}) as pool:
                await pool.wait(timeout=10)
                app.state.db = pool
                app.state.cache = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                                                 socket_connect_timeout=1, socket_timeout=1)
                yield
                await app.state.cache.aclose()
                return
        except Exception:
            pass
    app.state.db = None
    app.state.cache = None
    yield


app = FastAPI(title="Bondi API", version="0.1.0", lifespan=lifespan)


class Line(BaseModel):
    id: str
    name: str
    type: str
    company: str | None
    verified: bool


class LineGroup(BaseModel):
    type: str
    company: str | None
    lines: list[Line]


class Branch(BaseModel):
    id: str
    name: str
    direction: int
    variant: str
    color: str | None


class Stop(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    sequence: int | None = None
    distance_m: float | None = None


class StopLine(BaseModel):
    id: str
    name: str
    type: str
    color: str | None = None
    headsign: str | None = None
    frequency_min: int | None = None


class StopDetail(BaseModel):
    id: str
    name: str
    address: str | None = None
    lat: float
    lon: float
    landmark: str | None = None
    lines: list[StopLine] = []
    line_count: int = 0


class BusArrival(BaseModel):
    line_id: str
    line_name: str
    line_type: str
    line_color: str | None = None
    headsign: str
    scheduled_time: str
    eta_seconds: int
    eta_minutes: int
    status: str


class Alert(BaseModel):
    id: str
    title: str
    description: str
    line_id: str | None
    branch_id: str | None
    kind: str


async def rows(request: Request, sql: str, params=()):
    if not getattr(request.app.state, "db", None):
        return []
    async with request.app.state.db.connection() as connection:
        cursor = await connection.execute(sql, params)
        return await cursor.fetchall()


@app.get("/health")
async def health(request: Request):
    if getattr(request.app.state, "db", None):
        await rows(request, "SELECT 1")
    return {"status": "ok"}


@app.get("/api/v1/lines", response_model=list[LineGroup])
async def lines(request: Request):
    cache = getattr(request.app.state, "cache", None)
    if cache:
        try:
            cached = await cache.get("lines:v1")
            if cached:
                return json.loads(cached)
        except RedisError:
            pass

    data = await rows(request, "SELECT l.id,l.name,l.type,l.verified,a.name AS company FROM lines l LEFT JOIN agencies a ON a.id=l.agency_id ORDER BY l.type,a.name,l.name")
    if not data:
        # Fallback to predefined Gran La Plata lines
        groups_map = {}
        for l in LINES:
            k = (l["type"].capitalize(), l["company"])
            groups_map.setdefault(k, {"type": k[0], "company": k[1], "lines": []})["lines"].append({
                "id": l["id"],
                "name": l["name"],
                "type": l["type"],
                "company": l["company"],
                "verified": False,
            })
        result = list(groups_map.values())
        return result

    groups = {}
    for line in data:
        key = (line["type"], line["company"])
        groups.setdefault(key, {"type": key[0], "company": key[1], "lines": []})["lines"].append(line)
    result = list(groups.values())
    if cache:
        try:
            await cache.setex("lines:v1", 60, json.dumps(result))
        except RedisError:
            pass
    return result


@app.get("/api/v1/lines/{line_id}/branches", response_model=list[Branch])
async def branches(line_id: str, request: Request):
    line_data = next((l for l in LINES if l["id"].lower() == line_id.lower()), None)
    db_branches = await rows(request, "SELECT id,name,direction,variant,color FROM branches WHERE line_id=%s ORDER BY name,direction", (line_id,))
    if db_branches:
        return db_branches
    if not line_data and not await rows(request, "SELECT id FROM lines WHERE id=%s", (line_id,)):
        raise HTTPException(404, "Línea no encontrada")
    if line_data:
        return [{
            "id": f"{line_data['id']}_ida",
            "name": line_data["headsign"],
            "direction": 0,
            "variant": "regular",
            "color": line_data["color"].replace("#", ""),
        }]
    return []


@app.get("/api/v1/lines/{line_id}/branches/{branch_id}/stops", response_model=list[Stop])
async def branch_stops(line_id: str, branch_id: str, request: Request):
    db_stops = await rows(request, """SELECT s.id,s.name,ST_Y(s.location::geometry) AS lat,
        ST_X(s.location::geometry) AS lon,bs.sequence FROM branch_stops bs
        JOIN stops s ON s.id=bs.stop_id WHERE bs.branch_id=%s ORDER BY bs.sequence""", (branch_id,))
    if db_stops:
        return db_stops

    line_data = next((l for l in LINES if l["id"].lower() == line_id.lower()), None)
    valid_branch = (branch_id == f"{line_id.lower()}_ida")
    if not valid_branch and not await rows(request, "SELECT id FROM branches WHERE id=%s AND line_id=%s", (branch_id, line_id)):
        raise HTTPException(404, "Ramal no encontrado para la línea")

    if line_data and valid_branch:
        stops_result = []
        for idx, sid in enumerate(line_data["stops"]):
            s_obj = STOPS.get(sid)
            if s_obj:
                stops_result.append({
                    "id": s_obj["id"],
                    "name": s_obj["name"],
                    "lat": s_obj["lat"],
                    "lon": s_obj["lon"],
                    "sequence": idx,
                    "distance_m": None,
                })
        return stops_result
    raise HTTPException(404, "Ramal no encontrado para la línea")


@app.get("/api/v1/stops", response_model=list[StopDetail])
async def list_stops(request: Request):
    """Devuelve todas las paradas del Gran La Plata con las líneas que pasan por cada una."""
    return get_all_stops()


@app.get("/api/v1/stops/nearby", response_model=list[Stop])
async def nearby(request: Request, lat: Annotated[float, Query(ge=-90, le=90)],
                 lon: Annotated[float, Query(ge=-180, le=180)],
                 radius: Annotated[int, Query(ge=1, le=5000)] = 500):
    return await rows(request, """WITH point AS (SELECT ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography AS g)
        SELECT s.id,s.name,ST_Y(s.location::geometry) AS lat,ST_X(s.location::geometry) AS lon,
        ST_Distance(s.location,p.g) AS distance_m FROM stops s CROSS JOIN point p
        WHERE ST_DWithin(s.location,p.g,%s) ORDER BY distance_m,s.id LIMIT 100""", (lon, lat, radius))


@app.get("/api/v1/stops/{stop_id}", response_model=StopDetail)
async def get_stop(stop_id: str, request: Request):
    """Devuelve la información de una parada específica."""
    stop = get_stop_by_id(stop_id)
    if not stop:
        raise HTTPException(404, "Parada no encontrada")
    return stop


@app.get("/api/v1/stops/{stop_id}/arrivals", response_model=list[BusArrival])
async def get_stop_arrivals(stop_id: str, request: Request):
    """Devuelve los próximos micros que arribarán a la parada con cuenta regresiva en segundos."""
    if stop_id not in STOPS:
        raise HTTPException(404, "Parada no encontrada")
    return calculate_arrivals(stop_id)


@app.get("/api/v1/lines/{line_id}/stops", response_model=list[StopDetail])
async def get_line_stops(line_id: str, request: Request):
    """Devuelve las paradas en orden para una línea de micro específica."""
    line = next((l for l in LINES if l["id"].lower() == line_id.lower()), None)
    if not line:
        raise HTTPException(404, "Línea no encontrada")
    return [get_stop_by_id(sid) for sid in line["stops"] if get_stop_by_id(sid)]


@app.get("/api/v1/alerts", response_model=list[Alert])
async def alerts(request: Request):
    return await rows(request, """SELECT id,title,description,line_id,branch_id,kind FROM alerts
        WHERE moderation_status='approved' AND starts_at<=now() AND (ends_at IS NULL OR ends_at>now())
        ORDER BY starts_at DESC LIMIT 100""")
