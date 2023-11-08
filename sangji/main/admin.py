from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Profile)
admin.site.register(Obstacle)
admin.site.register(UserInfo)
admin.site.register(UserMuscleFunctionRange)
admin.site.register(ExternalExerciseLog)
