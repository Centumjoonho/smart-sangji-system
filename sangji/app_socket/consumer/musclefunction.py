import json
import io
import time
import pickle
import base64
import datetime
from django.http import JsonResponse
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from asgiref.sync import async_to_sync
from PIL import Image
import cv2
import numpy as np
import mediapipe as mp
from main.models import *
from app_socket.ROM import *

mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic
mp_pose = mp.solutions.pose

def image_to_bytearray(image):
    pil_im = Image.fromarray(image)
    b = io.BytesIO()
    # b = io.StringIO(s)
    pil_im.save(b, 'jpeg')
    im_bytes = b.getvalue()
    return im_bytes

def calculate_angle(a, b, c, side):
    a = np.array(a) # First
    b = np.array(b) # Mid
    c = np.array(c) # End
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)

    # if side:
    #     angle = -angle
    # if angle >180.0:
    #     angle = 360-angle
        
    return angle

class MuscleFunctionRangeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("MuscleFunctionRangeConsumer 연결 요청")
        self.start_positions_y = [] # 시작지점 데이터
        self.end_positions_y = [] # 종료지점 데이터
        self.left_angles = []
        self.right_angles = []
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        self.user_id = ""
        self.exercise_type = ""

        self.status = 0 # 0 시작, 1 종료
        await self.accept()

    async def disconnect(self,close_code):
        print("MuscleFunctionRangeConsumer 해제")

    async def receive(self, text_data=None, bytes_data=None):
        if not bytes_data:
            text_data_json = json.loads(text_data)
            action = text_data_json.get('action')
            print(text_data_json)
            if action == "init":
                self.user_id = text_data_json.get('user_id')
                self.exercise_type = text_data_json.get('exercise_type')
            elif action == "finish":
                print("완료되었습니다.")
                try:
                    start_y = np.mean(self.start_positions_y)
                    end_y = np.mean(self.end_positions_y)
                    y_linspace = np.linspace(start_y, end_y, 10)
                    left_angle_linspace = y_linspace
                    right_angle_linspace = y_linspace
                    # left_angle_linspace = np.linspace(min(self.left_angles), max(self.left_angles), 10)
                    # right_angle_linspace = np.linspace(min(self.right_angles), max(self.right_angles), 10)
                    await self.save_log()
                    await self.send(text_data=json.dumps({
                        'y_linspace' : y_linspace.astype('int').tolist(),
                        'left_angle_linspace' : left_angle_linspace.astype('int').tolist(),
                        'right_angle_linspace' : right_angle_linspace.astype('int').tolist()
                    }))
                except Exception as err:
                    print(err)
                    
            elif action == 'restart':
                self.start_positions_y = []
                self.end_positions_y = []
                self.left_angles = []
                self.right_angles = []
            else:
                step = text_data_json.get('STEP')
                y_value = text_data_json.get('HWNowPosition')
                if step == 0:
                    self.start_positions_y.append(y_value)
                elif step == 1:
                    self.end_positions_y.append(y_value)
        else:
            # 이미지 전달 받아 각도 추출
            print("Recieved image from application")
            bitmap_to_image = Image.open(io.BytesIO(bytes_data)) 
            image = np.asarray(bitmap_to_image)
            try:
                results = self.pose.process(image)
                pose_landmarks = results.pose_landmarks
                landmarks  = pose_landmarks.landmark
                # 각도
                right_shoulder = [landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                right_elbow    = [landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                right_wrist    = [landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].x,landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                right_hip      = [landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                left_shoulder  = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                left_elbow     = [landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                left_wrist     = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                left_hip       = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
                # 좌 팔꿈치 각도
                left_angle = self.calculate_angle(
                            left_shoulder,
                            left_elbow,
                            left_wrist
                        )
                # 우 팔꿈치 각도
                right_angle = self.calculate_angle(
                            right_shoulder,
                            right_elbow,
                            right_wrist
                        )
                
                self.left_angles.append(left_angle)
                self.right_angles.append(right_angle)
            except Exception as err:
                print(err) 

    @database_sync_to_async
    def save_log(self):
        """
        유저 가동범위 데이터 저장
        b_start_ypos
        c_start_ypos
        s_start_ypos
        b_end_ypos
        c_end_ypos
        s_end_ypos
        """
        try:
            print(self.exercise_type)
            user = User.objects.get(username=self.user_id)
            f_1 = None
            f_2 = None
            if self.exercise_type == 'latpulldown':
                f_1 = 'l_start_ypos'
                f_2 = 'l_end_ypos'
            elif self.exercise_type == 'blatpulldown':
                f_1 = 'b_start_ypos'
                f_2 = 'b_end_ypos'
            elif self.exercise_type == 'seatedrow':
                f_1 = 's_start_ypos'
                f_2 = 's_end_ypos'
            elif self.exercise_type == 'chestpress':
                f_1 = 'c_start_ypos'
                f_2 = 'c_end_ypos'

            setattr(user.userinfo, f_1, np.mean(self.start_positions_y))
            setattr(user.userinfo, f_2, np.mean(self.end_positions_y))
            user.userinfo.save()

            umfr = UserMuscleFunctionRange.objects.create(
                user=user,
                exercise_type=self.exercise_type,
                start_positions_y=np.mean(self.start_positions_y),
                end_positions_y=np.mean(self.end_positions_y),
                y_positions=np.linspace(np.mean(self.start_positions_y), np.mean(self.end_positions_y), 10),
                # left_angles=np.linspace(min(self.left_angles), max(self.left_angles), 10),
                # right_angles=np.linspace(min(self.right_angles), max(self.right_angles), 10)
            )
            print(self.exercise_type, " 가동범위 측정 완료")
        except Exception as err:
            print(err)

    def calculate_angle(self, a, b, c):
        a = np.array(a) # First
        b = np.array(b) # Mid
        c = np.array(c) # End
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle >180.0:
            angle = 360-angle
            
        return angle


class ROMHeadLateralflextion(AsyncWebsocketConsumer):
    '''
        머리 외측굴곡
    '''
    async def connect(self):
        # self.SHOURDER_ABDUCTION = "abduction"
        # self.SHOURDER_ADDUCTION = "adduction"
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
        self.rom_type = None
        self.direction = None

        # 어깨 중앙선을 그리기 위한 변수
        self.shoulder_center_coordinate = None
        self.nose_coordinate = None
        
        await self.accept()
        print("머리 외측굴곡 연결")

    async def disconnect(self, close_code):
        print("머리 외측굴곡 연결 해제")

  
    async def receive(self, text_data=None, bytes_data=None):
        context = {}

        if not bytes_data:
            
            text_data_json = json.loads(text_data,strict=False)
            if text_data_json.get('stepData'): #1차, 2차, 3차 측정관련데이터가 있으면
                step_data = text_data_json.get('stepData')
                # step_image,right_angle,left_angle = self.process_skeleton_from_base64(step_data) #base스켈레톤 및 각도 그리기
                # change right and left angle for flip
                step_image, left_angle, right_angle = self.process_skeleton_from_base64(step_data) #base스켈레톤 및 각도 그리기
                
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
                self.rom_type = text_data_json.get('rom_type')
                self.uuid = text_data_json.get('uuid')
                self.direction =  text_data_json.get('direction')
                self.direction = 'right' if self.direction == 'left' else 'left'
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

            if hasattr(results.pose_landmarks, 'landmark'):
                # 코와 어깨 선 중앙을 이어줌 (목)
                image_height, image_width, _ = image.shape
                # calculate nose's x, y
                nose_x = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].x * image_width)
                nose_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].y * image_height)
                nose_coordinate = (nose_x, nose_y)

                # calculate shoulder line
                right_shoulder_x = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * image_width
                right_shoulder_y = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * image_height
                left_shoulder_x = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x * image_width
                left_shoulder_y = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * image_height
                # 좌/우 어깨선 중앙에 점 표시
                shoulder_center_coordinate = (int((right_shoulder_x + left_shoulder_x) / 2), 
                                            int((right_shoulder_y + left_shoulder_y) / 2))
                # 어깨선 중앙으로부터 수직 좌표
                shoulder_center_line_coordinate = (shoulder_center_coordinate[0], shoulder_center_coordinate[1] - 400)
                # right_angle, left_angle = self.rom.measure_rom(action="shoulder",image=image)
                lateral_flextion_angle = str(round(calculate_angle(shoulder_center_line_coordinate,
                                                                shoulder_center_coordinate,
                                                                nose_coordinate,
                                                                shoulder_center_coordinate[0] - nose_coordinate[0] < 0), 0))

                # 어깨-코 선 그리기
                cv2.line(image, 
                        shoulder_center_coordinate, 
                        nose_coordinate, 
                        (255, 255, 255), 
                        2)
                
                # 어깨 중앙선 그리기
                cv2.line(image,
                        shoulder_center_coordinate,
                        shoulder_center_line_coordinate,
                        (255, 0, 0),
                        2)
                        
            # 가동범위 측정
            if self.is_start:
                self.right_angle, self.left_angle = self.rom.measure_rom(action="shoulder",image=image)
                # image = self._draw_angle(image,self.left_angle,self.right_angle)

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
        image_height, image_width, _ = image.shape

        results = self.pose.process(image)

        if hasattr(results.pose_landmarks, 'landmark'):
            # 코와 어깨 선 중앙을 이어줌 (목)
            # calculate nose's x, y
            nose_x = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].x * image_width)
            nose_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].y * image_height)
            nose_coordinate = (nose_x, nose_y)

            # calculate shoulder line
            right_shoulder_x = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * image_width
            right_shoulder_y = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * image_height
            left_shoulder_x = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x * image_width
            left_shoulder_y = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * image_height
            # 좌/우 어깨선 중앙에 점 표시
            shoulder_center_coordinate = (int((right_shoulder_x + left_shoulder_x) / 2), 
                                        int((right_shoulder_y + left_shoulder_y) / 2))
            # 어깨선 중앙으로부터 수직 좌표
            shoulder_center_line_coordinate = (shoulder_center_coordinate[0], shoulder_center_coordinate[1] - 400)
            # right_angle, left_angle = self.rom.measure_rom(action="shoulder",image=image)
            lateral_flextion_angle = str(round(calculate_angle(shoulder_center_line_coordinate,
                                                            shoulder_center_coordinate,
                                                            nose_coordinate,
                                                            shoulder_center_coordinate[0] - nose_coordinate[0] < 0), 0))

            right_angle = lateral_flextion_angle
            left_angle = lateral_flextion_angle
            mp_drawing.draw_landmarks(
                image, self.rom.results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            cv2.line(image, 
                    shoulder_center_coordinate, 
                    nose_coordinate, 
                    (255, 255, 255), 
                    2)

            # 어깨 중앙선 그리기
            cv2.line(image,
                    shoulder_center_coordinate,
                    shoulder_center_line_coordinate,
                    (255, 0, 0),
                    2)

        # image = self._draw_angle(image,left_angle,right_angle)
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


class ROMHeadflextion(AsyncWebsocketConsumer):
    '''
        머리 굴곡 / 신전 
        (동일하게 가는 것으로 변경 -> 23. 04.19)
    '''
    async def connect(self):
        # self.SHOURDER_ABDUCTION = "abduction"
        # self.SHOURDER_ADDUCTION = "adduction"
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
        self.rom_type = None
        self.direction = None
        
        # 기준 각도
        self.standard_angle = None

        await self.accept()
        print("머리 굴곡 연결")

    async def disconnect(self, close_code):
        print("머리 굴곡 연결 해제")

    
    async def receive(self, text_data=None, bytes_data=None):
        context = {}

        if not bytes_data:
            
            text_data_json = json.loads(text_data,strict=False)
            if text_data_json.get('stepData'): #1차, 2차, 3차 측정관련데이터가 있으면
                step_data = text_data_json.get('stepData')
                step_image,right_angle,left_angle = self.process_skeleton_from_base64(step_data) #base스켈레톤 및 각도 그리기
                
                right_angle = abs(self.standard_angle - right_angle)
                left_angle = abs(self.standard_angle - left_angle)

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
                self.rom_type = text_data_json.get('rom_type')
                self.uuid = text_data_json.get('uuid')
                self.direction =  text_data_json.get('direction')
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

            elif action == "standard_picture":
                direction = text_data_json.get('direction')
                self.standard_angle = self.angle

                print("standard angle: ", self.angle)
                
                await self.send(text_data=json.dumps({
                    'standard_angle' : self.standard_angle
                }))

            return

        else: #안드로이드에서 전송된 bytes이미지가 있으면
            bitmap_to_image = Image.open(io.BytesIO(bytes_data)) # 안드로이드에서 넘겨온 이미지 ByteArray를 이미지로 처리함.
            image = np.asarray(bitmap_to_image) #nparray변환
            image.flags.writeable = False
            results = self.pose.process(image)

            self.calc_ear_position(image, results)

            # 가동범위 측정
            if self.is_start:
                self.right_angle, self.left_angle = self.rom.measure_rom(action="shoulder",image=image)
                # image = self._draw_angle(image,self.left_angle,self.right_angle)

            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            processed_image = image_to_bytearray(image)
            
            await self.send(bytes_data=processed_image)  
            await self.send(text_data=json.dumps({
                    'left_angle': self.left_angle,
                    'right_angle': self.right_angle,
                    'completion': self.completion,
            }))
    
    def calc_ear_position(self, image, results):
        """
        귀 좌표에서 수직으로 올린 좌표 구하기
        """

        if not hasattr(results.pose_landmarks, 'landmark'):
            return

        image_height, image_width, _ = image.shape

        # 귀 좌표
        ear_coordination = (int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_EAR].x * image_width),
                            int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_EAR].y * image_height))

        # 귀 수직 좌표
        ear_vertical_coord = (int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_EAR].x * image_width),
                              int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_EAR].y * image_height) - 200)
        
        # 코 좌표
        nose_coord = (int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].x * image_width),
                      int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].y * image_height))

        # 귀-귀 수직 선
        cv2.line(image, 
                ear_coordination, 
                ear_vertical_coord, 
                (255, 0, 0), 
                2)

        # 귀-코 선
        cv2.line(image, 
                ear_coordination, 
                nose_coord, 
                (255, 0, 0), 
                2)

        self.angle = calculate_angle(ear_vertical_coord, ear_coordination, nose_coord, True)

        return image, self.angle, self.angle

    
    def process_skeleton_from_base64(self,step_data):
        
        image_pil = Image.open(io.BytesIO(base64.b64decode(step_data.get('base64Image'))))
        image = np.array(image_pil)
        image_height, image_width, _ = image.shape

        results = self.pose.process(image)

        image, left_angle, right_angle = self.calc_ear_position(image, results)

        # # 코와 어깨 선 중앙을 이어줌 (목)
        # # calculate nose's x, y
        # nose_x = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].x * image_width)
        # nose_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].y * image_height)
        # nose_coordinate = (nose_x, nose_y)

        # # calculate shoulder line
        # right_shoulder_x = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * image_width
        # right_shoulder_y = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * image_height
        # left_shoulder_x = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x * image_width
        # left_shoulder_y = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * image_height
        # # 좌/우 어깨선 중앙에 점 표시
        # shoulder_center_coordinate = (int((right_shoulder_x + left_shoulder_x) / 2), 
        #                               int((right_shoulder_y + left_shoulder_y) / 2))

        # # 어깨선 중앙으로부터 수직 좌표
        # shoulder_center_line_coordinate = (shoulder_center_coordinate[0], shoulder_center_coordinate[1] - 400)
        # # right_angle, left_angle = self.rom.measure_rom(action="shoulder",image=image)
        # lateral_flextion_angle = str(round(calculate_angle(shoulder_center_line_coordinate,
        #                                                    shoulder_center_coordinate,
        #                                                    nose_coordinate,
        #                                                    shoulder_center_coordinate[0] - nose_coordinate[0] < 0), 0))

        # right_angle = lateral_flextion_angle
        # left_angle = lateral_flextion_angle
        # mp_drawing.draw_landmarks(
        #     image, self.rom.results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # cv2.line(image, 
        #         shoulder_center_coordinate, 
        #         nose_coordinate, 
        #         (255, 255, 255), 
        #         2)

        # image = self._draw_angle(image,left_angle,right_angle)
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


class ROMHeadextension(AsyncWebsocketConsumer):
    '''
        머리 과신전
    '''
    async def connect(self):
        # self.SHOURDER_ABDUCTION = "abduction"
        # self.SHOURDER_ADDUCTION = "adduction"
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
        self.rom_type = None
        self.direction = None
        
        await self.accept()
        print("머리 과신전 연결")

    async def disconnect(self, close_code):
        print("머리 과신전 연결 해제")

    
    async def receive(self, text_data=None, bytes_data=None):
        context = {}

        if not bytes_data:
            
            text_data_json = json.loads(text_data,strict=False)
            if text_data_json.get('stepData'): #1차, 2차, 3차 측정관련데이터가 있으면
                step_data = text_data_json.get('stepData')
                step_image,right_angle,left_angle = self.process_skeleton_from_base64(step_data) #base스켈레톤 및 각도 그리기
                
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
                self.rom_type = text_data_json.get('rom_type')
                self.uuid = text_data_json.get('uuid')
                self.direction =  text_data_json.get('direction')
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
                # image = self._draw_angle(image,self.left_angle,self.right_angle)

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
        image_height, image_width, _ = image.shape

        results = self.pose.process(image)

        # 코와 어깨 선 중앙을 이어줌 (목)
        # calculate nose's x, y
        nose_x = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].x * image_width)
        nose_y = int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].y * image_height)
        nose_coordinate = (nose_x, nose_y)

        # calculate shoulder line
        right_shoulder_x = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * image_width
        right_shoulder_y = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * image_height
        left_shoulder_x = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x * image_width
        left_shoulder_y = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * image_height
        # 좌/우 어깨선 중앙에 점 표시
        shoulder_center_coordinate = (int((right_shoulder_x + left_shoulder_x) / 2), 
                                      int((right_shoulder_y + left_shoulder_y) / 2))

        # 어깨선 중앙으로부터 수직 좌표
        shoulder_center_line_coordinate = (shoulder_center_coordinate[0], shoulder_center_coordinate[1] - 400)
        # right_angle, left_angle = self.rom.measure_rom(action="shoulder",image=image)
        lateral_flextion_angle = str(round(calculate_angle(shoulder_center_line_coordinate,
                                                           shoulder_center_coordinate,
                                                           nose_coordinate,
                                                           shoulder_center_coordinate[0] - nose_coordinate[0] < 0), 0))

        right_angle = lateral_flextion_angle
        left_angle = lateral_flextion_angle
        mp_drawing.draw_landmarks(
            image, self.rom.results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        cv2.line(image, 
                shoulder_center_coordinate, 
                nose_coordinate, 
                (255, 255, 255), 
                2)

        # image = self._draw_angle(image,left_angle,right_angle)
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
