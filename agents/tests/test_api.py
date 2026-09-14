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
