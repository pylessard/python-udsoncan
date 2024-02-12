pipeline {
    agent {
        label 'docker'
    }
    stages {
        stage ('Docker') {
            agent {
                dockerfile {
                    args '-e HOME=/tmp -e BUILD_CONTEXT=ci'
                    additionalBuildArgs '--target build-tests'
                    reuseNode true
                }
            }
            stages {
                stage('Testing'){
                    parallel{
                        
                        stage ('Python 3.11') {
                            steps {
                                sh '''
                                python3.11 -m venv venv-3.11
                                VENV_DIR=venv-3.11 scripts/with-venv.sh scripts/check-python-version.sh 3.11
                                VENV_DIR=venv-3.11 COVERAGE_SUFFIX=3.11 scripts/with-venv.sh scripts/runtests.sh
                                '''
                            }
                        }
                        stage ('Python 3.10') {
                            steps {
                                sh '''
                                python3.10 -m venv venv-3.10
                                VENV_DIR=venv-3.10 scripts/with-venv.sh scripts/check-python-version.sh 3.10
                                VENV_DIR=venv-3.10 COVERAGE_SUFFIX=3.10 scripts/with-venv.sh scripts/runtests.sh
                                '''
                            }
                        }
                        stage ('Python 3.9') {
                            steps {
                                sh '''
                                python3.9 -m venv venv-3.9
                                VENV_DIR=venv-3.9 scripts/with-venv.sh scripts/check-python-version.sh 3.9
                                VENV_DIR=venv-3.9 COVERAGE_SUFFIX=3.9 scripts/with-venv.sh scripts/runtests.sh
                                '''
                            }
                        }
                        stage ('Python 3.8') {
                            steps {
                                sh '''
                                python3.8 -m venv venv-3.8
                                VENV_DIR=venv-3.8 scripts/with-venv.sh scripts/check-python-version.sh 3.8
                                VENV_DIR=venv-3.8 COVERAGE_SUFFIX=3.8 scripts/with-venv.sh scripts/runtests.sh 
                                '''
                            }
                        }
                        stage ('Python 3.7') {
                            steps {
                                sh '''
                                python3.7 -m venv venv-3.7
                                VENV_DIR=venv-3.7 scripts/with-venv.sh scripts/check-python-version.sh 3.7
                                VENV_DIR=venv-3.7 COVERAGE_SUFFIX=3.7 scripts/with-venv.sh scripts/runtests.sh 
                                '''
                            }
                        }
                    }
                }
            }
        }
    }
}
