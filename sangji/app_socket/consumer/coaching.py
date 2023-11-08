"""
AI Coaching Socket
"""
import io
import json
from PIL import Image
import mediapipe as mp
import numpy as np

from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer

from app_socket.consumer.musclefunction import image_to_bytearray

mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic
mp_pose = mp.solutions.pose

class CoachingPoseEstimation(AsyncWebsocketConsumer):
    '''
        AI 코칭용 포즈 측정
        
        각 프레임에 대하여
        - 관절 각도 산출 
        - 팔꿈치, 손목, 어깨 X, Y 값 반환
        
    '''
    async def connect(self):
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        
        self.right_shoulder = [0, 0]
        self.right_elbow = [0, 0]  
        self.right_wrist = [0, 0]   
        self.right_hip = [0, 0]  
        self.left_shoulder = [0, 0]
        self.left_elbow = [0, 0]  
        self.left_wrist = [0, 0]  
        self.left_hip = [0, 0]  

        await self.accept()
        print("AI 코칭용 포즈 측정 측정")

    async def disconnect(self,close_code):
        print("AI 코칭용 포즈 측정 측정 연결 해제")

    async def receive(self, text_data=None, bytes_data=None):
        bitmap_to_image = Image.open(io.BytesIO(bytes_data)) # 안드로이드에서 넘겨온 이미지 ByteArray를 이미지로 처리함.
        image = np.asarray(bitmap_to_image) #nparray변환
        
        image.flags.writeable = False
        results = self.pose.process(image)

        if results.pose_landmarks:
            # 각도
            landmarks  = results.pose_landmarks.landmark
            self.right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            self.right_elbow    = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            self.right_wrist    = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

            self.left_shoulder  = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            self.left_elbow     = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            self.left_wrist     = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

        # Send each landmark y value
        data = {
            "right_shoulder" : 1 - self.right_shoulder[1],
            "right_elbow" : 1 - self.right_elbow[1],
            "right_wrist" : 1 - self.right_wrist[1],
            "left_shoulder" : 1 - self.left_shoulder[1],
            "left_elbow" : 1 - self.left_elbow[1],
            "left_wrist" : 1 - self.left_wrist[1]
        }

        await self.send(text_data=json.dumps(data))
        
        mp_drawing.draw_landmarks(
            image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        processed_image = image_to_bytearray(image)
        await self.send(bytes_data=processed_image)  