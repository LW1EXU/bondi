# Bondi v0.3.0-alpha.1

Versión mayor de la plataforma integral **Bondi** para el transporte público del Gran La Plata (La Plata, Berisso y Ensenada).

Esta versión completa todos los requerimientos de la especificación técnica: pipeline de subagentes con Gemini API, backend geoespacial en FastAPI, cliente nativo Android en Kotlin/Jetpack Compose, y aplicación web móvil (PWA) en Next.js.

---

## 1. Pipeline de Subagentes (`/agents`)
- **Subagente RAG de Viaje (`agents/rag_planner.py`)**:
  - Resuelve consultas en lenguaje natural (*"cómo voy de 7 y 50 a la facultad de informática"*).
  - Parser geográfico que interpreta nomenclaturas de la cuadrícula platense: calles numéricas (*"7 y 50"*, *"60 y 137"*), diagonales (*"Diag. 74"*), avenidas y caminos (*"Cno. Centenario y 502"*), y puntos de interés (facultades de la UNLP, hospitales, terminales y plazas).
  - Algoritmo de ruteo multimodal que evalúa recorridos directos y con 1 transbordo a través de nodos clave (Plaza Moreno, Plaza San Martín, Plaza Italia, Estación de Trenes, Hospitales), ponderando distancias a pie y tiempos de espera.
  - Genera instrucciones paso a paso estructuradas y texto explicativo en lenguaje natural mediante la API de Gemini (con fallback determinístico local).
- **Subagente Scraper & Crawler (`agents/crawler.py`)**:
  - Rastreo programado de recorridos, ramales, frecuencias y avisos para las 19 líneas del Gran La Plata.
- **Subagente Normalizador (`agents/normalizer.py`)**:
  - Canonicalización de direcciones platenses y generación de datasets GeoJSON.
- **Subagente Verificador & Diff (`agents/validator.py`)**:
  - Control de anomalías, integridad topológica, saltos geográficos y versionado semántico de datasets.

---

## 2. Backend & API (`/backend`)
- **FastAPI + PostGIS + Redis**:
  - `GET /api/v1/lines?type=comunal|provincial|especial`: Listado de líneas con filtrado por tipo y soporte de caché en Redis.
  - `GET /api/v1/stops/nearby?lat=...&lon=...&radius=...`: Búsqueda espacial de paradas por radio en metros mediante `ST_DWithin`.
  - `GET /api/v1/stops/{id}/arrivals`: Arribos estimados en tiempo real con cuenta regresiva en segundos para cada línea.
  - `GET /api/v1/lines/{id}/branches` y `/stops`: Secuencias ordenadas de paradas por ramal.
  - `POST /api/v1/plan`: Planificador de rutas punto a punto con tramos de caminata y micros.
  - `POST /api/v1/travel-assistant`: Endpoint en lenguaje natural para el asistente RAG de viaje.
  - `GET /api/v1/sync/deltas`: Endpoint de sincronización delta para funcionamiento 100% offline.

---

## 3. App Nativa Android (`/android`)
- **Kotlin + Jetpack Compose (MVVM + Clean Architecture)**:
  - **Buscador Platense**: Optimizado para la cuadrícula de calles y diagonales de La Plata (reconoce intersecciones como *"7 y 50"* y lugares clave).
  - **Persistencia Offline**: Base de datos SQLite (`BondiDbHelper`) para almacenamiento local de favoritos y catálogo sin conexión a Internet.
  - **Navegación por pestañas**:
    - **Líneas**: Catálogo completo de las 19 líneas con filtros (Todas, Favoritos, Comunales, Provinciales), cabeceras y trazado secuencial de paradas.
    - **Paradas**: Directorio de las 33 paradas del Gran La Plata con arribos y cuentas regresivas en vivo.
    - **SUBE / NFC**: Calculadora orientativa de viajes según tarifa comunal ($371,13) y provincial ($413,44), visualización del saldo negativo de emergencia (-$480) y botón con atajo a NFC para lectura y acreditación de saldo.
    - **Alertas**: Notificaciones y avisos de desvíos u obras viales en Gran La Plata.
  - **Firma digital Android**:
    - Compilación firmada oficialmente con Keystore `bondi-preview`.
    - Esquemas de firma APK v2 y v3 validados con `apksigner` para compatibilidad con Android 11 a 15+.

---

## 4. Web Frontend / PWA (`/web`)
- **Next.js 16 + Tailwind CSS (Mobile-First)**:
  - Mapa interactivo con Leaflet que representa las 33 paradas y el trazado de líneas.
  - Reloj en tiempo real y contador regresivo en vivo (*"En camino"*, *"🟢 Llegando"* o cuenta regresiva min:seg).
  - **Asistente RAG de Viaje integrado**: Formulario interactivo para consultar cómo viajar entre cualquier punto de La Plata con desglose visual de tramos.
  - **Panel colapsable de frecuencias**:
    - Diurnas: Horas pico (6 a 10 min) y valle (10 a 14 min).
    - Nocturnas: Servicios de guardia y rondines cada 30 a 45 min (líneas 24hs).
    - Días no hábiles: Sábados (12 a 18 min) y domingos/feriados (20 a 30 min).
  - **Service Worker PWA con Workbox (`/sw.js`) y `manifest.json`**:
    - Estrategias de caché para mapas y catálogo offline.
    - Instalable en pantalla de inicio de Android e iOS.

---

## 5. Artefactos y Verificación
- **APK Release**: `artifacts/bondi-0.3.0-alpha.1.apk`
- **Sumas de comprobación**: `artifacts/SHA256SUMS.txt`
- **Suite de pruebas**: 33 pruebas unitarias de backend y agentes pasando al 100% (`pytest`).
- **Pruebas Android**: Pruebas unitarias de catálogo y algoritmos pasando en JVM (`testDebugUnitTest`).
- **Build Web**: Compilación estática Next.js verificada con 0 errores y 0 advertencias (`npm run build`).
