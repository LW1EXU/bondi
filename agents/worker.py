import argparse
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from apscheduler.schedulers.blocking import BlockingScheduler
from agents.crawler import crawl
from agents.models import Dataset, GazetteerEntry
from agents.normalizer import normalize, geojson
from agents.validator import diff, review

log = logging.getLogger("bondi.pipeline")


def run_once() -> Path:
    root = Path(os.getenv("DATA_DIR", "data"))
    run = root / "runs" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8])
    run.mkdir(parents=True)
    try:
        config = Path("agents/config")
        sources = json.loads((config / "sources.json").read_text())
        enabled = [source for source in sources if source.get("enabled")]
        if not enabled:
            raise ValueError("No hay fuentes habilitadas; configurar URLs de recorridos verificadas")
        records = []
        for source in enabled:
            records.extend(crawl(source, run / "raw"))
        (run / "extractions.json").write_text(json.dumps(records, ensure_ascii=False, indent=2))
        gazetteer = [GazetteerEntry.model_validate(entry) for entry in json.loads((config / "gazetteer.json").read_text())]
        dataset = normalize(records, gazetteer)
        (run / "candidate.json").write_text(dataset.model_dump_json(indent=2))
        previous_file = root / "published.json"
        published = json.loads(previous_file.read_text()) if previous_file.exists() else None
        previous = Dataset.model_validate(published["dataset"]) if published else None
        report = review(dataset, previous)
        delta = diff(previous, dataset, published["version"] if published else "0.0.0")
        (run / "review.json").write_text(json.dumps({**report.model_dump(), "diff": delta}, indent=2, ensure_ascii=False))
        if report.approved:
            (run / "stops-sequence.geojson").write_text(json.dumps(geojson(dataset), ensure_ascii=False))
        # Publication is a separate transaction, not an LLM side effect.
        (run / "status.json").write_text(json.dumps({"status": "review_required" if report.approved else "rejected"}))
        log.info("Pipeline terminado: %s", run)
        return run
    except Exception as exc:
        (run / "status.json").write_text(json.dumps({"status": "failed", "error_type": type(exc).__name__}))
        log.error("Pipeline falló (%s); ver configuración y artefactos en %s", type(exc).__name__, run)
        raise


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.once:
        run_once()
        return
    scheduler = BlockingScheduler(timezone="America/Argentina/Buenos_Aires")
    scheduler.add_job(run_once, "cron", hour=3, minute=0, id="daily-ingestion",
                      max_instances=1, coalesce=True, misfire_grace_time=3600)
    log.info("Programado diariamente a las 03:00 America/Argentina/Buenos_Aires")
    scheduler.start()


if __name__ == "__main__":
    main()
