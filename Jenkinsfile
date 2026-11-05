
pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    environment {
        APP_NAME = 'two-tier-devops-project'
        COMPOSE_FILE = 'docker-compose.yml'
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Source code checked out by Jenkins.'
                sh 'git status --short --branch'
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    set -e

                    echo "Checking Python version..."
                    python3.12 --version

                    echo "Creating virtual environment..."
                    python3.12 -m venv .venv

                    echo "Activating virtual environment..."
                    . .venv/bin/activate

                    echo "Upgrading pip..."
                    python -m pip install --upgrade pip

                    echo "Installing pytest..."
                    python -m pip install pytest==8.4.2

                    echo "Installing application dependencies..."
                    python -m pip install -r app/requirements.txt

                    echo "Running application tests..."
                    .venv/bin/python -m pytest -v
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    set -e

                    echo "Building Docker images..."
                    docker compose -f ${COMPOSE_FILE} build
                '''
            }
        }

        stage('Deploy Application') {
            steps {
                sh '''
                    set -e

                    echo "Checking environment configuration..."

                    if [ ! -f .env ]; then
                        echo "ERROR: .env file is missing."
                        exit 1
                    fi

                    echo "Deploying application..."
                    docker compose -f ${COMPOSE_FILE} up -d

                    echo "Checking running containers..."
                    docker compose -f ${COMPOSE_FILE} ps
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
                    curl --fail --retry 5 --retry-delay 5 \
                        http://localhost:5000/health

                    echo ""

                    echo "Checking database health..."
                    curl --fail \
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

