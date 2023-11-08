# Smart Sangji Project

## Installation

본 프로젝트는 Python 3.8.10, Django 2.2.9 버전으로 개발되었습니다.

프로젝트 설치 및 실행을 위해 아래 명령어를 실행합니다.

```shell
pip install -r requirements.txt
# Move to project folder
cd sangji
# Start django development server
python manage.py runserver
```

## Module Structure 

본 프로젝트는 5개 모듈로 구성되어 있습니다.

1. analysis
    - 관리자 시스템 모듈

2. app_socket
    - 실내용 상지 기기와의 통신을 위한 모듈

3. main
    - 관리자 시스템 일부 기능 (협응 게임 관련)
    - 계정 관련 기능

4. mole_game_package
    - 협응 게임 기능

5. project
    - Project 세팅 관련

## AI Model 

본 프로젝트에서는 2가지 AI 모델이 사용되었습니다.

1. [Mediapipe](https://github.com/google/mediapipe)
2. [DeepFace](https://github.com/serengil/deepface)
