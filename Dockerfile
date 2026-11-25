FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

COPY codigo ./codigo
COPY datos ./datos
COPY assets ./assets

RUN useradd --create-home --uid 10001 zoonauta \
    && mkdir -p /app/registros/interfaz \
    && chown -R zoonauta:zoonauta /app/registros

USER zoonauta

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8000\")}/healthz', timeout=3)"

CMD ["python", "-m", "codigo.interfaz.servidor", "--host", "0.0.0.0"]
