# Imagen base de Python
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias del sistema para GDAL y PostgreSQL
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    binutils \
    libproj-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Instalar pipenv
RUN pip install --no-cache-dir pipenv

# Copiar Pipenv primero (para cache)
COPY Pipfile Pipfile.lock /app/

# Instalar dependencias dentro del sistema (no virtualenv)
RUN pipenv install --system --deploy

# Copiar el resto del proyecto
COPY . /app/

# Exponer puerto 8000
EXPOSE 8000

# Comando para ejecutar con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "manza_spots.wsgi:application"]
