FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=manza_spots.settings

WORKDIR /app

# Dependencias de sistema para GeoDjango (GDAL/GEOS/PROJ) + Postgres
# Se quedan en la imagen final porque django.contrib.gis carga estas
# librerias en tiempo de ejecucion via ctypes, no solo al compilar.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    binutils \
    libproj-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . /app/

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Usuario sin privilegios (seguridad) — igual que en Coleccion Lorenza
RUN useradd --no-create-home --shell /bin/false django \
    && mkdir -p /app/staticfiles /app/logs /app/media \
    && chown -R django:django /app /entrypoint.sh

USER django

EXPOSE 8000

# Railway inyecta $PORT automaticamente (normalmente 8000)
CMD ["/entrypoint.sh"]