pipeline {
    agent any

    environment {
        TEST_IMAGE = "baseball-dash:test-${BUILD_NUMBER}"
        CONTAINER_NAME = "baseball-dash-test-instance-${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // 🧪 STAGE 1: Fast Python validations (Old Tests)
        stage('Run Python Unit/Integration Tests') {
            agent {
                docker { image 'python:3.11-slim' }
            }
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate

                    pip install -r requirements.txt pytest
                    pytest tests/ --junitxml=test-reports/results.xml
                '''
            }
            post {
                always {
                    junit 'test-reports/results.xml'
                }
            }
        }

        // 🔨 STAGE 2: Package everything up
        stage('Build Container Image') {
            steps {
                sh "docker build -t ${TEST_IMAGE} ."
            }
        }

        // 🚀 STAGE 3: Infrastructure Sanity Check (New Container Test)
        stage('Run Container & Smoke Test') {
            steps {
                sh "docker run -d --name ${CONTAINER_NAME} -p 8081:5000 ${TEST_IMAGE}"
                sh "sleep 5"
                sh """
                    RESPONSE=\$(curl -s --connect-timeout 5 http://localhost:8081/live)
                    if echo "\$RESPONSE" | grep -q "alive"; then
                        echo "SUCCESS: Container is fully functional!"
                    else
                        docker logs ${CONTAINER_NAME}
                        exit 1
                    fi
                """
            }
        }
    }

    post {
        always {
            sh """
                docker stop ${CONTAINER_NAME} || true
                docker rm ${CONTAINER_NAME} || true
                docker rmi ${TEST_IMAGE} || true
            """
        }
    }
}
