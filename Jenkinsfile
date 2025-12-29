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
                sh """
                ssh -o StrictHostKeyChecking=no ${SSH_USER}@${API_HOST} '
                    set -e

                    echo "==> Entrando a servidor API DEV"

                    if [ ! -d ${APP_DIR}/.git ]; then
                        echo "==> Clonando repositorio"
                        git clone ${GIT_URL} ${APP_DIR}
                    else
                        echo "==> Actualizando repositorio"
                        cd ${APP_DIR}
                        git fetch origin
                        git checkout develop
                        git pull origin develop
                    fi

                    cd ${APP_DIR}

                    echo "==> Parando contenedores"
                    docker compose -f docker-compose.dev.yml down

                    echo "==> Construyendo imagen"
                    docker compose -f docker-compose.dev.yml build

                    echo "==> Levantando API DEV"
                    docker compose -f docker-compose.dev.yml up -d

                    echo "==> Deploy DEV completado"
                '
                """
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