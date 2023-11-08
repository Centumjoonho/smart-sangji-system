from django.test import TestCase
from .analyzers import *
import cv2
import time
import numpy as np
from .models import *
import random
import datetime

while True:
    time.sleep(0.02)
    ExerciseStampLog.objects.create(
        uuid='asdfsdfsd-fsdfklasdjflkadsjf-sdklfjldksfj',
        time=datetime.datetime.now(),
        sensor_1=random.random(),
        elbow_left_angle=random.random(),
        elbow_right_angle=random.random(),
        shoulder_right_angle=random.random(),
        shoulder_left_angle=random.random(),
    )
    print("저장")