pipeline {
    agent any
    stages {
        stage('Test') {
            agent {
                dockerfile {
                    args '-u root:root'
                    reuseNode true
                }
            }
            steps {
                sh "python setup.py install --quiet" // Necessary for locally-defined command lines apps to be accessible for testing.

                sh "pytest --junitxml=pytest_results.xml unittests"

                sh "behave -D record_mode=none --tags=-skip -f json.cucumber -o test-results-csvcubedintegration.json csvcubedintegrationfeatures"
                sh "behave -D record_mode=none --tags=-skip -f json.cucumber -o test-results.json features"

            }
        }
    }
    post {
        always {
            cucumber fileIncludePattern: '**/test-results*.json'
            junit allowEmptyResults: true, testResults: '**/*results*.xml'
        }
    }
}
