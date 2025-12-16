FROM python:3.10

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    binutils \
    libproj-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir pipenv

COPY Pipfile Pipfile.lock /app/
RUN pipenv install --system --deploy --dev  # Agrega --dev para dependencias de desarrollo

COPY . /app/

EXPOSE 8000

# En desarrollo el comando lo sobrescribe el compose
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]