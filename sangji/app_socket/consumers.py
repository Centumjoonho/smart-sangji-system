import json
import io
from os import lseek
import random
import time
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from PIL import Image
import cv2
import time
import numpy as np
import mediapipe as mp
import pickle
import base64
import datetime
from django.http import JsonResponse
from mole_game_package.Player import Player
from .analyzers import *
from .models import *

from .ROM import *

from app_socket.draw import draw_angle
from mole_game_package.Player import Player

def draw_grid(img, line_color=(162, 162, 162), thickness=2, type_=8, pxstep=50):
    '''(ndarray, 3-tuple, int, int) -> void
    draw gridlines on img
    line_color:
        BGR representation of colour
    thickness:
        line thickness
    type:
        8, 4 or cv2.LINE_AA
    pxstep:
        grid line frequency in pixels
    '''
    x = pxstep
    y = pxstep
    while x < img.shape[1]:
        cv2.line(img, (x, 0), (x, img.shape[0]), color=line_color, lineType=type_, thickness=thickness)
        x += pxstep

    while y < img.shape[0]:
        cv2.line(img, (0, y), (img.shape[1], y), color=line_color, lineType=type_, thickness=thickness)
        y += pxstep
        
mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic
mp_pose = mp.solutions.pose
hr = HeartRateProcess()

def image_to_bytearray(image):
    pil_im = Image.fromarray(image)
    b = io.BytesIO()
    # b = io.StringIO(s)
    pil_im.save(b, 'jpeg')
    im_bytes = b.getvalue()
    return im_bytes

class MoleGameConsumer(AsyncWebsocketConsumer):
    '''
        두더지게임처리용 소켓 consumer
    '''
    async def connect(self):
        print("수립")
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        self.hand = "right_hand"
        self.game_id = ""
        self.username = ""
        await self.accept()

    async def disconnect(self,close_code):
        print("해제")

    async def receive(self, text_data=None, bytes_data=None):
        """
        :param str text_data: text data from socket
        :param byte bytes_data: bytes data from socket
        :return: 손 좌표와 손 감지 여부에 대한 json
        :rtype: json
        :raises AttributeError: 랜드마크가 감지되지 않았을 경우
        """
        if not bytes_data:
            text_data_json = json.loads(text_data)
            print(text_data_json)
            self.hand = text_data_json.get('hand')
            self.game_id = text_data_json.get('gameId')
            self.username = text_data_json.get('username')
            return
        else:    
            bitmap_to_image = Image.open(io.BytesIO(bytes_data)) 
            image = np.asarray(bitmap_to_image)
            detect_hands = True
            loc = [0, 0]

            try:
                image = cv2.flip(image, 1)
                results = self.pose.process(image)
                pose_landmarks = results.pose_landmarks
                landmarks  = pose_landmarks.landmark
                # 각도
                right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                right_elbow    = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                right_wrist    = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                right_hip      = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]

                left_shoulder  = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                left_elbow     = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                left_wrist     = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                left_hip       = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]

                if self.hand == "right_hand":
                    loc = [landmarks[self.mp_pose.PoseLandmark.LEFT_INDEX.value].x,landmarks[self.mp_pose.PoseLandmark.LEFT_INDEX.value].y]
                    angle_1 = self.calculate_angle(
                                left_shoulder,
                                left_elbow,
                                left_wrist
                            )
                    angle_2 = self.calculate_angle(
                                left_shoulder,
                                left_elbow,
                                left_hip
                            )
                else:
                    loc = [landmarks[self.mp_pose.PoseLandmark.RIGHT_INDEX.value].x,landmarks[self.mp_pose.PoseLandmark.RIGHT_INDEX.value].y]
                    angle_1 = self.calculate_angle(
                                right_shoulder,
                                right_elbow,
                                right_wrist
                            )
                    angle_2 = self.calculate_angle(
                                right_shoulder,
                                right_elbow,
                                right_hip
                            )
          
                await self.save_log(angle_1, angle_2)
            except AttributeError as err:
                detect_hands = False

            await self.send(text_data=json.dumps({
                'curX': loc[0],
                'curY': loc[1],
                'detect_hands' : detect_hands
            }))

    @database_sync_to_async
    def save_log(self, angle_1, angle_2):
        """
        각 관절 각도 저장
        :param int angle_1: 겨드랑이 각도
        :param int angle_2: 팔꿈치 각도
        """
        MoleDataLog.objects.create(
            game_id=self.game_id,
            username=self.username,
            timestamp=str(int(time.time() * 1000)),
            angle_1=int(angle_1),
            angle_2=int(angle_2)
        )

    def calculate_angle(self, a, b, c):
        a = np.array(a) # First
        b = np.array(b) # Mid
        c = np.array(c) # End
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle >180.0:
            angle = 360-angle
            
        return angle

class MoleGameDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("두더지 잡기 게임 데이터 소켓 연결")
        await self.accept()

    async def disconnect(self, close_code):
        print("두더지 잡기 게임 데이터 소켓 해제")

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                await self.save_log(json.loads(text_data))
            except Exception as err:
                print(err)


    @database_sync_to_async
    def save_log(self, data):
        MoleDataLog.objects.create(
            game_id=data.get("gameId"),
            username=data.get("username"),
            timestamp=data.get("time"),
            grid_size=data.get("splitScreenCnt"),
            hit_count=data.get("hitCnt"),
            mole_position=data.get("molePosition"),
            pane_count=data.get("paneCnt"),
            hammer_position=data.get("handPosition"),
        )

class IsometricExerciseTestLatPullDownConsumer(AsyncWebsocketConsumer):
    """
    운동 기능 검사 등척성 검사 - 랫 풀 다운
    """
    async def connect(self):
        print("운동 기능 검사 등척성 검사 - 랫 풀 다운 컨슈머 연결")
        self.uuid = None
        self.level = None # 단계 설정
        self.second = None # 초 단위 설정값
        self.count = None # 측정 횟수 설정값

        self.is_start = False # 시작 상태 플래그
        self.is_finish = False # 종료 상태 플래그

        # 랫 풀 다운
        self.use_skeleton = True
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        self.client_datas = 0
        self.client_datas = 0 # 운동 횟수
        self.right_shoulder = None
        self.right_elbow    = None
        self.right_wrist    = None
        self.left_shoulder  = None
        self.left_elbow     = None
        self.left_wrist     = None
        self.PUSH_ANGLE = 150 # 해당 각도를 10단계로 구분함
        self.PULL_ANGLE = 70
        self.up_status = False
        self.left_check = False
        self.right_check = False
        self.last_left_angle = None
        self.last_right_angle = None

        # 각도 기록
        self.last_elbow_left_angles = []
        self.last_elbow_right_angles = []
        self.last_shoulder_right_angles = []
        self.last_shoulder_left_angles = []

        # 센서 값
        self.strengh_values = {}
        self.position_flag = None # 최대점 측정 [0], 중간점 측정 [1], 최저점 측정 [2] 
        self.now_count = -1  # 현재 카운트
        self.now_step = 0
        
        

        await self.accept()

    async def disconnect(self, close_code):
        print("운동 기능 검사 등척성 검사 - 랫 풀 다운 컨슈머 연결 해제", close_code)

    async def receive(self, text_data=None, bytes_data=None):
        if not bytes_data:
            try:
                print(text_data)
                text_data_json = json.loads(text_data)
                action = text_data_json.get("action") # send 시 액션을 넘겨줘야 함.

                if action == "intialize":
                    self.uuid = text_data_json.get("uuid") 
                    self.level = text_data_json.get("level") 
                    self.second = text_data_json.get("second")
                    self.count = text_data_json.get("count")
                    self.now_count = self.count # (추가)
                    # 측정 값 초기화
                    # 세트 별 측정 + 최대·중간·최저점별 측정
                    self.strengh_values = {
                        0 : [ [] for i in range(int(self.count))],
                        1 : [ [] for i in range(int(self.count))],
                        2 : [ [] for i in range(int(self.count))]
                     }
                    # self.set_angle(self.level)

                elif action == "start":
                    self.is_start = True
                    self.is_finish = False
                    self.position_flag = text_data_json.get("flag")
                    
                elif action == "count_down":
                    # 초 단위가 지나갈 경우 -> 3초에 한 번씩 인터벌이 깎일 때
                    count = text_data_json.get('count')
                    self.now_count = count
                    print(self.now_count)
                    if count == 0:
                        print("운동 종료")
                        self.is_finish = True # 운동 종료 처리
                        await self.save_user_strengh(self.position_flag) # 최대 근력 DB 저장
                        await self.send(text_data=json.dumps({
                            'count' : self.client_datas,
                            'is_finish' : self.is_finish,
                            "step" : self.now_step,
                            'last_right_angle' : self.last_right_angle,
                            'last_left_angle' : self.last_left_angle
                        }))

                elif action == "sensor":
                    # 센서값 발생
                    _type = text_data_json.get("type") 
                    value = text_data_json.get("value") 
                    if self.is_start and self.now_count > -1:
                        # self.strengh_values[self.flag]
                        try:
                            self.strengh_values[self.position_flag][self.now_count-1].append(value)
                            # self.strengh_values[self.position_flag][self.now_count].append(value)
                        except Exception as err:
                            print(err) 

            except Exception as err:
                print("여기 에러?", err, text_data)

            return
        
        bitmap_to_image = Image.open(io.BytesIO(bytes_data)) # 안드로이드에서 넘겨온 이미지 ByteArray를 이미지로 처리함.
        image_array = np.asarray(bitmap_to_image) # ByteArray를 이미지로 처리한 결과를 np.array로 변경함

        image = image_array
        image = cv2.flip(image, 1)
        image.flags.writeable = False
        results = self.pose.process(image)

        # 랫 풀 다운
        if not self.is_finish and self.is_start: # 측정 시작 조건
            try:  
                landmarks = results.pose_landmarks.landmark
                self.right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                self.right_elbow    = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                self.right_wrist    = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                self.right_hip      = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]

                self.left_shoulder  = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                self.left_elbow     = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                self.left_wrist     = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                self.left_hip       = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                
                self.saveAngles() # 각도 저장

                self.left_check = self.check_left_arm(landmarks)
                self.right_check = self.check_right_arm(landmarks)

                if self.left_check and self.right_check:
                    self.up_status = True

                if self.up_status == True and \
                    self.check_left_arm_pulldown(landmarks) and \
                    self.check_right_arm_pulldown(landmarks):
                    
                    self.client_datas += 1 
                    self.up_status = False

            except Exception as e:
                print(e)
            # 저장 항목
            # print(self.last_left_strength, self.last_right_strength, self.last_right_angle, self.last_left_angle, time.time(), self.count, self.level, self.second)

            await self.send(text_data=json.dumps({
                'count' : self.client_datas,
                'is_finish' : self.is_finish,
                "step" : self.now_step,
                'last_right_angle' : self.last_right_angle,
                'last_left_angle' : self.last_left_angle
            }))

        if self.use_skeleton:
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        try:
            draw_grid(image)
        except:
            pass

        processed_image = image_to_bytearray(image)
        await self.send(bytes_data=processed_image)    

    def saveAngles(self):
        self.last_elbow_left_angle = self.calculate_angle(self.left_shoulder,self.left_elbow,self.left_wrist)
        self.last_elbow_right_angle = self.calculate_angle(self.right_shoulder,self.right_elbow,self.right_wrist)
        self.last_shoulder_right_angle = self.calculate_angle(self.right_elbow,self.right_shoulder,self.right_hip)
        self.last_shoulder_left_angle = self.calculate_angle(self.left_elbow,self.left_shoulder,self.left_hip)

        # 각도 저장
        self.last_elbow_left_angles.append(self.last_elbow_left_angle)
        self.last_elbow_right_angles.append(self.last_elbow_right_angle)
        self.last_shoulder_right_angles.append(self.last_shoulder_right_angle)
        self.last_shoulder_left_angles.append(self.last_shoulder_left_angle)

        

    def set_angle(self, level):
        # 단계 설정에 따라서 각도 설정
        # 45-180 도에 대한 도수분포표
        # [ 45.   58.5  72.   85.5  99.  112.5 126.  139.5 153.  166.5 180. ]
        if level == 10:
            self.PUSH_ANGLE = 180
        elif level == 9:
            self.PUSH_ANGLE = 166
        elif level == 8:
            self.PUSH_ANGLE = 153
        elif level == 7:
            self.PUSH_ANGLE = 139
        elif level == 6:
            self.PUSH_ANGLE = 126
        elif level == 5:
            self.PUSH_ANGLE = 112
        elif level == 4:
            self.PUSH_ANGLE = 85
        elif level == 3:
            self.PUSH_ANGLE = 72
        elif level == 2:
            self.PUSH_ANGLE = 58
        elif level == 1:
            self.PUSH_ANGLE = 45
        
        print(self.PUSH_ANGLE) 

        self.PUSH_ANGLE 
        print("단계를 설정합니다.") 

    def calculate_angle(self, a, b, c):
        a = np.array(a) # First
        b = np.array(b) # Mid
        c = np.array(c) # End
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle >180.0:
            angle = 360-angle
            
        return angle

    def check_left_arm(self, landmarks):
        '''
            왼쪽팔 위로 올렸는지 체크하기
            Return
                왼쪽손목 y좌표가 외쪽눈 y좌표 위에위치하고 팔 각도가 160 이상이면 True 아니면 False
        '''

        left_eye_y = landmarks[mp_pose.PoseLandmark.LEFT_EYE.value].y
        angle = self.calculate_angle(self.left_shoulder,self.left_elbow,self.left_wrist)
        self.last_left_angle = angle
        
        if angle >= self.PUSH_ANGLE and self.left_wrist[1] < left_eye_y:
            return True
        return False

    
    def check_right_arm(self,landmarks):
        '''
            오른쪽 팔 위로 올렸는지 체크
            Return
                오른쪽손목 y좌표가 오른쪽눈 y좌표 위에위치하고 팔 각도가 160 이상이면 True 아니면 False
        '''
        right_eye_y = landmarks[mp_pose.PoseLandmark.RIGHT_EYE.value].y
        angle = self.calculate_angle(self.right_shoulder,self.right_elbow,self.right_wrist)
        self.last_right_angle = angle

        if angle >= self.PUSH_ANGLE and self.right_wrist[1] < right_eye_y:
            return True
        return False

    def check_right_arm_pulldown(self, landmarks):
        '''
            오른쪽 팔 끌어내렸는지 체크
            Return
                오른쪽손목 y좌표가 오른쪽입 y좌표 아래에 위치하고 팔각도가 70이하면 True 아니면 False
        '''

        mouth_right_y = landmarks[mp_pose.PoseLandmark.MOUTH_RIGHT.value].y
        angle = self.calculate_angle(self.right_shoulder,self.right_elbow,self.right_wrist)

        if angle <= self.PULL_ANGLE and mouth_right_y <= self.right_wrist[1]:
            return True
        
        return False


    def check_left_arm_pulldown(self, landmarks):
        '''
            오른쪽 팔 끌어내렸는지 체크
            Return
                왼쪽손목 y좌표가 왼쪽입 y좌표 아래에 위치하고 팔각도가 70이하면 True 아니면 False
        '''

        mouth_left_y = landmarks[mp_pose.PoseLandmark.MOUTH_LEFT.value].y
        angle = self.calculate_angle(self.left_shoulder,self.left_elbow,self.left_wrist)
        #print("right_leftdown: ",angle)

        if angle <= self.PULL_ANGLE and mouth_left_y <= self.left_wrist[1]:
            return True
        
        return False
    
    def reset_angles(self):
        self.last_elbow_left_angles = []
        self.last_elbow_right_angles = []
        self.last_shoulder_right_angles = []
        self.last_shoulder_left_angles = []

    @database_sync_to_async
    def save_user_strengh(self, flag):
        """
        유저 근력 저장
        """
        def get_max_value(strengths):
            print(strengths)
            _max_value = 0
            for _strength in strengths:
                count_max = max(_strength) # 해당 세트의 최댓값
                if count_max > _max_value:
                    _max_value = count_max
            return _max_value

        def get_avg_value(strengths):
            _sum = 0
            _cnt = 0
            try:
                for _strength in strengths:
                    for _str in _strength:
                        _sum += _str
                        _cnt += 1
                return round(_sum /_cnt, 2)
            except Exception as err:
                print(err)
                return 0

        user = UserInfomation.objects.filter(uuid=self.uuid)
        if flag == 0:
            strengths = self.strengh_values[0]
            if strengths:
                user.update(maxium_strengh=get_avg_value(strengths))
                print("최대점 측정 완료")
            # 최대점 평균 각도 저장
            user.update(
                isometric_latpulldown_max_position_last_elbow_left_angle=np.mean(self.last_elbow_left_angles),
                isometric_latpulldown_max_position_last_elbow_right_angle=np.mean(self.last_elbow_right_angles),
                isometric_latpulldown_max_position_last_shoulder_right_angle=np.mean(self.last_shoulder_right_angles),
                isometric_latpulldown_max_position_last_shoulder_left_angle=np.mean(self.last_shoulder_left_angles),
            )
            self.reset_angles()
            self.now_step = '1' 
                    
        elif flag == 1:
            strengths = self.strengh_values[1]
            if strengths:
                user.update(minium_strengh=get_avg_value(strengths))
                print("중간점 측정 완료")
            # 중간점 평균 각도 저장
            user.update(
                isometric_latpulldown_mid_position_last_elbow_left_angle=np.mean(self.last_elbow_left_angles),
                isometric_latpulldown_mid_position_last_elbow_right_angle=np.mean(self.last_elbow_right_angles),
                isometric_latpulldown_mid_position_last_shoulder_right_angle=np.mean(self.last_shoulder_right_angles),
                isometric_latpulldown_mid_position_last_shoulder_left_angle=np.mean(self.last_shoulder_left_angles),
            )
            self.reset_angles()
            self.now_step = '2'


        elif flag == 2:
            strengths = self.strengh_values[2]
            if strengths:
                user.update(midium_strengh=get_avg_value(strengths))
                print("최저점 측정 완료")
            # 최저점 평균 각도 저장
            user.update(
                isometric_latpulldown_min_position_last_elbow_left_angle=np.mean(self.last_elbow_left_angles),
                isometric_latpulldown_min_position_last_elbow_right_angle=np.mean(self.last_elbow_right_angles),
                isometric_latpulldown_min_position_last_shoulder_right_angle=np.mean(self.last_shoulder_right_angles),
                isometric_latpulldown_min_position_last_shoulder_left_angle=np.mean(self.last_shoulder_left_angles),
            )
            user.update(strength_logs=json.dumps(self.strengh_values)) # 종료 시점에 로그 저장
            self.reset_angles()
            self.now_step = '3' # 측정 종료
    
class IsokineticsExerciseTestLatPullDownConsumer(AsyncWebsocketConsumer):
    """
    운동 기능 검사 등속성 검사 - 랫 풀 다운
    """
    async def connect(self):
        print("운동 기능 검사 등속성 검사 - 랫 풀 다운 컨슈머 연결")
        self.angle = None 
        self.count = None 
        self.uuid = None
        self.remain_count = None
        self.is_start = False # 시작 상태 플래그
        self.is_finish = False # 종료 상태 플래그
        # 랫 풀 다운
        self.use_skeleton = True
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        self.client_datas = 0
        self.client_datas = 0 # 운동 횟수
        self.right_shoulder = None
        self.right_elbow    = None
        self.right_wrist    = None
        self.left_shoulder  = None
        self.left_elbow     = None
        self.left_wrist     = None
        self.PUSH_ANGLE = 150 # 각속도 부분
        self.PULL_ANGLE = 70
        self.up_status = False
        self.left_check = False
        self.right_check = False
        self.last_left_angle = None
        self.last_right_angle = None
        # 센서 값
        self.strengh_values = []
        self.last_left_strength = None
        self.last_right_strength = None

        await self.accept()

    async def disconnect(self, close_code):
        print("운동 기능 검사 등속성 검사 - 랫 풀 다운 컨슈머 연결 해제")


    async def receive(self, text_data=None, bytes_data=None):
        if not bytes_data:
            try:   
                text_data_json = json.loads(text_data)
                action = text_data_json.get("action") # send 시 액션을 넘겨줘야 함.

                if action == "intialize":
                    print("초기화")
                    self.uuid = text_data_json.get("uuid") 
                    self.angle = text_data_json.get("angle", 180)
                    self.count = text_data_json.get("count", 0)
                    self.PUSH_ANGLE = int(self.angle)
                    self.remain_count = int(self.count)
                    self.user_max_strength = await self.get_user_max_strengh()
                elif action == "set_user_strengh":
                    print("사용자 최대 근력 설정")
                    self.user_max_strength = text_data_json.get("value")
                elif action == "start":
                    self.is_start = True
                elif action == "sensor":
                    # 센서값 발생
                    _type = text_data_json.get("type") 
                    value = text_data_json.get("value") 
                    print(_type, value)
            except Exception as err:
                print(err)
            return
        
        bitmap_to_image = Image.open(io.BytesIO(bytes_data)) # 안드로이드에서 넘겨온 이미지 ByteArray를 이미지로 처리함.
        image_array = np.asarray(bitmap_to_image) # ByteArray를 이미지로 처리한 결과를 np.array로 변경함

        image = image_array
        image = cv2.flip(image, 1)
        image.flags.writeable = False
        results = self.pose.process(image)
        strengh_condition = False # 최대 근력의 80%보다 약한가 강한가 체크

        # 랫 풀 다운
        if not self.is_finish and self.is_start: # 측정 시작 조건
            try:  
                landmarks = results.pose_landmarks.landmark
                self.right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                self.right_elbow    = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                self.right_wrist    = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

                self.left_shoulder  = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                self.left_elbow     = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                self.left_wrist     = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                self.left_check = self.check_left_arm(landmarks)
                self.right_check = self.check_right_arm(landmarks)

                if self.left_check and self.right_check:
                    self.up_status = True

                if self.up_status == True and \
                    self.check_left_arm_pulldown(landmarks) and \
                    self.check_right_arm_pulldown(landmarks):

                    if self.last_left_strength < self.user_max_strength * 0.8 or \
                            self.last_right_strength < self.user_max_strength * 0.8:
                        print("최대 근력의 80% 보다 낮으십니다")
                    else:
                        strengh_condition = True
                        self.client_datas += 1 
                        self.remain_count -= 1

                        if self.remain_count == 0:
                            print("운동 종료")
                            self.is_finish = True

                    self.up_status = False

            except Exception as e:
                print(e)
            # 저장 항목

            await self.send(text_data=json.dumps({
                'remain_count' : self.remain_count,
                'count' : self.client_datas,
                'is_finish' : self.is_finish,
                'last_right_angle' : self.last_right_angle,
                'last_left_angle' : self.last_left_angle,
                'user_max_strengh' : self.user_max_strength,
                'strengh_condition' : strengh_condition
            }))

        if self.use_skeleton:
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        processed_image = image_to_bytearray(image)
        await self.send(bytes_data=processed_image)    

    def set_angle(self):
        # 단계 설정에 따라서 각도 설정
        print("단계를 설정합니다.") 

    def calculate_angle(self, a, b, c):
        a = np.array(a) # First
        b = np.array(b) # Mid
        c = np.array(c) # End
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle >180.0:
            angle = 360-angle
            
        return angle

    def check_left_arm(self, landmarks):
        '''
            왼쪽팔 위로 올렸는지 체크하기
            Return
                왼쪽손목 y좌표가 외쪽눈 y좌표 위에위치하고 팔 각도가 160 이상이면 True 아니면 False
        '''

        left_eye_y = landmarks[mp_pose.PoseLandmark.LEFT_EYE.value].y
        angle = self.calculate_angle(self.left_shoulder,self.left_elbow,self.left_wrist)
        self.last_left_angle = angle
        
        if angle >= self.PUSH_ANGLE and self.left_wrist[1] < left_eye_y:
            return True
        return False

    
    def check_right_arm(self,landmarks):
        '''
            오른쪽 팔 위로 올렸는지 체크
            Return
                오른쪽손목 y좌표가 오른쪽눈 y좌표 위에위치하고 팔 각도가 160 이상이면 True 아니면 False
        '''
        right_eye_y = landmarks[mp_pose.PoseLandmark.RIGHT_EYE.value].y
        angle = self.calculate_angle(self.right_shoulder,self.right_elbow,self.right_wrist)
        self.last_right_angle = angle

        if angle >= self.PUSH_ANGLE and self.right_wrist[1] < right_eye_y:
            return True
        return False

    def check_right_arm_pulldown(self, landmarks):
        '''
            오른쪽 팔 끌어내렸는지 체크
            Return
                오른쪽손목 y좌표가 오른쪽입 y좌표 아래에 위치하고 팔각도가 70이하면 True 아니면 False
        '''

        mouth_right_y = landmarks[mp_pose.PoseLandmark.MOUTH_RIGHT.value].y
        angle = self.calculate_angle(self.right_shoulder,self.right_elbow,self.right_wrist)

        if angle <= self.PULL_ANGLE and mouth_right_y <= self.right_wrist[1]:
            return True
        
        return False


    def check_left_arm_pulldown(self, landmarks):
        '''
            오른쪽 팔 끌어내렸는지 체크
            Return
                왼쪽손목 y좌표가 왼쪽입 y좌표 아래에 위치하고 팔각도가 70이하면 True 아니면 False
        '''

        mouth_left_y = landmarks[mp_pose.PoseLandmark.MOUTH_LEFT.value].y
        angle = self.calculate_angle(self.left_shoulder,self.left_elbow,self.left_wrist)
        #print("right_leftdown: ",angle)

        if angle <= self.PULL_ANGLE and mouth_left_y <= self.left_wrist[1]:
            return True
        
        return False
    
    @database_sync_to_async
    def get_user_max_strengh(self):
        """
        유저 최대근력 반환
        """
        user = UserInfomation.objects.filter(uuid=self.uuid)
        if user:
            return user[0].maxium_strengh
        return None

class IsotonicExerciseTestLatPullDownConsumer(AsyncWebsocketConsumer):
    """
    운동 기능 검사 등장성 검사 - 랫 풀 다운
    """
    async def connect(self):
        print("운동 기능 검사 등장성 검사 - 랫 풀 다운 컨슈머 연결")
        self.rm = None 
        self.count = None 
        self.remain_count = None
        self.uuid = None
        self.is_start = False # 시작 상태 플래그
        self.is_finish = False # 종료 상태 플래그
        # 랫 풀 다운
        self.use_skeleton = True
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        self.client_datas = 0
        self.client_datas = 0 # 운동 횟수
        self.right_shoulder = None
        self.right_elbow    = None
        self.right_wrist    = None
        self.left_shoulder  = None
        self.left_elbow     = None
        self.left_wrist     = None
        self.PUSH_ANGLE = 100 # 각속도 부분
        self.PULL_ANGLE = 70
        self.up_status = False
        self.left_check = False
        self.right_check = False
        self.last_left_angle = None
        self.last_right_angle = None
        # 센서 값
        self.strengh_values = []
        self.last_left_strength = None
        self.last_right_strength = None

        await self.accept()

    async def disconnect(self, close_code):
        print("운동 기능 검사 등장성 검사 - 랫 풀 다운 컨슈머 연결 해제")

    async def receive(self, text_data=None, bytes_data=None):
        if not bytes_data:
            try:   
                text_data_json = json.loads(text_data)
                action = text_data_json.get("action") # send 시 액션을 넘겨줘야 함.

                if action == "intialize":
                    self.uuid = text_data_json.get("uuid") 
                    self.rm = text_data_json.get("rm")
                    self.remain_count = int(self.rm)
                elif action == "start":
                    self.is_start = True
                elif action == "sensor":
                    # 센서값 발생
                    _type = text_data_json.get("type") 
                    value = text_data_json.get("value") 
                elif action == "set_5rm":
                    print("5rm 설정 진행")
                    _type = text_data_json.get('type')
                    rm = text_data_json.get('5rm', '1500')
                    await self.save_user_5rm(_type, rm)

            except Exception as err:
                print(err)
            return
        
        bitmap_to_image = Image.open(io.BytesIO(bytes_data)) # 안드로이드에서 넘겨온 이미지 ByteArray를 이미지로 처리함.
        image_array = np.asarray(bitmap_to_image) # ByteArray를 이미지로 처리한 결과를 np.array로 변경함

        image = image_array
        image = cv2.flip(image, 1)
        image.flags.writeable = False
        results = self.pose.process(image)
        strengh_condition = False # 최대 근력의 80%보다 약한가 강한가 체크

        # 랫 풀 다운
        if not self.is_finish and self.is_start: # 측정 시작 조건
            try:  
                landmarks = results.pose_landmarks.landmark
                self.right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                self.right_elbow    = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                self.right_wrist    = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

                self.left_shoulder  = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                self.left_elbow     = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                self.left_wrist     = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                self.left_check = self.check_left_arm(landmarks)
                self.right_check = self.check_right_arm(landmarks)

                if self.left_check and self.right_check:
                    self.up_status = True

                if self.up_status == True and \
                    self.check_left_arm_pulldown(landmarks) and \
                    self.check_right_arm_pulldown(landmarks):
                
                    self.client_datas += 1 
                    self.remain_count -= 1

                    if self.remain_count == 0:
                        print("운동 종료")
                        self.is_finish = True

                    self.up_status = False

            except Exception as e:
                print(e)
            # 저장 항목

            await self.send(text_data=json.dumps({
                'remain_count' : self.remain_count,
                'count' : self.client_datas,
                'is_finish' : self.is_finish,
                'last_right_angle' : self.last_right_angle,
                'last_left_angle' : self.last_left_angle,
            }))

        if self.use_skeleton:
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        processed_image = image_to_bytearray(image)
        await self.send(bytes_data=processed_image)    

    @database_sync_to_async
    def save_user_5rm(self, _type, weight):
        user = UserInfomation.objects.filter(uuid=self.uuid)
        print(weight, user)
        if user:
            if _type == 'min':
                user.update(RM_5_min=int(weight))
                print("5RM 최저 저장 완료") 
            elif _type == 'mid':
                user.update(RM_5_mid=int(weight))
                print("5RM 중간 저장 완료") 
            elif _type == 'max':
                user.update(RM_5_max=int(weight))
                print("5RM 최대 저장 완료") 

    def calculate_angle(self, a, b, c):
        a = np.array(a) # First
        b = np.array(b) # Mid
        c = np.array(c) # End
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle >180.0:
            angle = 360-angle
            
        return angle

    def check_left_arm(self, landmarks):
        '''
            왼쪽팔 위로 올렸는지 체크하기
            Return
                왼쪽손목 y좌표가 외쪽눈 y좌표 위에위치하고 팔 각도가 160 이상이면 True 아니면 False
        '''

        left_eye_y = landmarks[mp_pose.PoseLandmark.LEFT_EYE.value].y
        angle = self.calculate_angle(self.left_shoulder,self.left_elbow,self.left_wrist)
        self.last_left_angle = angle
        
        if angle >= self.PUSH_ANGLE and self.left_wrist[1] < left_eye_y:
            return True
        return False

    
    def check_right_arm(self,landmarks):
        '''
            오른쪽 팔 위로 올렸는지 체크
            Return
                오른쪽손목 y좌표가 오른쪽눈 y좌표 위에위치하고 팔 각도가 160 이상이면 True 아니면 False
        '''
        right_eye_y = landmarks[mp_pose.PoseLandmark.RIGHT_EYE.value].y
        angle = self.calculate_angle(self.right_shoulder,self.right_elbow,self.right_wrist)
        self.last_right_angle = angle

        if angle >= self.PUSH_ANGLE and self.right_wrist[1] < right_eye_y:
            return True
        return False

    def check_right_arm_pulldown(self, landmarks):
        '''
            오른쪽 팔 끌어내렸는지 체크
            Return
                오른쪽손목 y좌표가 오른쪽입 y좌표 아래에 위치하고 팔각도가 70이하면 True 아니면 False
        '''

        mouth_right_y = landmarks[mp_pose.PoseLandmark.MOUTH_RIGHT.value].y
        angle = self.calculate_angle(self.right_shoulder,self.right_elbow,self.right_wrist)

        if angle <= self.PULL_ANGLE and mouth_right_y <= self.right_wrist[1]:
            return True
        
        return False


    def check_left_arm_pulldown(self, landmarks):
        '''
            오른쪽 팔 끌어내렸는지 체크
            Return
                왼쪽손목 y좌표가 왼쪽입 y좌표 아래에 위치하고 팔각도가 70이하면 True 아니면 False
        '''

        mouth_left_y = landmarks[mp_pose.PoseLandmark.MOUTH_LEFT.value].y
        angle = self.calculate_angle(self.left_shoulder,self.left_elbow,self.left_wrist)
        #print("right_leftdown: ",angle)

        if angle <= self.PULL_ANGLE and mouth_left_y <= self.left_wrist[1]:
            return True
        
        return False
    

# class HeartRateConsumer(WebsocketConsumer):
#     """
#     얼굴을 기반으로 심박수를 측정하는 이미지 처리를 위한 소켓
#     """
#     def connect(self):
#         print("심박수 이미지 처리 서버 연결")
#         self.accept()

#     def disconnect(self, close_code):
#         print("심박수 이미지 처리 소켓 해제")
    
#     def receive(self, bytes_data):
#         """
#         bytes_data : 비트맵 이미지 bytes array
#         """
#         try:
#             bitmap_to_image = Image.open(io.BytesIO(bytes_data))
#             image_array = np.asarray(bitmap_to_image)
#             frame, face_frame, ROI1, ROI2, status, mask = hr.face_detect(image_array)
#             bpm = hr.run(frame, face_frame, ROI1, ROI2, status, mask)
#             bpm = 0 if bpm is None else round(bpm)
#             self.send(text_data=json.dumps({
#                 'bpm' : bpm,
#             }))
#         except Exception as err:
#             print(err)

class HeartRateConsumer(WebsocketConsumer):
    """
    핏기기앱으로부터 심박수를 받아서 앱에 전송하기 위한 소켓
    """
    def connect(self):
        print("심박수 소켓 서버 연결")

        self.group_name = "1"
        
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.last_heartrate = 80

        self.accept()

    def disconnect(self, close_code):
        print("심박수 소켓 서버 해제")
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    
    def receive(self,text_data=None):
        '''
            핏빗에서 심박수 받아서 모바일에 전송
            Args
                text_data 
                    ex){
                        "heartRate": "90",
                        "timestamp": "2022-01-02T12:46:28.209Z"
                    }
        '''
        print(text_data)
        
        if self.last_heartrate > 200:
            self.last_heartrate = 85
        self.last_heartrate += 1
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'send_heart_rate',
                'bpm': self.last_heartrate
            }
        )

        # text_data_json = json.loads(text_data)
        # try:
        #     # bpm = int(text_data_json.get('heartRate'))
        #     bpm = text_data
        #     async_to_sync(self.channel_layer.group_send)(
        #         self.group_name,
        #         {
        #             'type': 'send_heart_rate',
        #             'bpm': bpm
        #         }
        #     )
        # except ValueError:
        #     pass

    def send_heart_rate(self, event):
        bpm = event['bpm']
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'bpm': bpm
        }))

class RevitalizationIsometricChestpressConsumer(AsyncWebsocketConsumer):
    """
    재활운동 - 등척성 운동 - 체스트프레스에 연결되는 소켓
    """
    async def connect(self):
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        self.client_datas = 0
        self.left_check_var = 0
        self.right_check_var = 0
        self.use_skeleton = True
        self.exercise_status = True # 운동 상태

        self.right_shoulder = None
        self.right_elbow    = None
        self.right_wrist    = None
        self.right_hip      = None

        self.left_shoulder  = None
        self.left_elbow     = None
        self.left_wrist     = None
        self.left_hip       = None

        self.PUSH_ELBOW_ANGLE = 120
        self.PUSH_SHOULDER_ANGLE_A = 45
        self.PUSH_SHOULDER_ANGLE_B = 120

        self.PULL_ELBOW_ANGLE = 70
        self.PULL_SHOULDER_ANGLE_A = 35
        self.PULL_SHOULDER_ANGLE_B = 90
        #양팔 앞으로 밀면 True, 아니면 False
        self.push_status = True    

        await self.accept()
        print('체스트 프레스 컨슈머 연결 수립 완료')

    async def disconnect(self, close_code):
        print(close_code)
        print('연결 해제')

    async def receive(self, text_data=None, bytes_data=None):
        start = time.time()
        # not bytes data 처리
        if not bytes_data:
            text_data_json = json.loads(text_data)
            action = text_data_json.get("action") # send 시 액션을 넘겨줘야 함.

            if action == "skeleton":
                self.use_skeleton = text_data_json.get("use_skeleton")

            elif action == "set_user":
                self.uuid = text_data_json.get("uuid")
                self.user_height = text_data_json.get("user_height")
                self.user_weight = text_data_json.get("user_weight")
                self.user_age = text_data_json.get("user_age")
                self.user_sex = text_data_json.get("user_sex")
                self.user_name = text_data_json.get("user_name")
                self.user_handicapped_type = text_data_json.get("user_handicapped_type")
                print(self.user_name, self.user_handicapped_type, self.user_age, self.user_sex)
            elif action == "exercise_finish":
                print("운동 종료", text_data_json)
                self.running_time = text_data_json.get("running_time")
                exercise_status = False # 운동 상태를 False로 처리하여 체크함
                await self.save_exercise_log()

            return

        bitmap_to_image = Image.open(io.BytesIO(bytes_data)) # 안드로이드에서 넘겨온 이미지 ByteArray를 이미지로 처리함.
        image_array = np.asarray(bitmap_to_image) # ByteArray를 이미지로 처리한 결과를 np.array로 변경함

        image = image_array
        image = cv2.flip(image, 1)
        image.flags.writeable = False
        results = self.pose.process(image)

        # 랫 풀 다운
        try:  
            landmarks = results.pose_landmarks.landmark

            self.right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            self.right_elbow    = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            self.right_wrist    = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
            self.right_hip      = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]

            self.left_shoulder  = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            self.left_elbow     = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            self.left_wrist     = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            self.left_hip       = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]


            if self.check_push_left_arm() and self.check_push_right_arm():
                self.push_status = True

            if self.push_status == True and self.check_pull_left_arm() and self.check_pull_right_arm():
                self.client_datas += 1
                self.push_status = False


        except Exception as e:
            print(e)

        if self.use_skeleton:
            # 스켈레톤 활성화 시에만 스켈레톤을 그림.
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        processed_image = image_to_bytearray(image)

        # print('처리 시간: ', time.time() - start)
        await self.send(bytes_data=processed_image)    
        await self.send(text_data=json.dumps({
            'proceesing_time' : int((time.time() - start) * 1000),
            'count' : self.client_datas,
        }))

    def calculate_angle(self, a, b, c):
        a = np.array(a) # First
        b = np.array(b) # Mid
        c = np.array(c) # End
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle >180.0:
            angle = 360-angle
            
        return angle

    def check_push_right_arm(self):
        '''
            오른쪽 팔 밀었는지 체크
            Return
                오른쪽팔꿈치 각도가 120도 이상이고 오른쪽어깨 각도가 45 <= x <= 120 이면 True, 아니면 False
        '''

        right_elbow_angle    = self.calculate_angle(self.right_shoulder,self.right_elbow,self.right_wrist)
        right_shoulder_angle = self.calculate_angle(self.right_elbow,self.right_shoulder,self.right_hip)
        

        if right_elbow_angle >= self.PUSH_ELBOW_ANGLE and right_shoulder_angle >= self.PUSH_SHOULDER_ANGLE_A and right_shoulder_angle <=self.PUSH_SHOULDER_ANGLE_B:
            return True
        
        return False    
    
    def check_push_left_arm(self):
        '''
            왼쪽 팔 밀었는 체크
            Return
                왼쪽팔꿈치 각도가 120도 이상이고 왼쪽어깨 각도가 45 <= x <= 120 이면 True, 아니면 False
        '''
        left_elbow_angle    = self.calculate_angle(self.left_shoulder,self.left_elbow,self.left_wrist)
        left_shoulder_angle = self.calculate_angle(self.left_elbow,self.left_shoulder,self.left_hip)

        if left_elbow_angle >= self.PUSH_ELBOW_ANGLE and left_shoulder_angle >= self.PUSH_SHOULDER_ANGLE_A and left_shoulder_angle <=self.PUSH_SHOULDER_ANGLE_B:
            return True
        
        return False
    
    def check_pull_right_arm(self):
        '''
            오른쪽 팔 당겼는지 체크 
            Return
                오른쪽 팔꿈치 각도가 70도 이하고 오른쪽어깨 각도가 35 <= x <= 90 이면 True, 아니면 False

        '''
        right_elbow_angle    = self.calculate_angle(self.right_shoulder,self.right_elbow,self.right_wrist)
        right_shoulder_angle = self.calculate_angle(self.right_elbow,self.right_shoulder,self.right_hip)
        

        if right_elbow_angle <= self.PULL_ELBOW_ANGLE and right_shoulder_angle >= self.PULL_SHOULDER_ANGLE_A and right_shoulder_angle <= self.PULL_SHOULDER_ANGLE_B:
            return True
        
        return False    
    
    def check_pull_left_arm(self):
        '''
            왼쪽 팔 당겼는지 체크 
            Return
                왼쪽 팔꿈치 각도가 70도 이하고 왼쪽쪽어깨 각도가 35 <= x <= 90 이면 True, 아니면 False

        '''
        left_elbow_angle    = self.calculate_angle(self.left_shoulder,self.left_elbow,self.left_wrist)
        left_shoulder_angle = self.calculate_angle(self.left_elbow,self.left_shoulder,self.left_hip)

        if left_elbow_angle <= self.PULL_ELBOW_ANGLE and left_shoulder_angle >= self.PULL_SHOULDER_ANGLE_A and left_shoulder_angle <= self.PULL_SHOULDER_ANGLE_B:
            return True
        
        return False  

    @database_sync_to_async
    def save_exercise_log(self):
        try:
            log = ExerciseLog.objects.create(
                uuid = self.uuid,
                user_sex=self.user_sex,
                user_age=self.user_age,
                user_height=self.user_height,
                user_weight=self.user_weight,
                exercise_type="Chestpress",
                count=self.client_datas,
                running_time=self.running_time,
            )
        except Exception as err:
            print(err)  
    
class RevitalizationIsometricLatPulldownConsumer(AsyncWebsocketConsumer):
    """
    재활운동 - 등척성 운동 - 랫 풀 다운에 연결되는 소켓
    """
    async def connect(self):
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        self.client_datas = 0
        self.use_skeleton = True
        self.exercise_status = True # 운동 상태

        # 운동 체크 변수
        self.right_shoulder = None
        self.right_elbow    = None
        self.right_wrist    = None

        self.left_shoulder  = None
        self.left_elbow     = None
        self.left_wrist     = None
        
        self.PUSH_ANGLE = 150
        self.PULL_ANGLE = 70
        self.up_status = False
        self.left_check = False
        self.right_check = False
        self.last_left_angle = None
        self.last_right_angle = None

        # 각도 기록
        self.last_elbow_left_angles = []
        self.last_elbow_right_angles = []
        self.last_shoulder_left_angles = []
        self.last_shoulder_right_angles = []

        self.is_start = False # 시작 상태 플래그
        self.is_finish = False # 종료 상태 플래그
        self.second = None
        self.count = None
        
        self.strengh_values = {}
        self.position_flag = None # 최대점 측정 [0], 중간점 측정 [1], 최저점 측정 [2] 
        self.now_count = -1  # 현재 카운트
        self.now_step = 0

        await self.accept()
        print('연결 수립 완료')

    async def disconnect(self, close_code):
        print(close_code)
        print('연결 해제')

    async def receive(self, text_data=None, bytes_data=None):
        start = time.time()
        # not bytes data 처리
        if not bytes_data:
            text_data_json = json.loads(text_data)
            action = text_data_json.get("action") # send 시 액션을 넘겨줘야 함.

            if action == "skeleton":
                self.use_skeleton = text_data_json.get("use_skeleton")
            elif action == "set_user":
                self.uuid = text_data_json.get("uuid")
                self.user_height = text_data_json.get("user_height")
                self.user_weight = text_data_json.get("user_weight")
                self.user_age = text_data_json.get("user_age")
                self.user_sex = text_data_json.get("user_sex")
                self.second = text_data_json.get("second")
                self.count = text_data_json.get("count") # 세트수
                self.now_count = self.count # (추가)
                # 세트 별 측정 + 최대·중간·최저점별 측정
                self.strengh_values = {
                    0 : [ [] for i in range(int(self.count))],
                    1 : [ [] for i in range(int(self.count))],
                    2 : [ [] for i in range(int(self.count))]
                }
                print(self.strengh_values)
            elif action == "start":
                self.is_start = True
                self.is_finish = False
                self.position_flag = text_data_json.get("flag")
                print("start:", self.position_flag)
            elif action == "count_down":
                # 초 단위가 지나갈 경우 -> 3초에 한 번씩 인터벌이 깎일 때
                count = text_data_json.get('count')
                self.now_count = count

                if count == 0:
                    print("운동 종료")
                    self.is_finish = True # 운동 종료 처리
                    await self.save_user_strengh(self.position_flag) # 최대 근력 DB 저장
                    print(self.now_step, '운동 종료 단계 처리')
                    await self.send(text_data=json.dumps({
                        'count' : self.client_datas,
                        'is_finish' : self.is_finish,
                        "step" : self.now_step,
                        'last_right_angle' : self.last_right_angle,
                        'last_left_angle' : self.last_left_angle,
                        'proceesing_time' :  int((time.time() - start) * 1000),
                    }))    

            elif action == "exercise_finish":
                print("운동 종료", text_data_json)
                self.running_time = text_data_json.get("running_time")
                exercise_status = False # 운동 상태를 False로 처리하여 체크함
                await self.save_exercise_log()
            elif action == "sensor":
                # 센서값 발생
                _type = text_data_json.get("type") 
                value = text_data_json.get("value") 
                if self.is_start and self.now_count > -1:
                    # self.strengh_values[self.flag]
                    try:
                        self.strengh_values[self.position_flag][self.now_count-1].append(value)
                    except Exception as err:
                        print(err) 

            return

        bitmap_to_image = Image.open(io.BytesIO(bytes_data)) # 안드로이드에서 넘겨온 이미지 ByteArray를 이미지로 처리함.
        image_array = np.asarray(bitmap_to_image) # ByteArray를 이미지로 처리한 결과를 np.array로 변경함

        image = image_array
        image = cv2.flip(image, 1)
        image.flags.writeable = False
        results = self.pose.process(image)

        # 랫 풀 다운
        if not self.is_finish and self.is_start: 
            try:  
                landmarks = results.pose_landmarks.landmark

                self.right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                self.right_elbow    = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                self.right_wrist    = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                self.right_hip      = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]

                self.left_shoulder  = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                self.left_elbow     = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                self.left_wrist     = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                self.left_hip       = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]

                self.updateLastAngle()

                if self.check_left_arm(landmarks) and self.check_right_arm(landmarks):
                    self.up_status = True

                if self.up_status == True and \
                    self.check_left_arm_pulldown(landmarks) and \
                    self.check_right_arm_pulldown(landmarks):
                    
                    self.client_datas += 1 
                    self.up_status = False

            except Exception as e:
                print(e)

            await self.send(text_data=json.dumps({
                'count' : self.client_datas,
                'proceesing_time' : int((time.time() - start) * 1000),
                "step" : self.now_step,
                'last_right_angle' : self.last_right_angle,
                'last_left_angle' : self.last_left_angle
            }))
        
        if self.use_skeleton:
            # 스켈레톤 활성화 시에만 스켈레톤을 그림.
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        processed_image = image_to_bytearray(image)

        await self.send(bytes_data=processed_image)    
        # await self.send(text_data=json.dumps({
        #     'proceesing_time' : int((time.time() - start) * 1000),
        #     'count' : self.client_datas,
        # }))

    def reset_angles(self):
        self.last_elbow_left_angles = []
        self.last_elbow_right_angles = []
        self.last_shoulder_right_angles = []
        self.last_shoulder_left_angles = []

    @database_sync_to_async
    def save_user_strengh(self, flag):
        """
        유저 근력 저장
        """
        def get_max_value(strengths):
            _max_value = 0
            for _strength in strengths:
                count_max = max(_strength) # 해당 세트의 최댓값
                if count_max > _max_value:
                    _max_value = count_max
            return _max_value

        def get_avg_value(strengths):
            _sum = 0
            _cnt = 0
            try:
                for _strength in strengths:
                    for _str in _strength:
                        _sum += _str
                        _cnt += 1
                return round(_sum /_cnt, 2)
            except Exception as err:
                print(err)
                return 0

        print("운동 종료", self.strengh_values)
        user = UserInfomation.objects.filter(uuid=self.uuid)
        if flag == 0:
            strengths = self.strengh_values[0]
            if strengths:
                user.update(revital_latpulldown_maxium_strengh=get_avg_value(strengths))
                print("최대점 측정 완료")
            # 최대점 평균 각도 저장
            user.update(
                revital_latpulldown_max_position_last_elbow_left_angle=np.mean(self.last_elbow_left_angles),
                revital_latpulldown_max_position_last_elbow_right_angle=np.mean(self.last_elbow_right_angles),
                revital_latpulldown_max_position_last_shoulder_right_angle=np.mean(self.last_shoulder_right_angles),
                revital_latpulldown_max_position_last_shoulder_left_angle=np.mean(self.last_shoulder_left_angles),
            )
            self.reset_angles()
            self.now_step = '1' 
                    
        elif flag == 1:
            strengths = self.strengh_values[1]
            if strengths:
                user.update(revital_latpulldown_minium_strengh=get_avg_value(strengths))
                print("중간점 측정 완료")
            # 중간점 평균 각도 저장
            user.update(
                revital_latpulldown_mid_position_last_elbow_left_angle=np.mean(self.last_elbow_left_angles),
                revital_latpulldown_mid_position_last_elbow_right_angle=np.mean(self.last_elbow_right_angles),
                revital_latpulldown_mid_position_last_shoulder_right_angle=np.mean(self.last_shoulder_right_angles),
                revital_latpulldown_mid_position_last_shoulder_left_angle=np.mean(self.last_shoulder_left_angles),
            )
            self.reset_angles()
            self.now_step = '2'


        elif flag == 2:
            strengths = self.strengh_values[2]
            if strengths:
                user.update(revital_latpulldown_midium_strengh=get_avg_value(strengths))
                print("최저점 측정 완료")
            # 최저점 평균 각도 저장
            user.update(
                revital_latpulldown_min_position_last_elbow_left_angle=np.mean(self.last_elbow_left_angles),
                revital_latpulldown_min_position_last_elbow_right_angle=np.mean(self.last_elbow_right_angles),
                revital_latpulldown_min_position_last_shoulder_right_angle=np.mean(self.last_shoulder_right_angles),
                revital_latpulldown_min_position_last_shoulder_left_angle=np.mean(self.last_shoulder_left_angles),
            )
            user.update(revital_latpulldown_strength_logs=json.dumps(self.strengh_values)) # 종료 시점에 로그 저장
            self.reset_angles()
            self.now_step = '3' # 측정 종료
    
    def updateLastAngle(self):
        self.last_elbow_left_angle = self.calculate_angle(self.left_shoulder,self.left_elbow,self.left_wrist)
        self.last_elbow_right_angle = self.calculate_angle(self.right_shoulder,self.right_elbow,self.right_wrist)
        self.last_shoulder_right_angle = self.calculate_angle(self.right_elbow,self.right_shoulder,self.right_hip)
        self.last_shoulder_left_angle = self.calculate_angle(self.left_elbow,self.left_shoulder,self.left_hip)

        # 각도 저장
        self.last_elbow_left_angles.append(self.last_elbow_left_angle)
        self.last_elbow_right_angles.append(self.last_elbow_right_angle)
        self.last_shoulder_right_angles.append(self.last_shoulder_right_angle)
        self.last_shoulder_left_angles.append(self.last_shoulder_left_angle)



    def calculate_angle(self, a, b, c):
        a = np.array(a) # First
        b = np.array(b) # Mid
        c = np.array(c) # End
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle >180.0:
            angle = 360-angle
            
        return angle


    def check_left_arm(self, landmarks):
        '''
            왼쪽팔 위로 올렸는지 체크하기
            Return
                왼쪽손목 y좌표가 외쪽눈 y좌표 위에위치하고 팔 각도가 160 이상이면 True 아니면 False
        '''

        left_eye_y = landmarks[mp_pose.PoseLandmark.LEFT_EYE.value].y
        angle = self.calculate_angle(self.left_shoulder,self.left_elbow,self.left_wrist)
        self.last_left_angle = angle

        if angle >= self.PUSH_ANGLE and self.left_wrist[1] < left_eye_y:
            return True
        return False

    
    def check_right_arm(self,landmarks):
        '''
            오른쪽 팔 위로 올렸는지 체크
            Return
                오른쪽손목 y좌표가 오른쪽눈 y좌표 위에위치하고 팔 각도가 160 이상이면 True 아니면 False
        '''

        right_eye_y = landmarks[mp_pose.PoseLandmark.RIGHT_EYE.value].y
        angle = self.calculate_angle(self.right_shoulder,self.right_elbow,self.right_wrist)
        self.last_right_angle = angle

        if angle >= self.PUSH_ANGLE and self.right_wrist[1] < right_eye_y:
            return True
        return False

    def check_right_arm_pulldown(self, landmarks):
        '''
            오른쪽 팔 끌어내렸는지 체크
            Return
                오른쪽손목 y좌표가 오른쪽입 y좌표 아래에 위치하고 팔각도가 70이하면 True 아니면 False
        '''

        mouth_right_y = landmarks[mp_pose.PoseLandmark.MOUTH_RIGHT.value].y
        angle = self.calculate_angle(self.right_shoulder,self.right_elbow,self.right_wrist)

        if angle <= self.PULL_ANGLE and mouth_right_y <= self.right_wrist[1]:
            return True
        
        return False


    def check_left_arm_pulldown(self, landmarks):
        '''
            오른쪽 팔 끌어내렸는지 체크
            Return
                왼쪽손목 y좌표가 왼쪽입 y좌표 아래에 위치하고 팔각도가 70이하면 True 아니면 False
        '''

        mouth_left_y = landmarks[mp_pose.PoseLandmark.MOUTH_LEFT.value].y
        angle = self.calculate_angle(self.left_shoulder,self.left_elbow,self.left_wrist)
        #print("right_leftdown: ",angle)

        if angle <= self.PULL_ANGLE and mouth_left_y <= self.left_wrist[1]:
            return True
        
        return False

    @database_sync_to_async
    def save_exercise_log(self):
        try:
            log = ExerciseLog.objects.create(
                uuid = self.uuid,
                user_sex=self.user_sex,
                user_age=self.user_age,
                user_height=self.user_height,
                user_weight=self.user_weight,
                exercise_type="LatPullDown",
                count=self.client_datas,
                running_time=self.running_time,
            )
        except Exception as err:
            print(err)
        
class PoseEstimationConsumer(WebsocketConsumer):
    # holistic = mp_holistic.Holistic(
    #     min_detection_confidence=0.5,
    #     min_tracking_confidence=0.5
    # )

    def connect(self): 
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        self.client_datas = 0
        self.left_check_var = 0
        self.right_check_var = 0
        self.accept()
        print('연결 수립 완료')

    def disconnect(self, close_code):
        print('연결 해제')

    def receive(self, text_data=None, bytes_data=None):
        # text_data_json = json.loads(text_data)
        start = time.time()
        if not bytes_data:
            print(text_data, start)
            return
    
        bitmap_to_image = Image.open(io.BytesIO(bytes_data)) # 안드로이드에서 넘겨온 이미지 ByteArray를 이미지로 처리함.
        image_array = np.asarray(bitmap_to_image) # ByteArray를 이미지로 처리한 결과를 np.array로 변경함

        image = image_array
        image = cv2.flip(image, 1)
        image.flags.writeable = False
        results = self.pose.process(image)

        # 랫 풀 다운
        try:  
            landmarks = results.pose_landmarks.landmark

            LEFT_SHOULDER = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            LEFT_ELBOW = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            LEFT_WRIST = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

            RIGHT_SHOULDER = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            RIGHT_ELBOW = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            RIGHT_WRIST = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
 
            RIGHT_ELBOW_angle = self.calculate_angle(RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST)  
            LEFT_ELBOW_angle = self.calculate_angle(LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST)    

            if LEFT_ELBOW_angle >= 150 and RIGHT_ELBOW_angle >= 150:
                self.right_check_var = 1

            if self.right_check_var == 1 and LEFT_ELBOW_angle < 90 and RIGHT_ELBOW_angle < 90:
                self.client_datas += 1
                self.right_check_var = 0
                self.send(text_data=json.dumps({
                    'count' : self.client_datas,
                }))


        except Exception as e:
            print(e)

        mp_drawing.draw_landmarks(
            image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        
        processed_image = image_to_bytearray(image)
        # print('처리 시간: ', time.time() - start)

        self.send(bytes_data=processed_image)    

    def calculate_angle(self, a, b, c):
        a = np.array(a) # First
        b = np.array(b) # Mid
        c = np.array(c) # End
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle >180.0:
            angle = 360-angle
            
        return angle

class ROMElbowConsumer(AsyncWebsocketConsumer):
    '''
        팔꿈치 굴곡/신전 Consumer
    '''
    async def connect(self):
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)

        self.ARM_FLEXTION = "flextion"
        self.ARM_EXTENSION = "extension"
        self.left_angle = 0
        self.right_angle = 0
        
        self.each_step_data_dict = {}
        self.is_clicked_step_arr = []

        self.right_elbow_max_angle = 0
        self.right_elbow_min_angle = 0
        self.left_elbow_max_angle = 0
        self.left_elbow_min_angle = 0

        self.pre_time_sec = None # 이전 시간(초)
        self.uuid = None
        self.completion = False

        self.is_start = False # 시작 상태 플래그
        self.is_finish = False # 종료 상태 플래그

        self.rom = ROMMeasurement()

        # 기준 각도
        self.standard_angle = None
        
        await self.accept()
        print("팔꿈치 연결")


    async def disconnect(self, close_code):
        print('팔꿈치 연결 해제')
        
    async def receive(self, text_data=None, bytes_data=None):
        # print("data")
        context = {}


        if not bytes_data:
            text_data_json = json.loads(text_data,strict=False)
            if text_data_json.get('stepData'): #1차, 2차, 3차 측정관련데이터가 있으면
                step_data = text_data_json.get('stepData')
                # step_image,right_angle,left_angle = self.process_skeleton_from_base64(step_data) #base스켈레톤 및 각도 그리기
                # for flip
                step_image,left_angle,right_angle = self.process_skeleton_from_base64(step_data) #base스켈레톤 및 각도 그리기
                # 주석 처리 (각도 변경)
                # left_angle = 180 - left_angle
                # right_angle = 180 - right_angle

                # 기준 각도 - 측정 각도
                if self.standard_angle:
                    left_angle = self.standard_angle - left_angle
                    right_angle = self.standard_angle - right_angle

                print(f"{step_data.get('stepNumber')}")
                print("left: ",left_angle)
                print("right: ",right_angle)
                await self.send(text_data=json.dumps({
                    'left_angle': left_angle,
                    'right_angle':right_angle,
                    'completion': self.completion,
                    'step_data': { 
                        "stepNumber":step_data.get('stepNumber'),
                        "base64Image": base64.b64encode(image_to_bytearray(step_image)).decode('utf-8')   
                    }
                    
                }))
                return 

            action = text_data_json.get("action") # send 시 액션을 넘겨줘야 함.

            
            if action == 'intialize':
                #팔꿈치 굴곡/신전
                #굴곡: flextion, 신전: extension
                self.elbow_rom_type = text_data_json.get('elbow_rom_type')

                #arm : left면 왼쪽팔각도 측정
                #arm : right면 오른쪽팔각도 측정
                self.arm  = text_data_json.get('arm') 
                self.arm = 'right' if self.arm == 'left' else 'left'
                self.uuid = text_data_json.get('uuid')
            elif action == 'start':
                self.is_start = True
                
            elif action == 'finish':
                self.is_start = False
                self.is_finish = True

                await self.send(text_data=json.dumps({
                        'right_angle': self.right_angle,
                        'left_angle': self.left_angle,
                        'completion' : True,    
                    })) 

            elif action == "standard_picture":
                direction = text_data_json.get('direction')
                self.standard_angle = self.right_angle if self.arm == 'right' else self.left_angle
                
                await self.send(text_data=json.dumps({
                    'standard_angle' : self.standard_angle
                }))
                
                
            return

        else:
            bitmap_to_image = Image.open(io.BytesIO(bytes_data)) # 안드로이드에서 넘겨온 이미지 ByteArray를 이미지로 처리함.
            image = np.asarray(bitmap_to_image) #nparray변환
            
            image.flags.writeable = False
            
            results = self.pose.process(image)
            if self.is_start:
                self.right_angle,self.left_angle = self.rom.measure_rom(action="elbow",image=image) 
                # for flip
                # self.left_angle,self.right_angle = self.rom.measure_rom(action="elbow",image=image) 

                
                # 23. 04. 18 주석 처리 (각도 변경)
                # self.right_angle = 180 - self.right_angle
                # self.left_angle = 180 - self.left_angle
                
                image = self._draw_angle(image,self.left_angle,self.right_angle)
                    
                
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            processed_image = image_to_bytearray(image)
            await self.send(bytes_data=processed_image)  

            await self.send(text_data=json.dumps({
                    'right_angle': self.right_angle,
                    'left_angle': self.left_angle,
                    'completion' : self.completion,    
                }))
    
    def process_skeleton_from_base64(self,step_data):
        '''
          base64 이미지를 nparray로변환해서 스켈레톤 그리기
        '''
        
        image_pil = Image.open(io.BytesIO(base64.b64decode(step_data.get('base64Image'))))
        image = np.array(image_pil)

        right_angle, left_angle = self.rom.measure_rom(action="elbow",image=image)
        mp_drawing.draw_landmarks(
            image, self.rom.results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        image = self._draw_angle(image,left_angle,right_angle)
        return image,right_angle,left_angle

    def _draw_angle(self,image,left_angle,right_angle):
        ''' 
            nparray image를 인자로 받아서 팔꿈치 굴곡/신전 그리기
        '''
        h,w,c = image.shape
        if self.arm == "left":
            #
            #왼쪽팔꿈치 굴곡/신전 각도 그리기
            #
            x1 = (int(self.rom.left_elbow[0]*w) + int(self.rom.left_wrist[0]*w)) //2
            y1 = (int(self.rom.left_elbow[1]*h) + int(self.rom.left_wrist[1]*h)) //2
            x2 = (int(self.rom.left_elbow[0]*w) + int(self.rom.left_shoulder[0]*w)) //2
            y2 = (int(self.rom.left_elbow[1]*h) + int(self.rom.left_shoulder[1]*h)) //2

            image = draw_angle(
                        img = image,
                        position = [x1,y1,x2,y2],
                        degree=int(left_angle),
                        action="elbow_flextion_extension",
                        sortation="left",
                    )
        elif self.arm == "right":
            #
            #오른쪽팔꿈치 굴곡/신전 각도 그리기
            #
            x1 = (int(self.rom.right_elbow[0]*w) + int(self.rom.right_wrist[0]*w)) //2
            y1 = (int(self.rom.right_elbow[1]*h) + int(self.rom.right_wrist[1]*h)) //2
            x2 = (int(self.rom.right_elbow[0]*w) + int(self.rom.right_shoulder[0]*w)) //2
            y2 = (int(self.rom.right_elbow[1]*h) + int(self.rom.right_shoulder[1]*h)) //2

            image = draw_angle(
                        img = image,
                        position = [x1,y1,x2,y2],
                        degree=int(right_angle),
                        action="elbow_flextion_extension",
                        sortation="right",
                    )
        return image

class ROMShoulder1Consumer(AsyncWebsocketConsumer):
    '''
        어깨외전/내전
    '''
    async def connect(self):
        self.SHOURDER_ABDUCTION = "abduction"
        self.SHOURDER_ADDUCTION = "adduction"
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)


        self.left_angle = 0
        self.right_angle = 0
        
        self.each_step_data_dict = {}
        self.is_clicked_step_arr = []


        self.right_shoulder1_max_angle = 0
        self.left_shoulder1_max_angle = 0
        self.right_shoulder1_min_angle = 0
        self.left_shoulder1_min_angle = 0

        self.pre_time_sec = None # 이전 시간(초)
        self.uuid = None
        self.completion = False #3초지나면 True 

        self.is_start = False # 시작 상태 플래그
        self.is_finish = False # 종료 상태 플래그


        self.rom = ROMMeasurement()
        
        await self.accept()
        print("어깨(외전/내전) 연결")

    async def disconnect(self, close_code):
        print("어깨(외전/내전) 연결 해제")

    
    async def receive(self, text_data=None, bytes_data=None):
        context = {}

        if not bytes_data:
            
            text_data_json = json.loads(text_data,strict=False)
            if text_data_json.get('stepData'): #1차, 2차, 3차 측정관련데이터가 있으면
                step_data = text_data_json.get('stepData')
                # step_image,right_angle,left_angle = self.process_skeleton_from_base64(step_data) #base스켈레톤 및 각도 그리기
                # change right and left angle for flip
                step_image,left_angle,right_angle = self.process_skeleton_from_base64(step_data) #base스켈레톤 및 각도 그리기
                
                print(f"{step_data.get('stepNumber')}차")
                print("left: ",left_angle)
                print("right: ",right_angle)
                # print(base64.b64encode(image_to_bytearray(step_image)).decode('utf-8'))
                await self.send(text_data=json.dumps({
                    'left_angle': left_angle,
                    'right_angle':right_angle,
                    'completion': self.completion,
                    'step_data': { 
                        "stepNumber":step_data.get('stepNumber'),
                        "base64Image": base64.b64encode(image_to_bytearray(step_image)).decode('utf-8')   
                    }
                    
                }))
                return 
                
            
            action = text_data_json.get("action") # send 시 액션을 넘겨줘야 함.

            if action == 'intialize':
                #어깨 외전/내전
                #외전: abduction, 내전: adduction
                self.shoulder_rom_type = text_data_json.get('shoulder_rom_type')
                self.uuid = text_data_json.get('uuid')
                #오른쪽 왼쪽
                self.shoulder =  text_data_json.get('shoulder')
                # change left and right for flip
                self.shoulder = 'right' if self.shoulder == 'left' else 'left'
            elif action == 'start':
                self.is_start = True
            elif action == 'finish':
                self.is_start = False
                self.is_finish = True

                await self.send(text_data=json.dumps({
                        'left_angle': self.left_angle,
                        'right_angle': self.right_angle,
                        'completion' : True,

                    }))
                
            return

        else: #안드로이드에서 전송된 bytes이미지가 있으면

            bitmap_to_image = Image.open(io.BytesIO(bytes_data)) # 안드로이드에서 넘겨온 이미지 ByteArray를 이미지로 처리함.
            image = np.asarray(bitmap_to_image) #nparray변환
            
            image.flags.writeable = False
            results = self.pose.process(image)


            # 가동범위 측정
            if self.is_start:
                self.right_angle, self.left_angle = self.rom.measure_rom(action="shoulder",image=image)
                image = self._draw_angle(image,self.left_angle,self.right_angle)


            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            
            processed_image = image_to_bytearray(image)
            
            
            await self.send(bytes_data=processed_image)  
            await self.send(text_data=json.dumps({
                    'left_angle': self.left_angle,
                    'right_angle': self.right_angle,
                    'completion': self.completion,
            }))
    
    def process_skeleton_from_base64(self,step_data):
        
        image_pil = Image.open(io.BytesIO(base64.b64decode(step_data.get('base64Image'))))
        image = np.array(image_pil)

        right_angle, left_angle = self.rom.measure_rom(action="shoulder",image=image)
        mp_drawing.draw_landmarks(
            image, self.rom.results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        image = self._draw_angle(image,left_angle,right_angle)
        return image,right_angle,left_angle

    def _draw_angle(self,image,left_angle,right_angle):
        ''' 
            nparray image를 인자로 받아서 어깨 외전/내전각도 그리기
        '''
        h,w,c = image.shape
        if self.shoulder == "left":
            #
            #왼쪽어깨 외전/내전 각도 그리기
            #
            lx1 = (int(self.rom.left_shoulder[0]*w) + int(self.rom.left_elbow[0]*w)) //2
            ly1 = (int(self.rom.left_elbow[1]*h) + int(self.rom.left_shoulder[1]*h)) //2

            lx2 = (int(self.rom.left_hip[0]*w) + int(self.rom.left_shoulder[0]*w)) //2
            ly2 = (int(self.rom.left_shoulder[1]*h) + int(self.rom.left_hip[1]*h)) //2

            image = draw_angle(
                image,
                position = [lx1,ly1,lx2,ly2],
                degree=int(left_angle),
                action="shoulder_abduction_adduction",
                sortation="left",
            )
        if self.shoulder == "right":
            #
            #오른쪽어깨 외전/내전 각도 그리기
            #
            rx1 = (int(self.rom.right_shoulder[0]*w) + int(self.rom.right_elbow[0]*w)) //2
            ry1 = (int(self.rom.right_elbow[1]*h) + int(self.rom.right_shoulder[1]*h)) //2

            rx2 = (int(self.rom.right_hip[0]*w) + int(self.rom.right_shoulder[0]*w)) //2
            ry2 = (int(self.rom.right_shoulder[1]*h) + int(self.rom.right_hip[1]*h)) //2

            image = draw_angle(
                image,
                position = [rx1,ry1,rx2,ry2],
                degree=int(right_angle),
                action="shoulder_abduction_adduction",
                sortation="right",
            )
        return image

class ROMShoulder2Consumer(AsyncWebsocketConsumer):
    '''
        어깨 굴곡/신전
    '''
    async def connect(self):
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)

        self.SHOULDER_ROM_FLEXTION = "flextion" #굴곡
        self.SHOULDER_ROM_EXTENSION = "extension" #신전

        self.left_angle = 0
        self.right_angle = 0
        

        self.right_shoulder2_angle_list = [] 
        self.left_shoulder2_angle_list = []
        self.right_shoulder2_max_angle = 0
        self.left_shoulder2_max_angle= 0

        self.pre_time_sec = None # 이전 시간(초)
        self.uuid = None
        self.completion = False #3초지나면 True 

        self.is_start = False # 시작 상태 플래그
        self.is_finish = False # 종료 상태 플래그

        self.rom = ROMMeasurement()

        self.standard_angle = None
        self.shoulder_x = 0
        self.shoulder_y = 0

        self.image_width = 0 
        self.image_height = 0 
        
        await self.accept()
        print("어깨 굴곡/신전 연결")

    async def disconnect(self,close_code):
        print("어깨 굴곡/신전 연결 해제")

    async def receive(self, text_data=None, bytes_data=None):

        if not bytes_data:
            text_data_json = json.loads(text_data,strict=False)

            if text_data_json.get('stepData'): #1차, 2차, 3차 측정관련데이터가 있으면
                step_data = text_data_json.get('stepData')
                # step_image,right_angle,left_angle = self.process_skeleton_from_base64(step_data) #base스켈레톤 및 각도 그리기
                step_image,left_angle,right_angle = self.process_skeleton_from_base64(step_data) 

                print(left_angle, right_angle)

                left_angle = self.standard_angle + left_angle
                right_angle = self.standard_angle + right_angle
                if right_angle > 180.0:
                    right_angle = 360 - right_angle

                print("보정 후:", left_angle, right_angle)

                await self.send(text_data=json.dumps({
                    'left_angle': left_angle,
                    'right_angle':right_angle,
                    'completion': self.completion,
                    'step_data': { 
                        "stepNumber":step_data.get('stepNumber'),
                        "base64Image": base64.b64encode(image_to_bytearray(step_image)).decode('utf-8')   
                    }
                    
                }))
                return

            action = text_data_json.get("action") # send 시 액션을 넘겨줘야 함.
            if action == 'intialize':
                self.shoulder_rom_type = text_data_json.get('shoulder_rom_type')
                self.shoulder = text_data_json.get('shoulder')
                self.shoulder = 'right' if self.shoulder == 'left' else 'left'
                # print(self.shoulder_rom_type, self.shoulder)
                self.uuid = text_data_json.get('uuid')
            elif action == 'start':
                self.is_start = True
            elif action == 'finish':
                self.is_start = False
                self.is_finish = True
            
                await self.send(text_data=json.dumps({
                    'left_angle': self.left_angle,
                    'right_angle': self.right_angle,
                    'completion' : True,
                }))
            
            elif action == 'standard_picture':
                direction = self.shoulder
                print("기준 각도 촬영", direction)
                # 기준 각도 : 어깨 점 + 가상선 + 팔꿈치 점
                if direction == 'right':
                    self.standard_angle = self.calculate_angle(
                        # 팔꿈치
                        (self.rom.right_elbow[0] * self.image_width, self.rom.right_elbow[1] * self.image_height),
                        # 어깨
                        (self.shoulder_x, self.shoulder_y),
                        # 가상선 
                        self.shoulder_center_line_coordinate
                    )

                    if not self.shoulder_center_line_coordinate[0] > self.rom.right_elbow[0] * self.image_width:
                        self.standard_angle = -self.standard_angle

                else:
                    self.standard_angle = self.calculate_angle(
                        # 팔꿈치
                        (self.rom.left_elbow[0] * self.image_width, self.rom.left_elbow[1] * self.image_height),
                        # 어깨
                        (self.shoulder_x, self.shoulder_y),
                        # 가상선 
                        self.shoulder_center_line_coordinate
                    )

                    if self.shoulder_center_line_coordinate[0] > self.rom.left_elbow[0] * self.image_width:
                        self.standard_angle = -self.standard_angle
                        
                    
                print(self.standard_angle,  "기준 각도")
                await self.send(text_data=json.dumps({
                    'standard_angle' : self.standard_angle
                }))


            return
        else: ##안드로이드에서 전송된 bytes이미지가 있으면
            bitmap_to_image = Image.open(io.BytesIO(bytes_data)) # 안드로이드에서 넘겨온 이미지 ByteArray를 이미지로 처리함.
            image = np.asarray(bitmap_to_image) #nparray변환
            self.image_height, self.image_width, _ = image.shape
            image.flags.writeable = False
            results = self.pose.process(image)
            
            #가동범위 측정
            if self.is_start:
                # self.right_angle, self.left_angle = self.rom.measure_rom(action="shoulder",image=image)
                # for flip
                self.left_angle, self.right_angle = self.rom.measure_rom(action="shoulder",image=image)
                
                if self.rom.right_shoulder[0] > self.rom.right_elbow[0] and \
                        self.rom.right_shoulder[1] > self.rom.right_elbow[1]: #오른쪽어깨 굴곡 해당조건이면 180이상 각도측정
                        self.right_angle = 360 - self.right_angle
                
                if self.rom.left_shoulder[0] < self.rom.left_elbow[0] and \
                        self.rom.left_shoulder[1] > self.rom.left_elbow[1]: #왼쪽어깨 굴곡 해당조건이면 180이상 각도측정
                        self.left_angle = 360 - self.left_angle
                
                # image = self._draw_angle(image)

                # 견봉에서의 수직 선
                if results.pose_landmarks:
                    if self.shoulder == 'right': # 반대임.
                        self.shoulder_x = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * self.image_width)
                        self.shoulder_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * self.image_height)
                    else:
                        self.shoulder_x = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x * self.image_width)
                        self.shoulder_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * self.image_height)
                    self.shoulder_center_line_coordinate = (self.shoulder_x, self.shoulder_y + 400)
                    cv2.line(
                        image,
                        (self.shoulder_x, self.shoulder_y),
                        self.shoulder_center_line_coordinate,
                        (255, 0, 0), 
                        2)
                    
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            processed_image = image_to_bytearray(image)
            await self.send(bytes_data=processed_image)  
            await self.send(text_data=json.dumps({
                'left_angle': self.left_angle,
                'right_angle': self.right_angle,
                'completion': self.completion,
            }))
    
    def process_skeleton_from_base64(self,step_data):
        
        image_pil = Image.open(io.BytesIO(base64.b64decode(step_data.get('base64Image'))))
        image = np.array(image_pil)

        # right_angle, left_angle = self.rom.measure_rom(action="shoulder",image=image)
        # flip
        # left_angle, right_angle = self.rom.measure_rom(action="shoulder",image=image)
        left_angle = self.calculate_angle(
                        # 팔꿈치
                        (self.rom.right_elbow[0] * self.image_width, self.rom.right_elbow[1] * self.image_height),
                        # 어깨
                        (self.shoulder_x, self.shoulder_y),
                        # 가상선 
                        self.shoulder_center_line_coordinate
                    )
        right_angle = self.calculate_angle(
                        # 팔꿈치
                        (self.rom.left_elbow[0] * self.image_width, self.rom.left_elbow[1] * self.image_height),
                        # 어깨
                        (self.shoulder_x, self.shoulder_y),
                        # 가상선 
                        self.shoulder_center_line_coordinate
                    )
        mp_drawing.draw_landmarks(
            image, self.rom.results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        # image = self._draw_angle(image,left_angle,right_angle)

        # return image,right_angle,left_angle
        return image,left_angle,right_angle


    def _draw_angle(self,image,left_angle=None,right_angle=None):
        ''' 
            nparray image를 인자로 받아서 어깨 외전/내전각도 그리기
        '''
        left_angle = left_angle if left_angle else self.left_angle
        right_angle = right_angle if right_angle else self.right_angle
        # print(left_angle, right_angle, self.shoulder, self.shoulder_rom_type)
        h,w,c = image.shape
        if self.shoulder == "left":
            x1 = (int(self.rom.left_shoulder[0]*w) + int(self.rom.left_elbow[0]*w)) //2
            y1 = (int(self.rom.left_elbow[1]*h) + int(self.rom.left_shoulder[1]*h)) //2

            x2 = (int(self.rom.left_hip[0]*w) + int(self.rom.left_shoulder[0]*w)) //2
            y2 = (int(self.rom.left_shoulder[1]*h) + int(self.rom.left_hip[1]*h)) //2
            

        else:
            x1 = (int(self.rom.right_shoulder[0]*w) + int(self.rom.right_elbow[0]*w)) //2
            y1 = (int(self.rom.right_elbow[1]*h) + int(self.rom.right_shoulder[1]*h)) //2

            # x2 = (int(self.shoulder_center_line_coordinate[0]*w) + int(self.rom.right_shoulder[0]*w)) //2
            # y2 = (int(self.rom.right_shoulder[1]*h) + int(self.shoulder_center_line_coordinate[1]*h)) //2
            x2 = (int(self.rom.right_hip[0]*w) + int(self.rom.right_shoulder[0]*w)) //2
            y2 = (int(self.rom.right_shoulder[1]*h) + int(self.rom.right_hip[1]*h)) //2
        
        image = draw_angle(
                image,
                position = [x1,y1,x2,y2],
                # degree=int(right_angle if self.shoulder=="right" else left_angle),
                # for flip
                degree=int(right_angle if self.shoulder=="left" else left_angle),
                action=f"shoulder_{self.shoulder_rom_type}",
                sortation=self.shoulder,
            )
        return image
        
    def calculate_angle(self, a, b, c):
        a = np.array(a) # First
        b = np.array(b) # Mid
        c = np.array(c) # End
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        return angle


class NormalPoseEstimation(AsyncWebsocketConsumer):
    '''
        일반 포즈 측정
    '''
    async def connect(self):
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        await self.accept()
        print("일반 포즈 측정")

    async def disconnect(self,close_code):
        print("일반 포즈 측정 연결 해제")

    async def receive(self, text_data=None, bytes_data=None):
        bitmap_to_image = Image.open(io.BytesIO(bytes_data)) # 안드로이드에서 넘겨온 이미지 ByteArray를 이미지로 처리함.
        image = np.asarray(bitmap_to_image) #nparray변환
        
        image.flags.writeable = False
        results = self.pose.process(image)
        mp_drawing.draw_landmarks(
            image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        processed_image = image_to_bytearray(image)
        await self.send(bytes_data=processed_image)  