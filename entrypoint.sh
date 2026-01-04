#!/bin/bash
set -e

echo "========================================="
echo "==> Iniciando entrypoint de la aplicación"
echo "========================================="

# Función para esperar a que la base de datos esté disponible
wait_for_db() {
    echo "==> Esperando a que la base de datos esté disponible..."
    echo "==> Configuración de BD:"
    echo "    DB_HOST: ${DB_HOST}"
    echo "    DB_NAME: ${DB_NAME}"
    echo "    DB_USER: ${DB_USER}"
    echo "    DB_PORT: ${DB_PORT:-5432}"
    
    python << END
import sys
import time
import psycopg2
import os

max_retries = 60
retry_count = 0

db_config = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '5432')
}

print(f"Intentando conectar a: {db_config['host']}:{db_config['port']}/{db_config['dbname']}")

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(**db_config)
        conn.close()
        print("✓ Base de datos disponible")
        sys.exit(0)
    except psycopg2.OperationalError as e:
        retry_count += 1
        print(f"⏳ Error: {str(e)}")
        print(f"   Intento {retry_count}/{max_retries}")
        time.sleep(3)
    except Exception as e:
        print(f"✗ Error inesperado: {str(e)}")
        sys.exit(1)

print("✗ No se pudo conectar a la base de datos después de", max_retries, "intentos")
sys.exit(1)
END
}

# Función para ejecutar migraciones
run_migrations() {
    echo "==> Ejecutando migraciones de base de datos..."
    python manage.py migrate --noinput
    
    if [ $? -eq 0 ]; then
        echo "✓ Migraciones completadas exitosamente"
    else
        echo "✗ Error al ejecutar migraciones"
        exit 1
    fi
}

# Función para recolectar archivos estáticos
collect_static() {
    echo "==> Recolectando archivos estáticos..."
    python manage.py collectstatic --noinput
    
    if [ $? -eq 0 ]; then
        echo "✓ Archivos estáticos recolectados"
    else
        echo "⚠ Warning: Error al recolectar archivos estáticos (continuando...)"
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