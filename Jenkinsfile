
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
                    git status --short --branch
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

                    echo "Verifying Python version..."
                    .venv/bin/python --version

                    echo "Running application tests..."
                    .venv/bin/python -m pytest -v
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    set -e

                    echo "Checking environment file..."


                    if [ ! -f "$ENV_FILE" ]; then
                        echo "ERROR: Jenkins cannot read the environment file."
                        exit 1
                    fi

                    echo "Validating Docker Compose configuration..."

                    docker compose \
                        --env-file "$ENV_FILE" \
                        -p "$COMPOSE_PROJECT_NAME" \
                        -f "$WORKSPACE/$COMPOSE_FILE" \
                        config --quiet

                    echo "Building Docker images..."
		    
		    docker compose \
                        --env-file "$ENV_FILE" \
       		        -p "$COMPOSE_PROJECT_NAME" \
                	-f "$WORKSPACE/$COMPOSE_FILE" \
                	build
		    echo "Docker image build completed."

                '''
            }
        }

        stage('Deploy Application') {
            steps {
                sh '''
                    set -e

                    echo "Checking environment file..."

                    if [ ! -f "$ENV_FILE" ]; then
                        echo "ERROR: Jenkins cannot read the environment file."
                        exit 1
                    fi

                    echo "Deploying application..."

                    docker compose \
                        --env-file "$ENV_FILE" \
                        -p "$COMPOSE_PROJECT_NAME" \
                        -f "$WORKSPACE/$COMPOSE_FILE" \
                        up -d build

                    echo "Checking running containers..."

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
                sh '''
                    set -e

                    echo "Waiting for application startup..."
                    sleep 10

                    echo "Checking application health..."

                    curl --fail \
                        --retry 5 \
                        --retry-delay 5 \
                        --retry-connrefused \
                        http://localhost:5000/health

                    echo ""

                    echo "Checking database health..."

                    curl --fail \
                        --retry 5 \
                        --retry-delay 5 \
                        --retry-connrefused \
                        http://localhost:5000/db-health

                    echo ""
                    echo "Deployment verification successful."
                '''
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

