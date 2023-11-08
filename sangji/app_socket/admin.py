from django.contrib import admin
from .models import *

class MuscleFunctionLogDataAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'exercise_type', 'created_at']


admin.site.register(ExerciseLog)
admin.site.register(UserInfomation)
admin.site.register(ExerciseStampLog)
admin.site.register(MoleDataLog)
admin.site.register(ROMMeasureLog)
admin.site.register(MuscleFunctionLogData, MuscleFunctionLogDataAdmin)
admin.site.register(ROMLogData)