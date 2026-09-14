from unittest.mock import AsyncMock
import pytest
import asyncio
import httpx
from backend.app.main import app


def get(url):
    async def request():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.get(url)
    return asyncio.run(request())


def test_invalid_coordinates_rejected():
    assert get('/api/v1/stops/nearby?lat=91&lon=0').status_code == 422
    assert get('/api/v1/stops/nearby?lat=-34&lon=-58&radius=-1').status_code == 422


def test_missing_branch(monkeypatch):
    monkeypatch.setattr('backend.app.main.rows', AsyncMock(return_value=[]))
    assert get('/api/v1/lines/506/branches/wrong/stops').status_code == 404


def test_nearby_uses_lon_lat_and_meters(monkeypatch):
    query = AsyncMock(return_value=[])
    monkeypatch.setattr('backend.app.main.rows', query)
    response = get('/api/v1/stops/nearby?lat=-34.9&lon=-57.9&radius=700')
    assert response.status_code == 200
    assert query.call_args.args[2] == (-57.9,-34.9,700)
    assert 'ST_DWithin' in query.call_args.args[1]


def test_list_stops():
    response = get('/api/v1/stops')
    assert response.status_code == 200
    stops = response.json()
    assert len(stops) >= 30
    plaza_moreno = next((s for s in stops if s["id"] == "stop_plaza_moreno"), None)
    assert plaza_moreno is not None
    assert plaza_moreno["name"] == "Plaza Moreno"
    assert len(plaza_moreno["lines"]) >= 3


def test_stop_arrivals_and_countdown():
    response = get('/api/v1/stops/stop_plaza_moreno/arrivals')
    assert response.status_code == 200
    arrivals = response.json()
    assert len(arrivals) > 0
    first = arrivals[0]
    assert "line_name" in first
    assert "scheduled_time" in first
    assert "eta_seconds" in first
    assert first["eta_seconds"] >= 0
    # Arrivals should be sorted chronologically
    for i in range(len(arrivals) - 1):
        assert arrivals[i]["eta_seconds"] <= arrivals[i+1]["eta_seconds"]


def test_line_stops():
    response = get('/api/v1/lines/506/stops')
    assert response.status_code == 200
    stops = response.json()
    assert len(stops) >= 5
    ids = [s["id"] for s in stops]
    assert "stop_plaza_moreno" in ids

    assert get('/api/v1/lines/linea_inexistente/stops').status_code == 404


def test_lines_type_filtering():
    response = get('/api/v1/lines?type=comunal')
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for group in data:
        assert group["type"].lower() == "comunal"
        for line in group["lines"]:
            assert line["type"].lower() == "comunal"

    prov_res = get('/api/v1/lines?type=provincial')
    assert prov_res.status_code == 200
    prov_data = prov_res.json()
    assert len(prov_data) > 0
    for group in prov_data:
        assert group["type"].lower() == "provincial"


def test_plan_route():
    async def request():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.post('/api/v1/plan', json={
                "origin_lat": -34.9214,
                "origin_lon": -57.9545,
                "dest_lat": -34.9048,
                "dest_lon": -57.9463,
                "origin_name": "Plaza Moreno",
                "dest_name": "Estación La Plata",
            })
    res = asyncio.run(request())
    assert res.status_code == 200
    plan = res.json()
    assert "legs" in plan
    assert len(plan["legs"]) >= 2
    assert "total_duration_minutes" in plan
    assert plan["total_duration_minutes"] > 0
    assert plan["direct"] is True


def test_travel_assistant():
    async def request():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.post('/api/v1/travel-assistant', json={
                "query": "cómo voy de 7 y 50 a la facultad de informática"
            })
    res = asyncio.run(request())
    assert res.status_code == 200
    plan = res.json()
    assert "summary_text" in plan
    assert len(plan["legs"]) >= 2
    assert "Rondín" in plan["summary_text"] or "UNLP" in plan["summary_text"] or "Este" in plan["summary_text"]


def test_sync_deltas():
    response = get('/api/v1/sync/deltas')
    assert response.status_code == 200
    sync = response.json()
    assert sync["version"] == "0.2.0"
    assert sync["full_sync"] is True
    assert len(sync["lines"]) >= 19
    assert len(sync["stops"]) >= 33
    assert len(sync["branches"]) >= 19
    assert len(sync["branch_stops"]) >= 50

