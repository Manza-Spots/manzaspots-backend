#!/bin/bash
set -e

echo "========================================="
echo "==> Iniciando entrypoint de la aplicación"
echo "========================================="

# Función para esperar a que la base de datos esté disponible
wait_for_db() {
    echo "==> Esperando a que la base de datos esté disponible..."
    
    python << END
import sys
import time
import psycopg2
from decouple import config

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(
            dbname=config('DB_NAME'),
            user=config('DB_USER'),
            password=config('DB_PASSWORD'),
            host=config('DB_HOST'),
            port=config('DB_PORT', default=5432)
        )
        conn.close()
        print("Base de datos disponible")
        sys.exit(0)
    except psycopg2.OperationalError as e:
        retry_count += 1
        print(f"Esperando base de datos... intento {retry_count}/{max_retries}")
        time.sleep(2)

print("No se pudo conectar a la base de datos después de", max_retries, "intentos")
sys.exit(1)
END
}

# Función para ejecutar migraciones
run_migrations() {
    echo "==> Ejecutando migraciones de base de datos..."
    python manage.py migrate --noinput
    
    if [ $? -eq 0 ]; then
        echo "Migraciones completadas exitosamente"
    else
        echo "Error al ejecutar migraciones"
        exit 1
    fi
}

# Función para recolectar archivos estáticos
collect_static() {
    echo "==> Recolectando archivos estáticos..."
    python manage.py collectstatic --noinput
    
    if [ $? -eq 0 ]; then
        echo "Archivos estáticos recolectados"
    else
        echo "Warning: Error al recolectar archivos estáticos (continuando...)"
    fi
}

# Función principal
main() {
    wait_for_db
    run_migrations
    collect_static
    
    echo "========================================="
    echo "==> Iniciando servidor de aplicación"
    echo "========================================="
    
    # Ejecutar el comando pasado como argumento
    exec "$@"
}

# Ejecutar función principal
main "$@"