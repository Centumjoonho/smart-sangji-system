import json
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from app_socket.models import *
from .serializers import *
from main.models import *

class UserInfomationAPI(APIView):
    def post(self, request):
        print(request.POST)
        uuid=request.POST.get("uuid")
        age=request.POST.get("age")
        handicapped=request.POST.get("handicapped")
        username=request.POST.get("username")
        height=request.POST.get("height")
        weight=request.POST.get("weight")
        sex=request.POST.get("sex")

        if not age or not username:
            return Response({
                "message" : "모든 정보를 입력해 주세요",
            }, status=403)
        
        print(uuid, age, handicapped, username)
        user = UserInfomation.objects.create(
            uuid=uuid,
            user_age=age,
            user_handicapped_type=handicapped,
            user_name=username,
            user_sex=sex,
            user_height=height,
            user_weight=weight,
        )

        return Response({
            "message" : "프로필 생성 완료"
        }, status=200)

    def get(self, request):
        uuid=request.GET.get("uuid")
        userinfo = UserInfomation.objects.get(uuid=uuid)
        if userinfo:
            print(userinfo)
            userinfo_srz = UserInfomationSerializer(userinfo).data
            return Response({
                'userinfo' : userinfo_srz
            })


class ShoulderAbductionROMAPI(APIView):
    '''
        어깨외전
        3차측정중 선택된 왼쪽,오른쪽어깨외전 각도와이미지 db저장
    '''
    def post(self, request,**kwargs):
        print(kwargs)
        print(request)

        print("uuid: ",request.POST.get('uuid'))
        print("step1_angle: ",request.POST.get('step1_angle'))
        print("step2_angle: ",request.POST.get('step2_angle'))
        print("step3_angle: ",request.POST.get('step3_angle'))
        print("mean_angle: ",request.POST.get('mean_angle'))
        print("final_angle: ",request.POST.get('angle'))
        user = UserInfomation.objects.filter(uuid=request.POST.get('uuid'))

        if kwargs.get('left_or_right') == 'left':
            user.update(
                step1_left_shoulder_abduction_angle = request.POST.get('step1_angle'),
                step1_left_shoulder_abduction_image = request.POST.get('step1_image'),
                step2_left_shoulder_abduction_angle = request.POST.get('step2_angle'),
                step2_left_shoulder_abduction_image = request.POST.get('step2_image'),
                step3_left_shoulder_abduction_angle = request.POST.get('step3_angle'),
                step3_left_shoulder_abduction_image = request.POST.get('step3_image'),
                left_shoulder_abduction_max_angle = request.POST.get('angle'),
                left_shoulder_abduction_avg_angle  = request.POST.get('mean_angle')
            )
        else:
            user.update(
                step1_right_shoulder_abduction_angle = request.POST.get('step1_angle'),
                step1_right_shoulder_abduction_image = request.POST.get('step1_image'),
                step2_right_shoulder_abduction_angle = request.POST.get('step2_angle'),
                step2_right_shoulder_abduction_image = request.POST.get('step2_image'),
                step3_right_shoulder_abduction_angle = request.POST.get('step3_angle'),
                step3_right_shoulder_abduction_image = request.POST.get('step3_image'),
                right_shoulder_abduction_max_angle = request.POST.get('angle'),
                right_shoulder_abduction_avg_angle  = request.POST.get('mean_angle'),
            )
        
    
        return Response({})

class ShoulderAdductionROMAPI(APIView):
    '''
        어깨내전
        3차측정중 선택된 왼쪽,오른쪽어깨내전 각도와이미지 db저장
    '''
    def post(self, request,**kwargs):
        
        user = UserInfomation.objects.filter(uuid=request.POST.get('uuid'))

        if kwargs.get('left_or_right') == 'left':
            user.update(
                step1_left_shoulder_adduction_angle = request.POST.get('step1_angle'),
                step1_left_shoulder_adduction_image = request.POST.get('step1_image'),
                step2_left_shoulder_adduction_angle = request.POST.get('step2_angle'),
                step2_left_shoulder_adduction_image = request.POST.get('step2_image'),
                step3_left_shoulder_adduction_angle = request.POST.get('step3_angle'),
                step3_left_shoulder_adduction_image = request.POST.get('step3_image'),
                left_shoulder_adduction_min_angle = request.POST.get('angle'),
                left_shoulder_adduction_avg_angle  = request.POST.get('mean_angle')
            )
        else:
            user.update(
                step1_right_shoulder_adduction_angle = request.POST.get('step1_angle'),
                step1_right_shoulder_adduction_image = request.POST.get('step1_image'),
                step2_right_shoulder_adduction_angle = request.POST.get('step2_angle'),
                step2_right_shoulder_adduction_image = request.POST.get('step2_image'),
                step3_right_shoulder_adduction_angle = request.POST.get('step3_angle'),
                step3_right_shoulder_adduction_image = request.POST.get('step3_image'),
                right_shoulder_adduction_min_angle = request.POST.get('angle'),
                right_shoulder_adduction_avg_angle  = request.POST.get('mean_angle'),
            )
        
        return Response({})

class ShoulderFlextionROMAPI(APIView):
    '''
        어깨굴곡
        3차측정중 선택된 왼쪽,오른쪽어깨굴곡 각도와이미지 db저장
    '''
    def post(self, request,**kwargs):
        
        user = UserInfomation.objects.filter(uuid=request.POST.get('uuid'))

        if kwargs.get('left_or_right') == 'left':
            user.update(
                step1_left_shoulder_flextion_angle = request.POST.get('step1_angle'),
                step1_left_shoulder_flextion_image = request.POST.get('step1_image'),
                step2_left_shoulder_flextion_angle = request.POST.get('step2_angle'),
                step2_left_shoulder_flextion_image = request.POST.get('step2_image'),
                step3_left_shoulder_flextion_angle = request.POST.get('step3_angle'),
                step3_left_shoulder_flextion_image = request.POST.get('step3_image'),
                left_shoulder_flextion_max_angle = request.POST.get('angle'),
                left_shoulder_flextion_avg_angle  = request.POST.get('mean_angle')
            )
        else:
            user.update(
                step1_right_shoulder_flextion_angle = request.POST.get('step1_angle'),
                step1_right_shoulder_flextion_image = request.POST.get('step1_image'),
                step2_right_shoulder_flextion_angle = request.POST.get('step2_angle'),
                step2_right_shoulder_flextion_image = request.POST.get('step2_image'),
                step3_right_shoulder_flextion_angle = request.POST.get('step3_angle'),
                step3_right_shoulder_flextion_image = request.POST.get('step3_image'),
                right_shoulder_flextion_max_angle = request.POST.get('angle'),
                right_shoulder_flextion_avg_angle  = request.POST.get('mean_angle'),
            )
        
        return Response({})

class ShoulderExtensionROMAPI(APIView):
    '''
        어깨신전
        3차측정중 선택된 왼쪽,오른쪽어깨신전 각도와이미지 db저장
    '''
    def post(self, request,**kwargs):
        
        user = UserInfomation.objects.filter(uuid=request.POST.get('uuid'))

        if kwargs.get('left_or_right') == 'left':
            user.update(
                step1_left_shoulder_extension_angle = request.POST.get('step1_angle'),
                step1_left_shoulder_extension_image = request.POST.get('step1_image'),
                step2_left_shoulder_extension_angle = request.POST.get('step2_angle'),
                step2_left_shoulder_extension_image = request.POST.get('step2_image'),
                step3_left_shoulder_extension_angle = request.POST.get('step3_angle'),
                step3_left_shoulder_extension_image = request.POST.get('step3_image'),
                left_shoulder_extension_max_angle = request.POST.get('angle'),
                left_shoulder_extension_avg_angle  = request.POST.get('mean_angle')
            )
        else:
            user.update(
                step1_right_shoulder_extension_angle = request.POST.get('step1_angle'),
                step1_right_shoulder_extension_image = request.POST.get('step1_image'),
                step2_right_shoulder_extension_angle = request.POST.get('step2_angle'),
                step2_right_shoulder_extension_image = request.POST.get('step2_image'),
                step3_right_shoulder_extension_angle = request.POST.get('step3_angle'),
                step3_right_shoulder_extension_image = request.POST.get('step3_image'),
                right_shoulder_extension_max_angle = request.POST.get('angle'),
                right_shoulder_extension_avg_angle  = request.POST.get('mean_angle'),
            )
        
        return Response({})

class ElbowFlextionROMAPI(APIView):
    '''
        팔꿈치굴곡
        3차측정중 선택된 왼쪽,오른쪽팔꿈치굴곡 각도와이미지 db저장
    '''
    def post(self, request,**kwargs):
        
        user = UserInfomation.objects.filter(uuid=request.POST.get('uuid'))

        if kwargs.get('left_or_right') == 'left':
            user.update(
                step1_left_elbow_flextion_angle = request.POST.get('step1_angle'),
                step1_left_elbow_flextion_image = request.POST.get('step1_image'),
                step2_left_elbow_flextion_angle = request.POST.get('step2_angle'),
                step2_left_elbow_flextion_image = request.POST.get('step2_image'),
                step3_left_elbow_flextion_angle = request.POST.get('step3_angle'),
                step3_left_elbow_flextion_image = request.POST.get('step3_image'),
                left_elbow_flextion_max_angle = request.POST.get('angle'),
                left_elbow_flextion_avg_angle  = request.POST.get('mean_angle')
            )
        else:
            user.update(
                step1_right_elbow_flextion_angle = request.POST.get('step1_angle'),
                step1_right_elbow_flextion_image = request.POST.get('step1_image'),
                step2_right_elbow_flextion_angle = request.POST.get('step2_angle'),
                step2_right_elbow_flextion_image = request.POST.get('step2_image'),
                step3_right_elbow_flextion_angle = request.POST.get('step3_angle'),
                step3_right_elbow_flextion_image = request.POST.get('step3_image'),
                right_elbow_flextion_max_angle = request.POST.get('angle'),
                right_elbow_flextion_avg_angle  = request.POST.get('mean_angle'),
            )
        
        return Response({})


class ElbowExtensionROMAPI(APIView):
    '''
        팔꿈치신전
        3차측정중 선택된 왼쪽,오른쪽팔꿈치신전 각도와이미지 db저장
    '''
    def post(self, request,**kwargs):
        
        user = UserInfomation.objects.filter(uuid=request.POST.get('uuid'))

        if kwargs.get('left_or_right') == 'left':
            user.update(
                step1_left_elbow_extension_angle = request.POST.get('step1_angle'),
                step1_left_elbow_extension_image = request.POST.get('step1_image'),
                step2_left_elbow_extension_angle = request.POST.get('step2_angle'),
                step2_left_elbow_extension_image = request.POST.get('step2_image'),
                step3_left_elbow_extension_angle = request.POST.get('step3_angle'),
                step3_left_elbow_extension_image = request.POST.get('step3_image'),
                left_elbow_extension_min_angle = request.POST.get('angle'),
                left_elbow_extension_avg_angle  = request.POST.get('mean_angle')
            )
        else:
            user.update(
                step1_right_elbow_extension_angle = request.POST.get('step1_angle'),
                step1_right_elbow_extension_image = request.POST.get('step1_image'),
                step2_right_elbow_extension_angle = request.POST.get('step2_angle'),
                step2_right_elbow_extension_image = request.POST.get('step2_image'),
                step3_right_elbow_extension_angle = request.POST.get('step3_angle'),
                step3_right_elbow_extension_image = request.POST.get('step3_image'),
                right_elbow_extension_min_angle = request.POST.get('angle'),
                right_elbow_extension_avg_angle  = request.POST.get('mean_angle'),
            )
        
        return Response({})
    

class ROMAPI(APIView):
    def get(self, request):
        print("GET 요청 왔음") 
        return Response({"message" : "안녕하시미켄"}, status=200)
        
    def post(self, request):
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        user_id = data.get("user_id")
        _type = data.get("type")
        value = data.get("value")
        print(data)

        # 측정 기록
        try:
            ROMMeasureLog.objects.create(
                uuid=user_id,
                type=_type,
                value=value,
            )
            user = UserInfo.objects.filter(user__username=user_id)
            user.update(**{_type : value})

            return Response({"message" : "측정이 완료되었습니다."}, status=200)
        except Exception as err:
            print(err)
            return Response({"message" : f"측정 도중 문제가 발생했습니다.\n{err}"}, status=200)

class MuscleFunctionLog(APIView):
    """
    근기능 검사 수행 로그
    - 사용자
    - 측정일시
    - 측정 데이터 (JSON)
    """
    def post(self, request):
        print("운동 데이터 요청")
        print(request.POST)
        try:
            MuscleFunctionLogData.objects.create(
                user_id=request.POST.get('user'),
                exercise_type=request.POST.get('type'),
                log=request.POST.get('log'),
                extra=request.POST.get('extra'),
            )
        except Exception as err:
            print(err)
        return Response({}, status=200)

class UserROM(APIView):
    def post(self, request):
        user_id = request.POST.get('user_id')
        _type = request.POST.get('type')
        data = request.POST.getlist('data')
        
        try:
            ROMLogData.objects.create(
                user_id=user_id,
                type=_type,
                data=json.dumps(data)
            )
        except Exception as err:
            print(err)
        
        return Response({})