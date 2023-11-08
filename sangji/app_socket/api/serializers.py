import json

from rest_framework import serializers

from app_socket.models import *

class UserInfomationSerializer(serializers.ModelSerializer):
    maxium_log = serializers.SerializerMethodField()
    midium_log = serializers.SerializerMethodField()
    minium_log = serializers.SerializerMethodField()
    revital_maxium_log  = serializers.SerializerMethodField()
    revital_midium_log  = serializers.SerializerMethodField()
    revital_minium_log  = serializers.SerializerMethodField()
    class Meta:
        model = UserInfomation
        fields = '__all__'

    def get_maxium_log(self, obj):
        try:
            _json = json.loads(obj.strength_logs)
            return _json.get("0")
        except Exception as err:
            return []

    def get_midium_log(self, obj):
        try:
            _json = json.loads(obj.strength_logs)
            return _json.get("1")
        except Exception as err:
            return []

    def get_minium_log(self, obj):
        try:
            _json = json.loads(obj.strength_logs)
            return _json.get("2")
        except Exception as err:
            return []

    # 등척성 재활운동
    def get_revital_maxium_log(self, obj):
        try:
            _json = json.loads(obj.revital_latpulldown_strength_logs)
            return _json.get("0")
        except Exception as err:
            return []

    def get_revital_midium_log(self, obj):
        try:
            _json = json.loads(obj.revital_latpulldown_strength_logs)
            return _json.get("1")
        except Exception as err:
            return []

    def get_revital_minium_log(self, obj):
        try:
            _json = json.loads(obj.revital_latpulldown_strength_logs)
            return _json.get("2")
        except Exception as err:
            return []


class MuscleFunctionLogDataSerializer(serializers.ModelSerializer):
    exercise_type = serializers.SerializerMethodField()
    datetime_str = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    class Meta:
        model = MuscleFunctionLogData
        fields = ('user_id', 'exercise_type', 'created_at', 'datetime_str', 'type')

    def get_datetime_str(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    
    def get_exercise_type(self, obj):
        _type = ""

        if obj.exercise_type == "musclefunction_isometric":
            _type = "등척성"
        elif obj.exercise_type == "musclefunction_isotonic":
            _type = "등장성"
        else:
            _type = "등속성"
        
        return _type
    
    def get_created_at(self, obj):
        return obj.created_at

    def get_type(self, obj):
        return "indoor"
    