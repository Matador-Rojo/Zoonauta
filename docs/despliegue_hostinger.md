# Despliegue de Zoonauta en Hostinger

Zoonauta 6.0 corre únicamente con Python estándar (`3.11+`, cero dependencias `pip`) y ya está optimizado para producción web:

- **HTTPS / Proxy reverso:** acepta `Origin` en `https://`, lee `X-Forwarded-Proto` / `X-Forwarded-Host` y marca cookies como `Secure` en HTTPS.
- **Caché HTTP y compresión:** `gzip` automático en JSON/HTML/JS/CSS/SVG, `ETag` + `304 Not Modified` en imágenes y videos (`max-age=604800`), `Cache-Control` en audios de voz (`max-age=86400`), y streaming real por rango (`206 Partial Content`) en videos de portada.
- **Control de memoria:** expiración automática de sesiones inactivas (`TTL = 2 h`, tope de `500` sesiones concurrentes) y ruta de salud `/healthz`.
- **Medios optimizados:** 1 236 audios de voz en MP3 mono `24 kHz / 56 kbps`, videos de portada H.264 `faststart` sin pista de audio, e imágenes ligeras WebP (`pictogramas_ligeros`, `paisajes_ligeros`, `ilustraciones_ligeras`).

## Opción 1 (recomendada): Hostinger VPS con Docker Manager / `docker compose`

1. Sube la carpeta del proyecto (o `Zoonauta-6.0-Hostinger.zip`) a tu VPS o conecta tu repositorio Git en **hPanel → VPS → Docker Manager**.
2. Levanta el servicio con el `docker-compose.yml` incluido:
   ```bash
   docker compose up -d --build
   ```
3. Verifica que responde en el puerto `8000`:
   ```bash
   curl http://127.0.0.1:8000/healthz
   ```
4. Apunta tu dominio (con SSL/HTTPS de Hostinger o Nginx/Caddy/Traefik) a `http://127.0.0.1:8000` reenviando las cabeceras estándar `Host` y `X-Forwarded-Proto`.

## Opción 2: Hostinger VPS sin Docker (Python directo + `systemd`)

```bash
HOST=0.0.0.0 PORT=8000 python3 -m codigo.interfaz.servidor --host 0.0.0.0 --puerto 8000
```

Con Nginx como proxy HTTPS delante:

```nginx
server {
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```
