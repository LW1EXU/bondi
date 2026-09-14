"""Bounded official-source crawler; archives original bytes before extraction."""
import hashlib
import ipaddress
import json
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from agents.gemini import structured
from agents.models import Extraction

USER_AGENT = "BondiResearchBot/0.1"
MAX_BYTES = 2_000_000


def validate_url(url: str, allowed_hosts: set[str]) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("URL fuera de la lista de fuentes HTTPS")
    addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("La fuente resuelve a una red no pública")


def download(client: httpx.Client, url: str, hosts: set[str]) -> tuple[bytes, str]:
    validate_url(url, hosts)
    # Redirects deliberately require explicit configuration of the final URL.
    with client.stream("GET", url) as response:
        response.raise_for_status()
        content = bytearray()
        for chunk in response.iter_bytes():
            content.extend(chunk)
            if len(content) > MAX_BYTES:
                raise ValueError("Documento demasiado grande")
        return bytes(content), response.headers.get("content-type", "")


def crawl(source: dict, archive: Path) -> list[dict]:
    hosts = set(source["allowed_hosts"])
    pending = list(source["urls"])
    seen: set[str] = set()
    results = []
    robots: dict[str, RobotFileParser] = {}
    with httpx.Client(timeout=30, follow_redirects=False, headers={"User-Agent": USER_AGENT}) as client:
        while pending and len(seen) < source.get("max_pages", 5):
            url = pending.pop(0).split("#")[0]
            if url in seen:
                continue
            seen.add(url)
            origin = "https://" + (urlparse(url).netloc)
            if origin not in robots:
                body, _ = download(client, origin + "/robots.txt", hosts)
                robot = RobotFileParser()
                robot.parse(body.decode("utf-8", errors="replace").splitlines())
                robots[origin] = robot
            if not robots[origin].can_fetch(USER_AGENT, url):
                raise ValueError(f"robots.txt impide extraer {url}")
            time.sleep(max(1, robots[origin].crawl_delay(USER_AGENT) or 1))
            body, content_type = download(client, url, hosts)
            digest = hashlib.sha256(body).hexdigest()
            archive.mkdir(parents=True, exist_ok=True)
            (archive / f"{digest}.raw").write_bytes(body)
            metadata = {"url": url, "sha256": digest, "content_type": content_type,
                        "fetched_at": datetime.now(timezone.utc).isoformat()}
            (archive / f"{digest}.json").write_text(json.dumps(metadata, ensure_ascii=False))
            if "text/html" not in content_type and "text/plain" not in content_type:
                raise ValueError("Formato archivado pero no soportado aún (PDF/imagen requiere adaptador)")
            soup = BeautifulSoup(body, "html.parser")
            for link in soup.select("a[href]"):
                target = urljoin(url, link["href"]).split("#")[0]
                if urlparse(target).hostname in hosts and any(term in target.lower() for term in source.get("link_terms", [])):
                    pending.append(target)
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            document = soup.get_text(" ", strip=True)
            if len(document) > 80000:
                raise ValueError("Texto excede el presupuesto: requiere partición explícita")
            extraction = structured(
                "Extrae solo ramales, paradas en orden, sentido explícito 0=ida/1=vuelta y avisos de transporte del Gran La Plata. "
                "Omite ramales cuyo sentido no esté especificado. Copia evidence literalmente del documento. "
                "No derives horarios ni fechas. Conserva los horarios disponibles en schedule_text. "
                "Si no hay datos devuelve listas vacías. Documento JSON: " + json.dumps({"url": url, "text": document}), Extraction)
            for item in [*extraction.branches, *extraction.alerts]:
                if item.evidence not in document:
                    raise ValueError("Evidencia no encontrada en documento original")
            results.append({**metadata, "extraction": extraction.model_dump(mode="json")})
    return results
