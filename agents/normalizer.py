"""Gemini normalizes names; coordinates come exclusively from a curated gazetteer."""
import hashlib
import json
import re
import unicodedata
from agents.gemini import structured
from agents.models import Addresses, Branch, Dataset, Extraction, GazetteerEntry, Stop


def canonicalize(value: str) -> str:
    value = "".join(c for c in unicodedata.normalize("NFD", value.lower()) if unicodedata.category(c) != "Mn")
    value = re.sub(r"\b(diag|dg)\.?\s*", "diagonal ", value)
    value = re.sub(r"\b(av|avda)\.?\s*", "avenida ", value)
    value = re.sub(r"\b(cno)\.?\s*", "camino ", value)
    value = re.sub(r"\s*(?:&|\besquina\b)\s*", " y ", value)
    return " ".join(value.split())


def stable_id(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()[:24]


def normalize(records: list[dict], gazetteer: list[GazetteerEntry]) -> Dataset:
    index = {}
    for entry in gazetteer:
        key = canonicalize(entry.canonical)
        if key in index:
            raise ValueError(f"Dirección ambigua en nomenclátor: {key}")
        index[key] = entry
    branches = []
    for record in records:
        extraction = Extraction.model_validate(record["extraction"])
        for raw in extraction.branches:
            unknown = sorted({name for name in raw.stop_names if canonicalize(name) not in index})
            aliases = {}
            if unknown:
                addresses = structured(
                    "Normaliza nomenclatura platense: calles numéricas, diagonales, caminos y POI. "
                    "No calcules coordenadas. Devuelve exactamente una entrada por original. Datos: " + json.dumps(unknown), Addresses)
                if len(addresses.addresses) != len(unknown) or {a.original for a in addresses.addresses} != set(unknown):
                    raise ValueError("Gemini omitió o agregó direcciones")
                aliases = {a.original: canonicalize(a.canonical) for a in addresses.addresses}
            stops, unresolved = [], []
            for name in raw.stop_names:
                entry = index.get(aliases.get(name, canonicalize(name)))
                if entry is None:
                    unresolved.append(name)
                else:
                    stops.append(Stop(**entry.model_dump(), id=stable_id(canonicalize(entry.canonical))))
            branches.append(Branch(
                id=stable_id(raw.line_id, raw.name, str(raw.direction), raw.variant),
                line_id=raw.line_id, name=raw.name, direction=raw.direction, variant=raw.variant,
                stops=stops, unresolved=unresolved, source_url=record["url"],
                source_sha256=record["sha256"], evidence=raw.evidence, schedule_text=raw.schedule_text))
    return Dataset(branches=sorted(branches, key=lambda branch: branch.id))


def geojson(dataset: Dataset) -> dict:
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": branch.id,
         "properties": {"line_id": branch.line_id, "name": branch.name, "source_url": branch.source_url,
                        "geometry_kind": "stop_sequence_not_road_shape"},
         "geometry": {"type": "LineString", "coordinates": [[s.lon, s.lat] for s in branch.stops]}}
        for branch in dataset.branches if not branch.unresolved and len(branch.stops) >= 2]}
