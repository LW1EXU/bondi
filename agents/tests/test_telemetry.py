"""Tests unitarios y de integración para el subsistema de telemetría y arribos."""

import asyncio
import httpx
import pytest
from backend.app.main import app
from backend.app.routers.stops import realtime_client
from agents.realtime_client import RealtimeClient, STOP_REGISTRY_BY_CODE
from agents.schedule_crawler import ScheduleCrawler, TimetableEntry


def get_client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def async_get(url: str):
    async def req():
        async with get_client() as client:
            return await client.get(url)
    return asyncio.run(req())


# ---------------------------------------------------------------------------
# 1. Tests de búsqueda de parada por intersección (Lookup)
# ---------------------------------------------------------------------------

def test_lookup_stop_1735_exact_numbers():
    """Consulta por intersección '1 y 42' devuelve Parada 1735."""
    res = async_get("/api/v1/stops/lookup?street=1&cross=42")
    assert res.status_code == 200
    data = res.json()
    assert data["stop_code"] == 1735
    assert data["intersection"] == "Calle 1 y Calle 42"
    assert data["zone"] == "Casco Urbano"
    assert pytest.approx(data["lat"], rel=1e-4) == -34.9040
    assert pytest.approx(data["lon"], rel=1e-4) == -57.9482
    assert "Este" in data["lines"]
    assert "275" in data["lines"]
    assert "506" in data["lines"]
    assert "unlp" in data["lines"]


def test_lookup_stop_1735_reversed_and_with_text():
    """Búsqueda con orden invertido y prefijo 'Calle'."""
    res_inv = async_get("/api/v1/stops/lookup?street=42&cross=1")
    assert res_inv.status_code == 200
    assert res_inv.json()["stop_code"] == 1735

    res_txt = async_get("/api/v1/stops/lookup?street=Calle 1&cross=Calle 42")
    assert res_txt.status_code == 200
    assert res_txt.json()["stop_code"] == 1735


def test_lookup_plaza_moreno():
    """Búsqueda de parada emblemática Plaza Moreno (12 y 51)."""
    res = async_get("/api/v1/stops/lookup?street=12&cross=51")
    assert res.status_code == 200
    data = res.json()
    assert data["stop_code"] == 1001
    assert data["intersection"] == "Calle 12 y Calle 51"
    assert "506" in data["lines"]


def test_lookup_stop_not_found():
    """Búsqueda de esquina inexistente devuelve 404."""
    res = async_get("/api/v1/stops/lookup?street=999&cross=999")
    assert res.status_code == 404
    assert "no encontrada" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 2. Tests de arribos en tiempo real (simulado y live GPS)
# ---------------------------------------------------------------------------

def test_stop_1735_arrivals_simulated_realtime():
    """Consulta de arribos con telemetría en tiempo real activa para parada 1735."""
    res = async_get("/api/v1/stops/1735/arrivals?simulate=true")
    assert res.status_code == 200
    data = res.json()

    assert data["stop_code"] == 1735
    assert data["intersection"] == "Calle 1 y Calle 42"
    assert "query_time" in data
    assert isinstance(data["arrivals"], list)
    assert len(data["arrivals"]) >= 2

    # Línea Este: arribo en vivo por GPS (is_realtime=true)
    este = next((a for a in data["arrivals"] if a["line"] == "Este"), None)
    assert este is not None
    assert este["branch"] == "Ramal 12"
    assert este["destination"] == "Plaza Italia"
    assert este["eta_minutes"] == 3
    assert este["eta_text"] == "3 min"
    assert este["distance_meters"] == 650
    assert este["is_realtime"] is True
    assert este["confidence"] == "realtime"

    # Línea 275: arribo calculado por frecuencia/cronograma (is_realtime=false)
    line_275 = next((a for a in data["arrivals"] if a["line"] == "275"), None)
    assert line_275 is not None
    assert line_275["branch"] == "Ensenada"
    assert line_275["destination"] == "Astillero"
    assert line_275["eta_minutes"] == 11
    assert line_275["eta_text"] == "11 min"
    assert line_275["distance_meters"] == 2400
    assert line_275["is_realtime"] is False
    assert line_275["confidence"] == "scheduled"


def test_stop_1735_arrivals_fallback_headway(monkeypatch):
    """Fallback inteligente: si falla la API de GPS, todas las líneas usan Headway Engine."""
    # Simular que el endpoint satelital municipal está caído o tiene timeout
    monkeypatch.setattr(realtime_client, "query_gps_telemetry", lambda code: None)

    res = async_get("/api/v1/stops/1735/arrivals")
    assert res.status_code == 200
    data = res.json()

    assert data["stop_code"] == 1735
    assert data["intersection"] == "Calle 1 y Calle 42"
    assert len(data["arrivals"]) >= 2

    # Todas las unidades deben reportar is_realtime=false y confidence="scheduled"
    for arrival in data["arrivals"]:
        assert arrival["is_realtime"] is False
        assert arrival["confidence"] == "scheduled"
        assert arrival["eta_minutes"] > 0
        assert arrival["distance_meters"] > 0
        assert "min" in arrival["eta_text"] or arrival["eta_text"] == "¡Llegando!"


def test_nonexistent_stop_arrivals():
    """Consulta de código de parada no existente devuelve 404."""
    res = async_get("/api/v1/stops/999999/arrivals")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# 3. Tests del motor Headway y Crawler de cronogramas
# ---------------------------------------------------------------------------

def test_realtime_client_headway_calculation():
    """Valida la lógica del Headway Engine con velocidades de corredor (12 km/h casco, 25 km/h avenidas)."""
    client = RealtimeClient()
    stop_data = STOP_REGISTRY_BY_CODE[1735]
    from datetime import datetime, timezone
    now = datetime(2026, 9, 14, 14, 32, 0, tzinfo=timezone.utc)

    estimates = client.estimate_headway_arrivals(1735, stop_data, now)
    assert len(estimates) == 4
    for est in estimates:
        assert est.is_realtime is False
        assert est.confidence == "scheduled"
        assert est.eta_minutes >= 1


def test_schedule_crawler_coverage():
    """Verifica que el crawler extraiga las 21 líneas con franjas horarias y días tipo."""
    crawler = ScheduleCrawler()
    report = crawler.build_full_report()

    assert report.total_lines >= 21
    assert len(report.timetables) > 100

    # Verificar presencia de las líneas claves solicitadas
    expected_lines = {"195", "129", "338", "273", "214", "307", "202", "215", "418",
                      "506", "518", "520", "561", "508", "norte", "sur", "este", "oeste", "unlp"}
    crawled_lines = {t.line_code for t in report.timetables}
    for l in expected_lines:
        assert l in crawled_lines, f"Línea {l} no encontrada en los cronogramas rastreados"

    # Verificar franjas horarias
    time_bands = {t.time_band for t in report.timetables}
    assert "PICO_MANANA" in time_bands
    assert "VALLE" in time_bands
    assert "PICO_TARDE" in time_bands
    assert "NOCTURNO" in time_bands

    # Verificar días tipo
    day_types = {t.day_type for t in report.timetables}
    assert "HABIL" in day_types
    assert "SABADO" in day_types
    assert "DOMINGO_FERIADO" in day_types
