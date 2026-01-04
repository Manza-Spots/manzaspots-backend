pipeline {
    agent any

    environment {
        SSH_USER = "ec2-user"
        API_HOST = "10.0.3.30"
        APP_DIR  = "/opt/manzaspots/api"
    }

    stages {

        stage("Checkout") {
            steps {
                checkout scm
            }
        }

        stage("Deploy API DEV") {
            when {
                branch "develop"
            }

            steps {
                sshagent(credentials: ['api-ssh']) {
                    sh """
                    ssh -o StrictHostKeyChecking=no ${SSH_USER}@${API_HOST} '
                        set -e

                        echo "========================================="
                        echo "==> Iniciando deploy de API DEV"
                        echo "========================================="
                        
                        # Limpiar backups viejos al inicio
                        cd /opt/manzaspots
                        ls -dt api_backup_* 2>/dev/null | tail -n +3 | xargs rm -rf 2>/dev/null || true
                        
                        # Crear backup del directorio actual
                        BACKUP_DIR="${APP_DIR}_backup_\$(date +%Y%m%d_%H%M%S)"
                        if [ -d ${APP_DIR} ]; then
                            echo "==> Creando backup en \$BACKUP_DIR"
                            cp -r ${APP_DIR} \$BACKUP_DIR
                        fi

                        # Crear directorio temporal
                        TEMP_DIR=\$(mktemp -d)
                        
                        # Función de limpieza y rollback en caso de error
                        cleanup_and_rollback() {
                            local exit_code=\$?
                            echo "========================================="
                            echo "==> ERROR: Deploy falló con código \$exit_code"
                            echo "==> Iniciando rollback automático"
                            echo "========================================="
                            
                            # Limpiar temporal
                            rm -rf \$TEMP_DIR
                            
                            if [ -d \$BACKUP_DIR ]; then
                                echo "==> Parando contenedores fallidos"
                                cd ${APP_DIR}
                                docker compose -f docker-compose.dev.yml down || true
                                
                                echo "==> Restaurando backup"
                                cd /opt/manzaspots
                                rm -rf ${APP_DIR}
                                mv \$BACKUP_DIR ${APP_DIR}
                                
                                echo "==> Levantando contenedores con versión anterior"
                                cd ${APP_DIR}
                                docker compose -f docker-compose.dev.yml up -d
                                
                                echo "==> Verificando rollback"
                                sleep 10
                                if docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
                                    echo "Rollback completado exitosamente"
                                else
                                    echo "WARNING: Rollback puede haber fallado, verificar manualmente"
                                    docker compose -f docker-compose.dev.yml logs --tail=50
                                fi
                            else
                                echo "No hay backup disponible para rollback"
                            fi
                            
                            exit 1
                        }
                        
                        # Registrar función de rollback para errores
                        trap cleanup_and_rollback ERR

                        echo "==> Clonando repositorio en temporal"
                        git clone -b develop --depth 1 ${GIT_URL} \$TEMP_DIR

                        echo "==> Parando contenedores actuales"
                        if [ -d ${APP_DIR} ]; then
                            cd ${APP_DIR}
                            docker compose -f docker-compose.dev.yml down || true
                        fi

                        # Guardar .env si existe
                        if [ -f ${APP_DIR}/.env ]; then
                            cp ${APP_DIR}/.env /tmp/.env.backup
                        fi

                        echo "==> Copiando nuevos archivos"
                        mkdir -p ${APP_DIR}
                        rsync -av --delete \
                            --exclude='node_modules' \
                            --exclude='.env' \
                            --exclude='.env.local' \
                            --exclude='staticfiles' \
                            --exclude='media' \
                            \$TEMP_DIR/ ${APP_DIR}/

                        # Restaurar .env
                        if [ -f /tmp/.env.backup ]; then
                            cp /tmp/.env.backup ${APP_DIR}/.env
                            rm /tmp/.env.backup
                        fi

                        cd ${APP_DIR}

                        echo "==> Construyendo imagen Docker"
                        docker compose -f docker-compose.dev.yml build

                        echo "==> Levantando contenedores"
                        docker compose -f docker-compose.dev.yml up -d

                        echo "==> Esperando inicio de contenedores y ejecución de migraciones"
                        echo "    (El entrypoint ejecuta: wait_for_db -> migrate -> collectstatic)"
                        sleep 15

                        echo "==> Verificando logs de inicio"
                        docker compose -f docker-compose.dev.yml logs --tail=30 web

                        echo "==> Verificando que los contenedores están corriendo"
                        MAX_RETRIES=6
                        RETRY_COUNT=0
                        CONTAINERS_UP=false

                        while [ \$RETRY_COUNT -lt \$MAX_RETRIES ]; do
                            echo "==> Verificación \$((RETRY_COUNT + 1)) de \$MAX_RETRIES"
                            
                            if docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
                                echo "Contenedores corriendo"
                                CONTAINERS_UP=true
                                break
                            fi
                            
                            RETRY_COUNT=\$((RETRY_COUNT + 1))
                            if [ \$RETRY_COUNT -lt \$MAX_RETRIES ]; then
                                echo "Esperando 5 segundos antes de reintentar..."
                                sleep 5
                            fi
                        done

                        if [ "\$CONTAINERS_UP" = "false" ]; then
                            echo "ERROR: Los contenedores no están corriendo"
                            echo "==> Logs completos:"
                            docker compose -f docker-compose.dev.yml logs
                            exit 1
                        fi

                        echo "==> Verificando health de la API"
                        HEALTH_RETRIES=12
                        HEALTH_COUNT=0
                        API_HEALTHY=false

                        while [ \$HEALTH_COUNT -lt \$HEALTH_RETRIES ]; do
                            if curl -f -s http://localhost:8000/admin/ > /dev/null 2>&1; then
                                echo "✓ API respondiendo correctamente"
                                API_HEALTHY=true
                                break
                            fi
                            
                            HEALTH_COUNT=\$((HEALTH_COUNT + 1))
                            if [ \$HEALTH_COUNT -lt \$HEALTH_RETRIES ]; then
                                echo "Esperando respuesta de la API... (\$HEALTH_COUNT/\$HEALTH_RETRIES)"
                                sleep 5
                            fi
                        done

                        if [ "\$API_HEALTHY" = "false" ]; then
                            echo "ERROR: API no responde después de 60 segundos"
                            docker compose -f docker-compose.dev.yml logs --tail=100 web
                            exit 1
                        fi

                        echo "========================================="
                        echo "==> Deploy completado exitosamente"
                        echo "========================================="
                        
                        # Limpiar archivos temporales
                        rm -rf \$TEMP_DIR
                        
                        echo "==> Información del deploy:"
                        echo "    - Versión desplegada: develop"
                        echo "    - Backup creado: \$BACKUP_DIR"
                        echo "    - Contenedores activos:"
                        docker compose -f docker-compose.dev.yml ps
                        
                        echo "========================================="
                        echo "==> Limpieza completada"
                        echo "========================================="
                    '
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo "========================================="
            echo "API DEV desplegada correctamente"
            echo "========================================="
        }
        failure {
            echo "========================================="
            echo "Falló el deploy de la API DEV"
            echo "   Se ejecutó rollback automático"
            echo "========================================="
        }
    }
}