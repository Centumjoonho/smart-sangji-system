from django.urls import path

from . import views
from .api.views import *

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
    path('api/external/log', ExternalExerciseLogAPI.as_view()),
    
]
