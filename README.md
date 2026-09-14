# Bondi · Gran La Plata

Primera etapa: infraestructura, esquema PostGIS y pipeline de candidatos de datos con Gemini.
Incluye una API de consulta, una portada Next.js conectada a ella y un cliente Android preliminar. **No es todavía una
plataforma de transporte operativa**: no hay recorridos ni horarios oficiales cargados.

## Android preliminar

- 📲 **Descarga directa del APK**: [bondi-0.1.0-alpha.1.apk](https://github.com/LW1EXU/bondi/releases/download/v0.1.0-alpha.1/bondi-0.1.0-alpha.1.apk)
- 🏷️ **Notas de la versión**: [GitHub Releases v0.1.0-alpha.1](https://github.com/LW1EXU/bondi/releases/tag/v0.1.0-alpha.1)

Incluye catálogo offline de las 19 líneas solicitadas, búsqueda y favoritos; no requiere conexión a Internet.

## Inicio local

Requisitos: Docker Engine con Compose v2. Copiar `.env.example` a `.env`:

```sh
cp .env.example .env
docker compose up --build
```

Web: http://localhost:3000 · API/OpenAPI: http://localhost:8000/docs.
PostgreSQL y Redis son internos a la red de Compose. La contraseña predeterminada es
solo para desarrollo. No guardar claves en Git. `schema.sql` se ejecuta únicamente
al crear el volumen de PostgreSQL por primera vez; cambios posteriores requieren migraciones.

## Estructura y alcance implementado

- `schema.sql`: entidades de transporte, índices GiST, calendarios/excepciones, horarios
  con segundos superiores a 86400, alertas moderadas, versiones y registro de deltas.
- `backend/`: FastAPI, Pydantic, pool PostgreSQL y caché Redis opcional de líneas (60 s).
- `agents/crawler.py`: fuentes HTTPS explícitas, robots.txt, rastreo acotado, límite
  de descarga, archivo SHA-256 y extracción estructurada de ramales y avisos.
- `agents/normalizer.py`: parser local y Gemini Flash para nombres desconocidos;
  coordenadas exclusivas del nomenclátor con referencia a fuente.
- `agents/validator.py`: integridad determinista, diff semántico y revisión Gemini Pro.
- `agents/worker.py`: ejecución diaria a las 03:00 de Buenos Aires (06:00 UTC).
- `web/`: portada responsive Next.js que muestra el catálogo y su estado de verificación.
- `android/`: app preliminar Kotlin/Compose con catálogo offline, búsqueda, detalle y favoritos.
  Ver [android/README.md](android/README.md) para compilar y firmar el APK.

El catálogo contiene las 19 denominaciones pedidas. Empresas, jurisdicciones y vigencia
requieren verificación: el seed representa el alcance solicitado, no un padrón oficial.

Endpoints implementados: `GET /api/v1/lines`, `/api/v1/lines/{id}/branches`,
`/api/v1/lines/{id}/branches/{branch_id}/stops`, `/api/v1/stops/nearby`, `/api/v1/alerts`.
No se exponen rutas ficticias para el planificador ni la sincronización.

## Ejecutar el pipeline

1. Configurar `GEMINI_API_KEY` en `.env`; modelos configurables mediante variables.
2. Editar `agents/config/sources.json` con URLs finales verificadas de documentos de
   recorridos y sus hosts permitidos. La fuente incluida está **deshabilitada**: sirve
   para descubrimiento, no contiene por sí sola un dataset de recorridos completo.
3. Completar `agents/config/gazetteer.json` con objetos `canonical`, `lat`, `lon`,
   `source_url`. Una esquina no identifica necesariamente el lado o andén de una parada:
   antes de publicar deben revisarse ambos. No se usa una fórmula de cuadrícula para
   inventar coordenadas de diagonales o caminos.
4. Ejecutar:

```sh
docker compose run --rm worker python -m agents.worker --once
```

Los artefactos quedan en el volumen `pipeline_data`, bajo `/data/runs/<id>/`:
originales, metadatos, extracciones, candidato, revisión y estado. Un error conserva
el dataset publicado anterior. Un candidato aprobado por Gemini sigue en
`review_required`: la publicación transaccional es una etapa aún pendiente.
La comparación toma `/data/published.json` con estructura
`{"version":"0.1.0","dataset":{"branches":[...]}}` cuando existe.

Los avisos se conservan en `extractions.json`, sin publicación automática. Robots
inaccesible, redirecciones, PDFs e imágenes bloquean la fuente en esta versión;
requieren URL final o adaptador. No se descarta silenciosamente una fuente fallida.
El GeoJSON une paradas en orden y está marcado `stop_sequence_not_road_shape`:
**no es una traza vial**. No se exporta un GTFS incompleto sin horarios/calendarios.

## Pruebas

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
.venv/bin/python -m pytest -q
cd web
npm ci
npm run build
```

Las pruebas usan fixtures sintéticas y mocks, sin consumir Gemini ni fuentes oficiales.
No reemplazan pruebas de integración con PostGIS ni una auditoría de los datos.

## Siguientes etapas

Ver [docs/architecture.md](docs/architecture.md) para publicación, GTFS, routing,
sincronización, Android, PWA y controles de operación pendientes.

Referencias utilizadas: [Google GenAI SDK](https://googleapis.github.io/python-genai/),
[GTFS Schedule](https://gtfs.org/documentation/schedule/reference/),
[directorio oficial PBA](https://gba.gob.ar/transporte/transporte_de_pasajeros/listado_de_empresas).
