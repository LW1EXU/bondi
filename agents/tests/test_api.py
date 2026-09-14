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
