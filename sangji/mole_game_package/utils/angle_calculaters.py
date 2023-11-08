import cv2
import numpy as np
import mediapipe as mp

mpDraw= mp.solutions.drawing_utils  #미디어 파이프 초록색 선 그리기
mpPose = mp.solutions.pose
pose = mp.solutions.pose.Pose()

# 3점 각도 계산(손목, 팔꿈치, 어깨)
def calculate_angle(wrist, elbow, shoulder):
        
    wrist = np.array(wrist) # First /손목
    elbow = np.array(elbow) # Mid /팔꿈치
    shoulder = np.array(shoulder) # End /어깨
    
    radian1 = np.arctan2(
        shoulder[1] - elbow[1], 
        shoulder[0] - elbow[0],
    )
    
    randan2 = np.arctan2(
        wrist[1] - elbow[1], 
        wrist[0] - elbow[0],
    )
    radians = radian1 - randan2

    angle = np.abs(radians * 180.0 / np.pi)
    # print(angle) 
    
    if angle > 180.0:
        angle = 360 - angle
        
    return angle

def moleUp_decision_and_update_numCount(angle, max_angle, min_angle, moleSwitch, shrinked, numCount):
    
    '''
    MAX_ANGL 이상 팔을 폈을 경우 관절운동 카운트 증가
    SHRINED_LEFT를 False로 세팅
    MIN_ANGLE 이하로 팔을 오므린 경우 
    SHRINED_LEFT를 True로 세팅
    
    pararms
        angle:      int, 측정된 팔 각도 (왼팔 또는 오른팔)
        moleSwitch: boolean, 두더지를 나타남 판단
        shrinked:   boolean, 기준 각도까지 팔을 오므렸었는지 추적
        numCount:   int, 현재까지 관절운동 횟수
    
    return
        tuple: (moleSwitch, shrinked, numCount)
    '''
    
    # 팔 각도가 160도 이상 펴면, 
    # 두더지 사라지도록 설정하고 운동횟수 1회 증가
    if angle >= max_angle:
        moleSwitch = False
        if shrinked:
            shrinked = False
            numCount += 1
    
    # 팔 각도를 60도 이하로 접으면,
    # 두더지가 나타나도록 설정하고, 
    elif angle < min_angle:
        moleSwitch = True
        if not shrinked:
            shrinked=True
    
    else:
        # MIN_ANGLE과 MAX_ANGLE 사이에서 운동하고 
        # 있는 경우 아무것도 하지 않음
        pass
    
    return moleSwitch, shrinked, numCount