# Despliegue web de Zoonauta (PythonAnywhere, Hostinger VPS, Render y Docker)

Zoonauta corre únicamente con Python estándar (`3.10+`, cero dependencias `pip`) y está preparado
para producción web manteniendo intactos el núcleo en Python, los registros `.jsonl` y el panel
de observación `/revision`:

- **HTTPS / Proxy reverso:** acepta `Origin` en `https://`, lee `X-Forwarded-Proto` / `X-Forwarded-Host` y marca cookies como `Secure` en HTTPS.
- **Adaptador WSGI sin dependencias:** `codigo.interfaz.wsgi:application` listo para PythonAnywhere, Gunicorn o servidores WSGI.
- **Caché HTTP y compresión:** `gzip` automático en JSON/HTML/JS/CSS/SVG, `ETag` + `304 Not Modified` en imágenes (`max-age=604800`) y `Cache-Control` en audios de voz (`max-age=86400`).
- **Control de memoria:** expiración automática de sesiones inactivas (`TTL = 2 h`, tope de `500` sesiones concurrentes) y ruta de salud `/healthz`.
- **Paquete web optimizado (`Zoonauta-Web.zip`, ~70 MB):** incluye el frontend compilado (`web6/`) con portadas WebP 2K (`1672 × 941`) + atmósfera viva `<BosqueVivo />` sin archivos de video, imágenes ligeras WebP (`pictogramas_ligeros`, `paisajes_ligeros`, `ilustraciones_ligeras`, sin duplicados de `assets/animales/`), y las **8 voces completas** (`3 296` audios: 4 ES, 2 PT-BR, 2 EN) convertidas a **AAC-LC 32 kbps mono `.m4a`** (`audio/mp4`, `24 kHz`, `+faststart`).

## Opción 1 (gratuita y más rápida): PythonAnywhere (WSGI)

Ideal para demos y sustentación: el plan gratuito ofrece `512 MB` de espacio (`Zoonauta-Web.zip`
ocupa solo ~76 MB descomprimido) y no «duerme» el servidor.

1. En la consola **Bash** de PythonAnywhere, descarga y descomprime el paquete web del Release:
   ```bash
   wget https://github.com/Matador-Rojo/Zoonauta/releases/download/v1.0.0/Zoonauta-Web.zip
   unzip Zoonauta-Web.zip
   rm Zoonauta-Web.zip
   ```
2. En **Web → Add a new web app**, elige **Manual configuration** y **Python 3.10+** (3.11 / 3.12 / 3.13).
3. Abre el archivo **WSGI configuration file** (`/var/www/<usuario>_pythonanywhere_com_wsgi.py`) y deja solo:
   ```python
   import sys
   sys.path.insert(0, '/home/<usuario>/Zoonauta-Web')
   from codigo.interfaz.wsgi import application
   ```
4. Guarda y pulsa **Reload `<usuario>.pythonanywhere.com`**. Verifica `/`, `/healthz` y `/revision`.

## Opción 2: Hostinger VPS (Docker Manager / `docker compose`)

> **Nota sobre Hostinger:** los planes de Web Hosting compartido (Premium / Business / Unlimited)
> solo ejecutan PHP, sitios estáticos y Node.js; para correr el servidor Python de Zoonauta en
> Hostinger se requiere un plan **Hostinger VPS (KVM)**.

1. Sube `Zoonauta-Web.zip` (o conecta el repositorio Git) en **hPanel → VPS → Docker Manager**.
2. Levanta el servicio con el `docker-compose.yml` incluido:
   ```bash
   docker compose up -d --build
   ```
3. Verifica que responde en el puerto `8000`:
   ```bash
   curl http://127.0.0.1:8000/healthz
   ```
4. Apunta tu dominio (con SSL/HTTPS) a `http://127.0.0.1:8000` reenviando `Host` y `X-Forwarded-Proto`.

## Opción 3: VPS Linux sin Docker (Python directo + Nginx)

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

## Opción 4: Render (Docker directo desde GitHub)

Crea un **Web Service** conectado al repositorio `Matador-Rojo/Zoonauta` seleccionando el entorno
**Docker** (utiliza el `Dockerfile` de la raíz). Acepta dominio propio con HTTPS gratuito; en el plan
gratuito el contenedor entra en reposo tras 15 minutos sin tráfico.
