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

                        echo "==> Iniciando deploy"
                        
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
                            echo "==> ERROR: Deploy falló, iniciando rollback"
                            rm -rf \$TEMP_DIR
                            
                            if [ -d \$BACKUP_DIR ]; then
                                echo "==> Restaurando backup"
                                rm -rf ${APP_DIR}
                                mv \$BACKUP_DIR ${APP_DIR}
                                
                                echo "==> Levantando contenedores con versión anterior"
                                cd ${APP_DIR}
                                docker compose -f docker-compose.dev.yml up -d
                                
                                echo "==> Rollback completado"
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

                        echo "==> Copiando nuevos archivos"
                        mkdir -p ${APP_DIR}
                        rsync -av --delete \
                            --exclude='node_modules' \
                            --exclude='.env' \
                            --exclude='.env.local' \
                            \$TEMP_DIR/ ${APP_DIR}/

                        cd ${APP_DIR}

                        echo "==> Construyendo imagen"
                        docker compose -f docker-compose.dev.yml build

                        echo "==> Levantando API DEV"
                        docker compose -f docker-compose.dev.yml up -d

                        echo "==> Verificando que los contenedores están corriendo"
                        sleep 5
                        if ! docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
                            echo "==> ERROR: Los contenedores no están corriendo"
                            exit 1
                        fi

                        echo "==> Deploy completado exitosamente"
                        
                        # Limpiar archivos temporales y backup si todo salió bien
                        rm -rf \$TEMP_DIR
                        
                        # Mantener solo los últimos 3 backups
                        cd /opt/manzaspots
                        ls -dt api_backup_* 2>/dev/null | tail -n +4 | xargs rm -rf 2>/dev/null || true
                        
                        echo "==> Limpieza completada"
                    '
                    """
                }
            }
        }
    }
    post {
        success {
            echo "API DEV desplegada correctamente"
        }
        failure {
            echo "Falló el deploy de la API DEV"
        }
    }
}