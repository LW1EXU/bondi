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


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncConnectionPool(os.environ["DATABASE_URL"], open=False,
                                   kwargs={"row_factory": dict_row}) as pool:
        await pool.wait(timeout=30)
        app.state.db = pool
        app.state.cache = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"),
                                         socket_connect_timeout=1, socket_timeout=1)
        try:
            yield
        finally:
            await app.state.cache.aclose()


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


class Alert(BaseModel):
    id: str
    title: str
    description: str
    line_id: str | None
    branch_id: str | None
    kind: str


async def rows(request: Request, sql: str, params=()):
    async with request.app.state.db.connection() as connection:
        cursor = await connection.execute(sql, params)
        return await cursor.fetchall()


@app.get("/health")
async def health(request: Request):
    await rows(request, "SELECT 1")
    return {"status": "ok"}


@app.get("/api/v1/lines", response_model=list[LineGroup])
async def lines(request: Request):
    cache = request.app.state.cache
    try:
        cached = await cache.get("lines:v1")
        if cached:
            return json.loads(cached)
    except RedisError:
        pass
    data = await rows(request, "SELECT l.id,l.name,l.type,l.verified,a.name AS company FROM lines l LEFT JOIN agencies a ON a.id=l.agency_id ORDER BY l.type,a.name,l.name")
    groups = {}
    for line in data:
        key = (line["type"], line["company"])
        groups.setdefault(key, {"type": key[0], "company": key[1], "lines": []})["lines"].append(line)
    result = list(groups.values())
    try:
        await cache.setex("lines:v1", 60, json.dumps(result))
    except RedisError:
        pass
    return result


@app.get("/api/v1/lines/{line_id}/branches", response_model=list[Branch])
async def branches(line_id: str, request: Request):
    if not await rows(request, "SELECT id FROM lines WHERE id=%s", (line_id,)):
        raise HTTPException(404, "Línea no encontrada")
    return await rows(request, "SELECT id,name,direction,variant,color FROM branches WHERE line_id=%s ORDER BY name,direction", (line_id,))


@app.get("/api/v1/lines/{line_id}/branches/{branch_id}/stops", response_model=list[Stop])
async def stops(line_id: str, branch_id: str, request: Request):
    if not await rows(request, "SELECT id FROM branches WHERE id=%s AND line_id=%s", (branch_id, line_id)):
        raise HTTPException(404, "Ramal no encontrado para la línea")
    return await rows(request, """SELECT s.id,s.name,ST_Y(s.location::geometry) AS lat,
        ST_X(s.location::geometry) AS lon,bs.sequence FROM branch_stops bs
        JOIN stops s ON s.id=bs.stop_id WHERE bs.branch_id=%s ORDER BY bs.sequence""", (branch_id,))


@app.get("/api/v1/stops/nearby", response_model=list[Stop])
async def nearby(request: Request, lat: Annotated[float, Query(ge=-90, le=90)],
                 lon: Annotated[float, Query(ge=-180, le=180)],
                 radius: Annotated[int, Query(ge=1, le=5000)] = 500):
    return await rows(request, """WITH point AS (SELECT ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography AS g)
        SELECT s.id,s.name,ST_Y(s.location::geometry) AS lat,ST_X(s.location::geometry) AS lon,
        ST_Distance(s.location,p.g) AS distance_m FROM stops s CROSS JOIN point p
        WHERE ST_DWithin(s.location,p.g,%s) ORDER BY distance_m,s.id LIMIT 100""", (lon, lat, radius))


@app.get("/api/v1/alerts", response_model=list[Alert])
async def alerts(request: Request):
    return await rows(request, """SELECT id,title,description,line_id,branch_id,kind FROM alerts
        WHERE moderation_status='approved' AND starts_at<=now() AND (ends_at IS NULL OR ends_at>now())
        ORDER BY starts_at DESC LIMIT 100""")
