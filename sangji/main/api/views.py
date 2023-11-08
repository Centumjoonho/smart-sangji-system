import json
import base64 
import os

from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings


from main.models import *
from main.api.serializers import ExternalExerciseLogSerializer
from app_socket.models import *
from app_socket.api.serializers import MuscleFunctionLogDataSerializer

class UserAPI(APIView):
    def post(self, request):
        print(request.POST)
        data = request.POST.get('user')
        data = json.loads(data)

        if User.objects.filter(username=data.get('id')):
            return Response({
                "message" : "아이디가 존재합니다.",
                "success" : False,
            }, status=403)

        user_id = data.get('id')
        
        user = User.objects.create_user(
            username = user_id,
            password = data.get('password')
        )

        picture_base64 = data.get('picture')
        filename = None

        if picture_base64:
            profile_image = base64.b64decode(picture_base64)
            filename = f'{user_id}.jpg'  # I assume you have a way of picking unique filenames
            file_path = os.path.join(settings.MEDIA_ROOT, 'user_face', filename)
            with open(file_path, 'wb') as f:
                f.write(profile_image)

            # if user image add, need to delete pkl file which created by deepface
            vgg_face_pkl_path = os.path.join(settings.MEDIA_ROOT, 
                                             'user_face',
                                             'representations_vgg_face.pkl')
            if os.path.exists(vgg_face_pkl_path):
                print("delete vgg face pkl path")
                os.remove(vgg_face_pkl_path)

        profile = Profile.objects.create(
            user = user,
            name = data.get('name'),
            both = data.get('both'),
            sex  = data.get('sex'),
            phone = data.get('phone'),
            email = data.get('email'),
            picture = filename
        )

        userinfo = UserInfo.objects.create(
            user=user,
        )

        if data.get('obstacles'):
            obstacles = json.loads(data.get('obstacles'))
            for obstacle in obstacles:
                Obstacle.objects.create(
                    user = profile,
                    step1 = obstacle['step1'],
                    step2 = obstacle['step2'],
                    step3 = obstacle['step3']
                )
            
        return Response({
            "message" : "회원가입 성공",
            "success" : True,
        }, status=200)

    def get(self, request):
        
        users = User.objects.filter(username=request.GET.get('id'))
        if users:
            return Response({
                "is_exist" : True,
                "message" : "이미존재하는 아이디입니다."
            }, status=200)
        else:
            return Response({
                "is_exist" : False,
                "message" : "사용가능한 아이디입니다."
            }, status=200)

class LoginAPI(APIView):
    def post(self, request):
        print(request.POST)
        user = authenticate(username=request.POST.get('id'), 
                            password=request.POST.get('password'))
        if user:
            return Response({
                "success" : True,
                # "user" : user.username
            }, status=200)
        else:
            return Response({
                "success" : False
            }, status=200)
        
class MuscleFunctionLogDataAPI(APIView):
    """MuscleFunctionLogData API"""

    def get(self, request):

        username = request.GET.get('username')

        concat_data = []

        data = MuscleFunctionLogData.objects.filter(user_id=username)[:20]
        data_sr = MuscleFunctionLogDataSerializer(data, many=True).data

        # ExternalExerciseLog Data
        ext_data = ExternalExerciseLog.objects.filter(user=username)
        ext_data_sr = ExternalExerciseLogSerializer(ext_data, many=True).data

        concat_data += data_sr 
        concat_data += ext_data_sr

        concat_data = sorted(concat_data, key=lambda x: x['created_at'], reverse=True)
        
        context = {
            'result' : concat_data
        }
        
        return Response(context, status=200)
        

class ExternalExerciseLogAPI(APIView):
    """ExternalExerciseLog API"""

    def get(self, request):
        data = ExternalExerciseLog.objects.all()
        data_sr = ExternalExerciseLogSerializer(data, many=True).data

        print(data_sr)

        context = {
            'result' : data_sr
        }
        
        return Response(context, status=200)

    def post(self, request):
        print(request.data)
        data = {
            "excericse" : request.POST.get('exercise'),
            "repetition" : request.POST.get('repetition'),
            "datetime" : request.POST.get('date'),
            "user" : request.POST.get("username")
        }
        message = "성공적으로 생성되었습니다."
        success = True

        serializer = ExternalExerciseLogSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
        else:
            message = "생성 도중 에러가 발생했습니다."
            success = False
            print(serializer.errors)        

        context = {
            'success' : success,
            'result' : message
        }
    
        return Response(context, status=200)
    
