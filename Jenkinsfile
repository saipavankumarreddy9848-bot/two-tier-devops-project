pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Source code was checked out by Jenkins.'
                sh 'git status --short --branch'
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    set -e
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r app/requirements.txt pytest
                    python -m pytest -v
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh 'sudo docker compose build'
            }
        }

        stage('Deploy Application') {
            steps {
                sh 'sudo docker compose up -d'
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    sleep 10
                    curl --fail http://127.0.0.1:5000/health
                    echo
                    curl --fail http://127.0.0.1:5000/db-health
                    echo
                '''
            }
        }
    }
}
