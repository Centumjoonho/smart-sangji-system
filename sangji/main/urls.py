from django.urls import path

from . import views
from .api.views import *

#이준호 경로/id 추가 
urlpatterns = [
    # # 데이터 조회 시스템
    # path('analysis', views.analysis),

    path('log/<uuid>', views.exercise_log),
    path('register',UserAPI.as_view()),
    path('login',LoginAPI.as_view()),
    # 협응 게임
    path('mole/log/main', views.mole_log_main),
    path('mole/log/main/<game_id>', views.mole_log_detail),

    path('api/musclefunctionlog', MuscleFunctionLogDataAPI.as_view()),
    # 항목 삭제 api 를 위해 id 추가
    path('api/external/log', ExternalExerciseLogAPI.as_view()),
    path('api/external/log/<int:id>', ExternalExerciseLogAPI.as_view()),
    
]