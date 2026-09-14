# Bondi · Gran La Plata

Plataforma integral de transporte público para el Gran La Plata (La Plata, Berisso y Ensenada).

Comprende un **pipeline automatizado de subagentes con la API de Gemini**, backend de alto rendimiento en **FastAPI + PostgreSQL/PostGIS + Redis**, app nativa para **Android en Kotlin/Jetpack Compose** y versión web móvil **PWA en Next.js**.

---

## 📲 Descarga de la App Android

- ⬇️ **Descarga directa del APK**: [bondi-0.4.0-alpha.1.apk](https://github.com/LW1EXU/bondi/releases/download/v0.4.0-alpha.1/bondi-0.4.0-alpha.1.apk)
- 🏷️ **Notas de la versión**: [GitHub Releases v0.4.0-alpha.1](https://github.com/LW1EXU/bondi/releases/tag/v0.4.0-alpha.1)
- 🔒 **Firma**: Verificada oficialmente con `apksigner` (Esquemas APK Signature v2 y v3 compatibles con Android 11 a 15+).

---

## 🏛️ Arquitectura del Sistema

```
                         ┌─────────────────────────────────┐
                         │   Fuentes Oficiales / Portales  │
                         └────────────────┬────────────────┘
                                          │
                                 [1] CRAWLER AGENT
                                          │
                                 [2] NORMALIZER AGENT
                           (Cuadrícula Platense + Gemini API)
                                          │
                                 [3] VALIDATOR & DIFF
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │    PostgreSQL 16 + PostGIS Spatial    │
                      │  (Paradas, Ramales, GTFS, Deltas)     │
                      └───────┬───────────────────────┬───────┘
                              │                       │
                              ▼                       ▼
                     ┌────────────────┐       ┌───────────────┐
                     │  Redis 7 Cache │       │ RAG TRAVEL AG.│
                     └────────┬───────┘       └───────┬───────┘
                              │                       │
                              ▼                       ▼
                 ┌─────────────────────────────────────────────────┐
                 │          FastAPI Backend REST & GeoJSON         │
                 │   /lines · /stops · /plan · /travel-assistant   │
                 └──────────────┬───────────────────┬──────────────┘
                                │                   │
                                ▼                   ▼
        ┌───────────────────────────────┐   ┌───────────────────────────────┐
        │     Android Nativo (Kotlin)   │   │      Next.js 16 Web / PWA     │
        │ • Compose + SQLite Offline    │   │ • Leaflet interactivo         │
        │ • Buscador "7 y 50", Diag. 74 │   │ • Contador en vivo (min:seg)  │
        │ • Calculadora SUBE + Atajo NFC│   │ • Asistente RAG integrado     │
        │ • Notificaciones y Alertas    │   │ • Workbox Service Worker      │
        └───────────────────────────────┘   └───────────────────────────────┘
```

---

## 1. Pipeline de Subagentes (`/agents`)

- **Subagente Scraper & Crawler (`agents/crawler.py`)**: Rastreo acotado y seguro con validación de hosts, `robots.txt` y archivado inmutable con hash SHA-256 para las 19 líneas:
  * Comunales: **506, 518, 520, 561, Este, Oeste, Norte, Sur**.
  * Provinciales: **273, 275, 214, 307, 202, 215, 418, 414, 129, 195**.
  * Especiales: **Rondín Universitario UNLP**.
- **Subagente Normalizador (`agents/normalizer.py`)**: Parser geográfico platense que interpreta direcciones numéricas (*"7 y 50"*, *"60 y 137"*), diagonales (*"Diag. 74"*) y puntos de interés (facultades, hospitales, terminales y plazas). Genera capas GeoJSON y secuencias GTFS.
- **Subagente Verificador & Diff (`agents/validator.py`)**: Control topológico de integridad, detección de anomalías y saltos anómalos (>10 km) y versionado semántico de la red.
- **Subagente RAG de Viaje (`agents/rag_planner.py`)**: Motor de planificación multimodal en lenguaje natural. Interpreta origen y destino, evalúa conexiones directas o con 1 transbordo a través de nodos clave (Plaza San Martín, Plaza Moreno, Plaza Italia, Estación La Plata, etc.), calcula tramos peatonales e instruye paso a paso.

---

## 2. Backend & API (`/backend`)

Desarrollado en **FastAPI**, **PostgreSQL 16 / PostGIS** y **Redis**:
- `GET /api/v1/lines?type=comunal|provincial|especial`: Catálogo agrupado y filtrable con caché en Redis.
- `GET /api/v1/stops/nearby?lat={lat}&lon={lon}&radius={m}`: Búsqueda geoespacial mediante `ST_DWithin`.
- `GET /api/v1/stops/{id}/arrivals`: Arribos y frecuencias en tiempo real con cuenta regresiva en segundos.
- `GET /api/v1/lines/{id}/branches` y `/stops`: Trazado secuencial de paradas por ramal.
- `POST /api/v1/plan`: Planificador de rutas punto a punto con tramos de caminata y micros.
- `POST /api/v1/travel-assistant`: Subagente RAG para consultas en lenguaje natural (*"cómo voy de 7 y 50 a la facultad de informática"*).
- `GET /api/v1/sync/deltas`: Endpoint para sincronización delta y funcionamiento 100% offline.
- `GET /api/v1/alerts`: Alertas y desvíos activos moderados.

---

## 3. App Nativa Android (`/android`)

- **Kotlin + Jetpack Compose** con arquitectura Clean + MVVM.
- **Buscador Platense**: Optimizado para la cuadrícula y diagonales de La Plata.
- **Persistencia Offline**: Base de datos SQLite local (`BondiDbHelper`) para almacenamiento de favoritos y catálogo sin conexión a Internet.
- **Pestañas**:
  1. **Líneas**: Consulta de ramales, cabeceras, frecuencias y paradas de las 19 líneas.
  2. **Paradas**: Directorio georreferenciado con cuenta regresiva en vivo de cada micro.
  3. **SUBE / NFC**: Calculadora de pasajes según saldo actual ($371,13 comunal, $413,44 provincial), saldo de emergencia (-$480) y atajo a acreditación por NFC.
  4. **Alertas**: Notificaciones de desvíos y cortes de tránsito en La Plata.

---

## 4. Versión Web / PWA (`/web`)

- **Next.js 16 + Tailwind CSS (Mobile-First)**.
- **Mapa interactivo Leaflet**: Trazado de recorridos, marcadores interactivos y selector de paradas.
- **Temporizador en vivo**: Cuenta regresiva en minutos y segundos hacia el próximo micro.
- **Asistente de Viaje RAG**: Consultas directas de viaje con detalle paso a paso de transbordos y caminatas.
- **Panel colapsable de frecuencias**:
  - Horario diurno (pico 6-10 min, valle 10-14 min).
  - Horario nocturno (rondines cada 30-45 min).
  - Días no hábiles (sábados 12-18 min, domingos y feriados 20-30 min).
- **Service Worker PWA (Workbox)**: Cache de mapas, recursos estáticos y funcionamiento offline.

---

## 🚀 Inicio Rápido con Docker

```sh
# 1. Clonar el repositorio
git clone https://github.com/LW1EXU/bondi.git
cd bondi

# 2. Levantar todos los servicios (PostGIS, Redis, FastAPI, Worker y Next.js)
docker compose up --build
```

- **Frontend Web**: http://localhost:3000
- **Documentación API (Swagger/OpenAPI)**: http://localhost:8000/docs

---

## 🧪 Pruebas Unitarias y Validación

```sh
# Pruebas del Backend y Pipeline de Agentes (33 tests)
.venv/bin/pytest -v

# Compilación y verificación del Frontend Web
cd web && npm run build

# Pruebas y compilación de la App Android
cd android
./gradlew testDebugUnitTest assembleRelease
```
