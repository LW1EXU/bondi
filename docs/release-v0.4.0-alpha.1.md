# Bondi v0.4.0-alpha.1 — Telemetría en Vivo, Headway Engine y Búsqueda "¿Cuándo llega?"

Versión mayor de la plataforma integral **Bondi** para el transporte público del Gran La Plata (La Plata, Berisso y Ensenada), incorporando el subsistema completo de telemetría y predicción de arribos idéntico a "¿Cuándo llega mi micro?", búsqueda por intersección de calles y catalogación de las 21 líneas.

---

## 1. Subsistema de Arribos y Telemetría en Tiempo Real
- **Endpoint "¿Cuándo llega mi micro?" (`GET /api/v1/stops/{stop_code}/arrivals`)**:
  - Consulta los micros próximos a pasar por la parada mediante su código numérico unificado visible en el cartel de la esquina (ej. Parada 1735 en Calle 1 y 42).
  - Devuelve para cada unidad: línea, ramal, destino final, tiempo estimado de llegada en minutos (`eta_minutes`), texto legible (`eta_text`), distancia en metros (`distance_meters`) y estado de telemetría (`is_realtime`).
  - **Soporte de telemetría satelital GPS en vivo**: Consulta a la API municipal de arribos con timeout estricto de 2.5s.
  - **Headway Estimation Engine (Fallback Inteligente)**: Ante cortes de enlace satelital o indisponibilidad de la API municipal, proyecta de forma determinista el arribo empleando cronogramas oficiales por franja y velocidades históricas de corredor (12 km/h en casco urbano, 25 km/h en avenidas).

- **Buscador de Paradas por Intersección (`GET /api/v1/stops/lookup?street={street}&cross={cross}`)**:
  - Permite al usuario encontrar una parada tipeando las dos calles que forman la esquina (ej. `street=1&cross=42` o `street=Calle 1&cross=Calle 42`).
  - Normalizador platense que interpreta prefijos y números en cualquier orden.
  - Retorna el `stop_code`, coordenadas geográficas PostGIS, zona y lista de líneas que pasan por dicho poste.

---

## 2. Crawler de Cronogramas Oficiales (`/agents/schedule_crawler.py`)
- Mapeo estructurado de frecuencias y horarios de despacho para las 21 líneas de Gran La Plata:
  - **Unión Platense S.R.L.**: 273, 214, 418, 520, Norte, Sur.
  - **Empresa Línea 7 S.A.T.**: 307, 561, Oeste.
  - **TALP S.A.**: Línea 338 (Ruta 4 / Camino de Cintura).
  - **Interurbanas Autopista**: 195 (Metropol) y 129 (Misión Buenos Aires).
  - **Comunales y Provinciales**: 506, 518, 275, 215, 414, 508, Este, 202 y Rondín UNLP.
- Desglose por días tipo (`HABIL`, `SABADO`, `DOMINGO_FERIADO`) y franjas horarias (`PICO_MANANA`, `VALLE`, `PICO_TARDE`, `NOCTURNO`).
- Almacenamiento sincronizado en `scheduled_timetables` y exportación JSON.

---

## 3. Modelo de Datos y Esquema PostGIS (`schema.sql`)
- Ampliación de la tabla `stops` con `stop_code INT UNIQUE`, `street`, `cross_street`, `intersection`, coordenadas `geom geometry(Point, 4326)` y `zone`.
- Nueva tabla `stop_routes`: Relación muchos a muchos de postes físicos a ramales de líneas.
- Nueva tabla `scheduled_timetables`: Matriz de frecuencias y primeros/últimos despachos.

---

## 4. App Nativa Android (`/android`)
- **Versión 0.4.0-alpha.1 (versionCode 4)**.
- Catálogo actualizado con las 21 líneas platenses (incorporando la Línea 508 y la Línea 338).
- Registro de Parada 1735 (Calle 1 y Calle 42) y trazados asociados.
- **Firma digital Android**:
  - Compilado release firmado con keystore oficial `bondi-preview`.
  - Verificado con `apksigner` bajo los esquemas **v2** y **v3** para compatibilidad con Android 11 a 15+.
  - Resuelve incidencias de validación en instaladores de paquetes móviles.

---

## 5. Web Frontend / PWA (`/web`)
- Actualización de enlaces directos de descarga del APK release v0.4.0-alpha.1.
- Mapa interactivo con visualización de paradas y tiempos de llegada.
- Compilación de producción estática en Next.js verificada sin errores.

---

## 6. Artefactos y Verificación
- **Descarga directa del APK**: [`bondi-0.4.0-alpha.1.apk`](https://github.com/LW1EXU/bondi/releases/download/v0.4.0-alpha.1/bondi-0.4.0-alpha.1.apk)
- **Sumas de comprobación SHA-256**: `SHA256SUMS.txt`
  - `dd8dd44c88d8fc73bc32d4394ef9624d903a10be283e8385856f6e08ee7923e4  bondi-0.4.0-alpha.1.apk`
- **Suite de Pruebas**: 42 tests unitarios y de integración pasando al 100% en `pytest` (`agents/tests/test_telemetry.py`).
- **Pruebas Android JVM**: Pruebas unitarias de catálogo y algoritmos pasando al 100% (`testDebugUnitTest`).
