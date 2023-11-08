"""
Developer: Juyoung Ahn

Module: Face Identification Module
"""
import io
import cv2
import json
import time
import numpy as np
import mediapipe as mp
from PIL import Image
import warnings

from channels.generic.websocket import AsyncWebsocketConsumer

from main.face_recognition_module import *

warnings.filterwarnings('ignore')

class FaceIdentificationConsumer(AsyncWebsocketConsumer):
    """This class is for face identification in Sangji Device."""

    async def connect(self):
        self.start_time = time.time()
        self.foundFace = False
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        await self.close()

    async def receive(self, text_data: str) -> None:
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send the received message back to the client
        await self.send(text_data=json.dumps({
            'message': message
        }))
    
    async def receive(self, bytes_data: bytes) -> None:
        # print("receive image")

        if self.foundFace:
            self.disconnect(close_code=999)

        bitmap_to_image = Image.open(io.BytesIO(bytes_data)) 
        image = np.asarray(bitmap_to_image)
        # bitmap_to_image.save('./test.png')
        status, extra = run_face_identification_with_bytes(image)

        if status == 3:
            self.foundFace = True

        print("처리 결과: ", status, extra)

        if time.time() - self.start_time > 10 and status == 1:
            status = 2 
            self.start_time = time.time()

        # print("소요시간: ", time.time() - self.start_time )

        await self.send(text_data=json.dumps({
            'status' : status,
            'username' : extra.get('user_name')
        }))