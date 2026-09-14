"""Tests for Subagente RAG de Viaje (rag_planner)."""

import pytest
from agents.rag_planner import (
    geocode_platense,
    extract_points_from_query,
    plan_trip,
    ask_travel_rag,
    haversine_m,
)


def test_haversine_calculation():
    # Plaza Moreno (-34.9214, -57.9545) to Plaza San Martín (-34.9142, -57.9498) ~ 900m
    d = haversine_m(-34.9214, -57.9545, -34.9142, -57.9498)
    assert 800 < d < 1100


def test_geocode_platense_pois():
    lat, lon, label = geocode_platense("facultad de informatica")
    assert round(lat, 2) == -34.91
    assert round(lon, 2) == -57.93
    assert "Informática" in label

    lat2, lon2, label2 = geocode_platense("hospital de ninos")
    assert "Hospital" in label2
    assert round(lat2, 2) == -34.94


def test_geocode_platense_numeric_intersections():
    # 7 y 50
    lat, lon, label = geocode_platense("7 y 50")
    assert -35.0 < lat < -34.8
    assert -58.1 < lon < -57.8
    assert "7" in label and "50" in label

    # 12 y 51
    lat, lon, label = geocode_platense("12 y 51")
    assert -35.0 < lat < -34.8
    assert -58.1 < lon < -57.8


def test_extract_points_from_query():
    o, d = extract_points_from_query("cómo voy de 7 y 50 a la facultad de informática")
    assert "7 y 50" in o
    assert "facultad de informática" in d

    o2, d2 = extract_points_from_query("de Plaza Moreno al Hospital de Niños")
    assert "Plaza Moreno" in o2
    assert "Hospital de Niños" in d2

    o3, d3 = extract_points_from_query("como voy a Estacion La Plata desde 60 y 137")
    assert "60 y 137" in o3
    assert "Estacion La Plata" in d3


def test_direct_trip_plan():
    # Plaza Moreno to Estación La Plata (served by 506, 561, 307)
    plan = plan_trip(
        origin_lat=-34.9214,
        origin_lon=-57.9545,
        dest_lat=-34.9048,
        dest_lon=-57.9463,
        origin_name="Plaza Moreno",
        dest_name="Estación La Plata",
    )
    assert plan.direct is True
    assert plan.transfers == 0
    assert len(plan.legs) >= 2
    assert any(leg.kind == "transit" for leg in plan.legs)
    assert plan.total_duration_minutes > 0


def test_transfer_trip_plan():
    # Trip between Los Hornos Sur (-34.9691, -58.0062) and Berisso Puente Roma (-34.8722, -57.8862)
    # Line Sur connects with 506 / 214 via Plaza Moreno or Hospitales
    plan = plan_trip(
        origin_lat=-34.9691,
        origin_lon=-58.0062,
        dest_lat=-34.8722,
        dest_lon=-57.8862,
        origin_name="Los Hornos Sur",
        dest_name="Berisso Puente Roma",
    )
    assert plan.transfers == 1
    assert plan.direct is False
    assert len(plan.legs) >= 4
    transit_legs = [leg for leg in plan.legs if leg.kind == "transit"]
    assert len(transit_legs) == 2


def test_ask_travel_rag_natural():
    plan = ask_travel_rag("cómo voy de 7 y 50 a la facultad de informática")
    assert plan.summary_text is not None
    assert len(plan.legs) >= 2
    assert plan.total_duration_minutes > 0
