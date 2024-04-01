def call(dockerRepoName, imageName) {
    pipeline {
        agent any
        environment {
            PATH = "$WORKSPACE/venv/bin:$PATH"
        }
        stages {
            stage('Build') {
                steps {
                    script {
                        sh 'python3 -m venv venv'
                        sh '. venv/bin/activate'
                        sh 'pip install -r requirements.txt --break-system-packages'
                        sh 'pip install --upgrade flask --break-system-packages'
                        sh 'pip install coverage --break-system-packages'
                    }
                }
            }

            // Newly added stage in Lab 6
            stage('Python Lint') {
                steps {
                    script {
                        sh 'pylint --fail-under=5 *.py'
                    }
                }
            }

            // Previously named Unit Test
            stage('Test and Coverage') {
                steps {
                    script {
                        // Remove any existing report files before running the tests
                        def test_reports_exist = fileExists 'test-reports'
                        if (test_reports_exist) {
                            sh 'rm test-reports/*.xml || true'
                        }

                        def api_test_reports_exist = fileExists 'api-test-reports'
                        if (api_test_reports_exist) {
                            sh 'rm api-test-reports/*.xml || true'
                        }

                        // Running the tests
                        def testFiles = findFiles(glob: 'test*.py')
                        testFiles.each {
                            file ->
                            // "coverage run" doesn't work as 'coverage: not found'
                            sh "python3 -m coverage run --omit */site-packages/*,*/dist-packages/* ${file}"
                        }
                    }
                }
                post {
                    always {
                        script {
                            // After running the tests, do the following...
                            def test_reports_exist = fileExists 'test-reports'
                            if (test_reports_exist) {
                                junit 'test-reports/*.xml'
                            }

                            def api_test_reports_exist = fileExists 'api-test-reports'
                            if (api_test_reports_exist) {
                                junit 'api-test-reports/*.xml'
                            }

                            // "coverage report" doesn't work as 'coverage: not found'
                            sh 'python3 -m coverage report'
                        }
                    }
                }
            }

            stage('Package') {
                when {
                    expression { env.GIT_BRANCH == 'origin/main' }
                }
                steps {
                    withCredentials([string(credentialsId: 'DockerHub', variable: 'TOKEN')]) {
                        sh "docker login -u 'nazzywazzy' -p '$TOKEN' docker.io"
                        sh "docker build -t ${dockerRepoName}:latest --tag nazzywazzy/${dockerRepoName}:${imageName} ."
                        sh "docker push nazzywazzy/${dockerRepoName}:${imageName}"
                    }
                }
            }

            // New stage
            stage('Zip Artifacts') {
                steps {
                    sh 'zip app.zip *.py'
                    archiveArtifacts artifacts: 'app.zip', onlyIfSuccessful: true
                }
            }
        }
        post {
            always {
                script {
                    sh 'unset PATH'
                }
            }
        }
    }
}
