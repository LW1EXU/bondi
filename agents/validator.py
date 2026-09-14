import math
from agents.gemini import structured
from agents.models import Dataset, Review


def distance_km(a, b) -> float:
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlat, dlon = lat2-lat1, math.radians(b.lon-a.lon)
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))


def validate(dataset: Dataset, previous: Dataset | None = None) -> list[str]:
    issues = []
    if not dataset.branches:
        issues.append("Dataset sin ramales")
    ids = [b.id for b in dataset.branches]
    if len(ids) != len(set(ids)):
        issues.append("Ramales duplicados: resolver conflictos entre fuentes")
    for branch in dataset.branches:
        if branch.unresolved:
            issues.append(f"{branch.id}: direcciones sin resolver: {branch.unresolved}")
        if len(branch.stops) < 2:
            issues.append(f"{branch.id}: menos de dos paradas")
        for a, b in zip(branch.stops, branch.stops[1:]):
            if distance_km(a, b) > 10:
                issues.append(f"{branch.id}: salto mayor de 10 km (requiere revisión interurbana)")
            if a.id == b.id:
                issues.append(f"{branch.id}: paradas consecutivas duplicadas")
    if previous and {b.id for b in previous.branches} - set(ids):
        issues.append("Desaparecieron ramales: confirmar baja o falla de fuente")
    return issues


def diff(previous: Dataset | None, current: Dataset, version: str = "0.0.0") -> dict:
    before = {b.id: b.model_dump() for b in previous.branches} if previous else {}
    after = {b.id: b.model_dump() for b in current.branches}
    added = sorted(after.keys() - before.keys())
    removed = sorted(before.keys() - after.keys())
    changed = sorted(key for key in before.keys() & after.keys() if before[key] != after[key])
    major, minor, patch = map(int, version.split("."))
    structural = removed or any(before[k]["stops"] != after[k]["stops"] for k in changed)
    next_version = f"{major+1}.0.0" if structural else f"{major}.{minor+1}.0" if added else f"{major}.{minor}.{patch+1}" if changed else version
    return {"version": next_version, "added": added, "removed": removed, "changed": changed}


def review(dataset: Dataset, previous: Dataset | None) -> Review:
    issues = validate(dataset, previous)
    if issues:
        return Review(approved=False, issues=issues)
    return structured(
        "Audita el candidato de transporte y su anterior. Detecta contradicciones, secuencias incoherentes y pérdida de cobertura. "
        "No asumas veracidad por tener formato correcto. Devuelve approved e issues. Candidato: " + dataset.model_dump_json()
        + " Anterior: " + (previous.model_dump_json() if previous else "null"), Review, pro=True)
