from django.urls import path

from . import views

# 관리자 시스템
urlpatterns = [
    path('', views.index),
    path('user', views.anaylsis_user),
    # 유저 운동 조회
    path('user/exercise', views.user_exercise_index),
    path('user/exercise/detail/<log_pk>', views.user_exercise_detail),
    # 유저 리포트 
    path('user/<user_id>/report', views.user_report_index),
    path('user/<user_id>/report/isometric', views.user_report_isometric),
    path('search/user/', views.search_users),
]
