FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
COPY backend ./backend
COPY agents ./agents
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 bondi && mkdir /data && chown bondi:bondi /data
USER bondi
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
