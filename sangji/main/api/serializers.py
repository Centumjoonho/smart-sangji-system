from rest_framework import serializers

from main.models import *

class ExternalExerciseLogSerializer(serializers.ModelSerializer):
    user = serializers.CharField(required=False)
    user_id = serializers.SerializerMethodField()
    exercise_type = serializers.SerializerMethodField()
    datetime_str = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    class Meta:
        model = ExternalExerciseLog
        fields = ('id','user', 'user_id', 'excericse', 'exercise_type', 
                  'datetime', 'repetition', 'datetime_str', 'created_at', 'type',)


    def get_datetime_str(self, obj):
        return obj.datetime.strftime('%Y-%m-%d %H:%M')
    
    def get_user_id(self, obj):
        return obj.user
    
    def get_exercise_type(self, obj):
        return f'{obj.excericse} | {obj.repetition}회'
    
    def get_created_at(self, obj):
        return obj.datetime
    
    def get_type(self, obj):
        return "outdoor"   
    
    # SerializerMethodField에 대응되는 get_ 메서드를 추가하여 id 값을 반환하도록 지정합니다.
    def get_id(self, obj):
        return obj.id