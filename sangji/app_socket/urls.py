from django.urls import path
from .api.views import *

urlpatterns = [
    path('user', UserInfomationAPI.as_view()),
    path('rom/shoulder/abduction/<left_or_right>',ShoulderAbductionROMAPI.as_view()),
    path('rom/shoulder/adduction/<left_or_right>',ShoulderAdductionROMAPI.as_view()),
    path('rom/shoulder/flextion/<left_or_right>',ShoulderFlextionROMAPI.as_view()),
    path('rom/shoulder/extension/<left_or_right>',ShoulderExtensionROMAPI.as_view()),
    path('rom/elbow/flextion/<left_or_right>',ElbowFlextionROMAPI.as_view()),
    path('rom/elbow/extension/<left_or_right>',ElbowExtensionROMAPI.as_view()),
    
    path('rom/', ROMAPI.as_view()),
    path('musclefunction/log', MuscleFunctionLog.as_view()),

    # Save user's ROM measurement result
    path('user/rom', UserROM.as_view())

]