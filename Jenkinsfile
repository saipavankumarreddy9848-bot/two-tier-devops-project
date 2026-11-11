
pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    environment {
        APP_NAME = 'two-tier-devops-project'
        COMPOSE_FILE = 'docker-compose.yml'
        COMPOSE_PROJECT_NAME = 'two-tier-devops-project'
        ENV_FILE = '/opt/two-tier-devops-project/.env'
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Source code checked out by Jenkins.'

                sh '''
                    set -e
                    git status --short --branch
                    git log -1 --oneline
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    set -e

                    echo "Checking Python version..."
                    python3.12 --version

                    echo "Creating Python 3.12 virtual environment..."
                    rm -rf .venv
                    python3.12 -m venv .venv

                    echo "Upgrading pip..."
                    .venv/bin/python -m pip install --upgrade pip

                    echo "Installing pytest..."
                    .venv/bin/python -m pip install pytest==8.4.2

                    echo "Installing application dependencies..."
                    .venv/bin/python -m pip install -r app/requirements.txt

                    echo "Running application tests..."
                    .venv/bin/python -m pytest -v

                    echo "All Python tests completed successfully."
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'

                    withSonarQubeEnv('SonarCloud') {
                        sh """
                            set -e

                            echo "Starting SonarQube Cloud analysis..."

                            ${scannerHome}/bin/sonar-scanner

                            echo "SonarQube analysis completed."
                        """
                    }
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    def commitId = sh(
                        script: 'git rev-parse --short=12 HEAD',
                        returnStdout: true
                    ).trim()

                    env.NEW_IMAGE = "${env.APP_NAME}-app:${commitId}"

                    echo "New application image: ${env.NEW_IMAGE}"
                }

                sh '''
                    set -e

                    echo "Checking environment file..."

                    if [ ! -f "$ENV_FILE" ]; then
                        echo "ERROR: Environment file not found."
                        exit 1
                    fi

                    echo "Validating Docker Compose configuration..."

                    docker compose \
                        --env-file "$ENV_FILE" \
                        -p "$COMPOSE_PROJECT_NAME" \
                        -f "$WORKSPACE/$COMPOSE_FILE" \
                        config --quiet

                    echo "Building versioned Docker image..."

                    APP_IMAGE="$NEW_IMAGE" docker compose \
                        --env-file "$ENV_FILE" \
                        -p "$COMPOSE_PROJECT_NAME" \
                        -f "$WORKSPACE/$COMPOSE_FILE" \
                        build app

                    echo "Docker image build completed."

                    docker image inspect "$NEW_IMAGE" >/dev/null
                '''
            }
        }

        stage('Deploy Application') {
            steps {
                script {
                    env.PREVIOUS_IMAGE =
                        "${env.APP_NAME}-app:rollback-${env.BUILD_NUMBER}"
                }

                sh '''
                    set -e

                    echo "Checking environment file..."

                    if [ ! -f "$ENV_FILE" ]; then
                        echo "ERROR: Environment file not found."
                        exit 1
                    fi

                    echo "Identifying currently deployed application..."

                    APP_CONTAINER=$(docker compose \
                        --env-file "$ENV_FILE" \
                        -p "$COMPOSE_PROJECT_NAME" \
                        -f "$WORKSPACE/$COMPOSE_FILE" \
                        ps -q app)

                    if [ -z "$APP_CONTAINER" ]; then
                        echo "ERROR: Existing application container not found."
                        exit 1
                    fi

                    CURRENT_IMAGE_ID=$(docker inspect \
                        --format '{{.Image}}' "$APP_CONTAINER")

                    echo "Preserving previous application image..."

                    docker tag "$CURRENT_IMAGE_ID" "$PREVIOUS_IMAGE"

                    echo "Previous image saved as: $PREVIOUS_IMAGE"
                    echo "Deploying new image: $NEW_IMAGE"

                    APP_IMAGE="$NEW_IMAGE" docker compose \
                        --env-file "$ENV_FILE" \
                        -p "$COMPOSE_PROJECT_NAME" \
                        -f "$WORKSPACE/$COMPOSE_FILE" \
                        up -d --no-build app

                    echo "Deployment command completed."

                    docker compose \
                        --env-file "$ENV_FILE" \
                        -p "$COMPOSE_PROJECT_NAME" \
                        -f "$WORKSPACE/$COMPOSE_FILE" \
                        ps
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                script {
                    try {
                        sh '''
                            set -e

                            echo "Waiting for application and database health..."

                            APP_CONTAINER=""
                            DB_CONTAINER=""
                            HEALTHY=false

                            for i in $(seq 1 12); do

                                APP_CONTAINER=$(docker compose \
                                    --env-file "$ENV_FILE" \
                                    -p "$COMPOSE_PROJECT_NAME" \
                                    -f "$WORKSPACE/$COMPOSE_FILE" \
                                    ps -q app)

                                DB_CONTAINER=$(docker compose \
                                    --env-file "$ENV_FILE" \
                                    -p "$COMPOSE_PROJECT_NAME" \
                                    -f "$WORKSPACE/$COMPOSE_FILE" \
                                    ps -q db)

                                if [ -n "$APP_CONTAINER" ] && [ -n "$DB_CONTAINER" ]; then

                                    APP_STATUS=$(docker inspect \
                                        --format '{{.State.Health.Status}}' "$APP_CONTAINER")

                                    DB_STATUS=$(docker inspect \
                                        --format '{{.State.Health.Status}}' "$DB_CONTAINER")

                                    echo "Application status: $APP_STATUS"
                                    echo "Database status: $DB_STATUS"

                                    if [ "$APP_STATUS" = "healthy" ] && \
                                       [ "$DB_STATUS" = "healthy" ]; then
                                        HEALTHY=true
                                        break
                                    fi
                                fi

                                sleep 5
                            done

                            if [ "$HEALTHY" != "true" ]; then
                                echo "ERROR: Container health verification failed."
                                exit 1
                            fi

                            echo "Both containers are healthy."

                            echo "Checking application endpoint..."

                            curl --fail \
                                --retry 5 \
                                --retry-delay 5 \
                                --retry-connrefused \
                                http://localhost:5000/health

                            echo ""

                            echo "Checking database connectivity..."

                            curl --fail \
                                --retry 5 \
                                --retry-delay 5 \
                                --retry-connrefused \
                                http://localhost:5000/db-health

                            echo ""

                            echo "Deployment verification successful."
                        '''

                    } catch (err) {

                        echo "DEPLOYMENT VERIFICATION FAILED."
                        echo "Starting automatic rollback..."

                        try {
                            sh '''
                                set -e

                                echo "Restoring previous application image..."

                                docker image inspect "$PREVIOUS_IMAGE" >/dev/null

                                APP_IMAGE="$PREVIOUS_IMAGE" docker compose \
                                    --env-file "$ENV_FILE" \
                                    -p "$COMPOSE_PROJECT_NAME" \
                                    -f "$WORKSPACE/$COMPOSE_FILE" \
                                    up -d --no-build app

                                echo "Waiting for restored application..."

                                APP_CONTAINER=$(docker compose \
                                    --env-file "$ENV_FILE" \
                                    -p "$COMPOSE_PROJECT_NAME" \
                                    -f "$WORKSPACE/$COMPOSE_FILE" \
                                    ps -q app)

                                if [ -z "$APP_CONTAINER" ]; then
                                    echo "ERROR: Restored application container not found."
                                    exit 1
                                fi

                                RESTORED=false

                                for i in $(seq 1 12); do

                                    STATUS=$(docker inspect \
                                        --format '{{.State.Health.Status}}' "$APP_CONTAINER")

                                    echo "Restored application status: $STATUS"

                                    if [ "$STATUS" = "healthy" ]; then
                                        RESTORED=true
                                        break
                                    fi

                                    sleep 5
                                done

                                if [ "$RESTORED" != "true" ]; then
                                    echo "ERROR: Restored application is not healthy."
                                    exit 1
                                fi

                                curl --fail \
                                    --retry 3 \
                                    --retry-delay 5 \
                                    --retry-connrefused \
                                    http://localhost:5000/health

                                echo ""
                                echo "ROLLBACK COMPLETED SUCCESSFULLY."
                            '''

                        } catch (rollbackError) {
                            echo "CRITICAL: Automatic rollback failed."
                            echo "Check Docker container logs and deployment status."
                        }

                        throw err
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: Pipeline completed successfully!'
        }

        failure {
            echo 'FAILURE: Pipeline failed. Check the stage logs.'
        }

        always {
            echo 'Jenkins pipeline execution completed.'
        }
    }
}

