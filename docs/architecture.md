# Diseño incremental

## Ingesta y publicación

Fuentes oficiales → archivo inmutable → extracción Flash → normalización Flash +
nomenclátor → controles deterministas → revisión Pro → candidato → publicación.
Cada candidato conserva URL, fecha y hash para reproducir su origen. La evidencia literal
reduce errores, pero no prueba que cada campo extraído sea correcto; hace falta revisión.
No se acepta pérdida de ramales por caída de una fuente. Umbral de salto de 10 km obliga
a revisión, incluso cuando pueda ser válido para servicios interurbanos.

Pendiente: adaptadores PDF/GTFS/avisos oficiales, nomenclátor geográfico completo,
resolución de conflictos entre fuentes y cobertura por línea. La publicación deberá
validar claves y horarios, adquirir un advisory lock PostgreSQL y actualizar tablas,
versión y `sync_changes` en una sola transacción. Un outbox notificará cambios después
del commit e invalidará cachés; Redis no será fuente de verdad. El scheduler actual
requiere una sola réplica; para escalar se necesita cola persistente y bloqueo distribuido.
Las versiones suben major al eliminar/reordenar paradas, minor al agregar ramales y
patch al cambiar metadatos. `0.0.0` representa ausencia de datos.

## GTFS y planificación

Implementar exportación validada de agency, routes, trips, stops, stop_times,
calendar/calendar_dates, frequencies y shapes solo con información suficiente.
Mantener servicio por fecha local y tiempos GTFS mayores de 24 h. Los feriados se
modelan con excepciones; no inferirlos con una lista fija de días de semana.
El filtro 00–05 considera viajes del día anterior que continúan después de medianoche.

El motor temporal (RAPTOR o CSA) calculará viajes y transbordos sobre la versión
publicada; un grafo peatonal calculará caminata real. Gemini traducirá la consulta
natural a parámetros y explicará resultados, sin generar servicios u horarios.
Sin GPS/GTFS-RT, los tiempos serán programados, nunca presentados como arribos reales.

## Clientes y offline

Android: HomeScreen y LineDetailScreen implementadas en Kotlin/Compose para el catálogo
preliminar; favoritos con SharedPreferences y estado en ViewModel. Hilt, Room,
WorkManager y MapRouteScreen siguen pendientes. MapLibre con paquetes de teselas de un
proveedor cuya licencia permita descarga. Room recibirá un snapshot SQLite inicial
y deltas con tombstones y versiones base/destino, aplicados atómicamente.

Web: ampliar portada a MapComponent, RouteSidebar y StopSelector; Tailwind/Lucide,
Workbox, manifest y persistencia IndexedDB pendientes. Separar caché de assets de
consultas versionadas; mostrar fecha del dataset y estado offline. La portada actual
no es aún una PWA instalable.

Favoritos persistidos localmente; alertas vinculadas por línea/ramal. Reportes ciudadanos
requieren identidad verificada, límites de uso y moderación Gemini antes de publicación.
SUBE será un cálculo orientativo basado en tarifas vigentes y enlaces oficiales;
la recarga NFC depende de una integración autorizada y no se simulará.

## Operación pendiente

Migraciones SQL incrementales, roles separados lectura/escritura, backup/restauración,
pruebas PostGIS reales, lockfiles Python, observabilidad de frescura y cobertura,
reintentos de descarga, cola durable, autenticación para reportes y límites de API.
Los contenedores API/worker/web ejecutan como usuarios sin privilegios. El crawler
admite solo configuración local confiable: su filtro DNS no reemplaza restricciones
de egress de red frente a DNS rebinding. Ninguna URL ingresada por usuarios llega a él.
