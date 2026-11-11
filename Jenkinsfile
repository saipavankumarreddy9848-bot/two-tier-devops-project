
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
                        up -d

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
		    echo "Waiting for application and database containers..."

	            APP_CONTAINER=""
        	    DB_CONTAINER=""

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
                        	break
                    	    fi
                	fi

                	if [ "$i" -eq 12 ]; then
                    	    echo "ERROR: Containers did not become healthy."

                    	    docker compose \
                        	--env-file "$ENV_FILE" \
                        	-p "$COMPOSE_PROJECT_NAME" \
                        	-f "$WORKSPACE/$COMPOSE_FILE" \
                        	ps

                    	    docker compose \
                        	--env-file "$ENV_FILE" \
                        	-p "$COMPOSE_PROJECT_NAME" \
                        	-f "$WORKSPACE/$COMPOSE_FILE" \
                        	logs --tail=50 app db

                    	    exit 1
                	fi

                	sleep 5
            	   
		    done


                    echo "Both containers are healthy."
                    

                    echo "Checking application health endpoint..."

                    curl --fail \
                        --retry 5 \
                        --retry-delay 5 \
                        --retry-connrefused \
                        http://localhost:5000/health

                    echo ""

                    echo "Checking database connectivity endpoint..."

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

