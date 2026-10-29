
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        DOCKERHUB_USERNAME = 'YOUR_DOCKERHUB_USERNAME'
        IMAGE_NAME = 'sales-system'
        K8S_MANIFEST = 'k8s/sales-system.yaml'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git status --short'
            }
        }

        stage('Validate Python') {
            steps {
                sh '''
                    python3 -m pip install -r requirements.txt
                    python3 -m py_compile app.py
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    docker build --build-arg APP_VERSION=v1 \
                      -t "$DOCKERHUB_USERNAME/$IMAGE_NAME:v1" .

                    docker build --build-arg APP_VERSION=v2 \
                      -t "$DOCKERHUB_USERNAME/$IMAGE_NAME:v2" .

                    docker build --build-arg APP_VERSION=v3 \
                      -t "$DOCKERHUB_USERNAME/$IMAGE_NAME:v3" .
                '''
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DH_USER',
                        passwordVariable: 'DH_TOKEN'
                    )
                ]) {
                    sh '''
                        set +x
                        printf '%s' "$DH_TOKEN" |
                          docker login -u "$DH_USER" --password-stdin

                        docker push "$DOCKERHUB_USERNAME/$IMAGE_NAME:v1"
                        docker push "$DOCKERHUB_USERNAME/$IMAGE_NAME:v2"
                        docker push "$DOCKERHUB_USERNAME/$IMAGE_NAME:v3"

                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                    sed "s|DOCKERHUB_USERNAME|$DOCKERHUB_USERNAME|g" \
                        "$K8S_MANIFEST" > /tmp/sales-system.yaml

                    kubectl apply -f /tmp/sales-system.yaml

                    kubectl rollout status deployment/sales-v1 \
                        --timeout=180s
                    kubectl rollout status deployment/sales-v2 \
                        --timeout=180s
                    kubectl rollout status deployment/sales-v3 \
                        --timeout=180s

                    kubectl get deployments,services
                '''
            }
        }
    }

    post {
        success {
            echo 'Sales System: all three versions built and deployed.'
        }
        failure {
            echo 'Pipeline failed. Check the failed stage in Jenkins Console Output.'
        }
    }
}
