# Validación de la primera etapa

- Python 3.14.7: 19 pruebas aprobadas (parser, nomenclátor, anomalías, diff,
  GeoJSON, fuentes, conservación del dataset y contrato HTTP con mocks).
- `compileall`: sin errores sintácticos.
- Compose: YAML parseado y cinco servicios presentes. Docker no está instalado en
  el entorno de trabajo; no se ejecutaron contenedores ni consultas PostGIS reales.
- Gemini: integración escrita contra Google GenAI SDK; sin llamadas reales porque
  no se configuró una clave ni fuentes de recorridos habilitadas.
- `npm run build`: compilación de producción completada con Next.js 16.3.5.
- Next.js: dependencias actualizadas a 16.3.5; instalación auditada sin vulnerabilidades
  reportadas por npm. El lockfile fija la resolución usada.

Las pruebas de API usan ASGITransport asíncrono dentro del proceso, sin levantar red
ni conectar PostgreSQL. La primera ejecución con TestClient síncrono se bloqueó en
el puente de hilos del entorno; se reemplazó conservando los casos HTTP y aserciones.
