
import numpy as np
import mediapipe as mp


class ROMMeasurement():
    '''
        가동범위 측정
    '''

    def __init__(self):
        
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_holistic = mp.solutions.holistic
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        
        self.right_shoulder = [0,0]
        self.right_elbow = [0,0]
        self.right_wrist = [0,0]
        self.right_hip   = [0,0]

        self.left_shoulder = [0,0]
        self.left_elbow = [0,0]
        self.left_wrist = [0,0]
        self.left_hip  = [0,0]


    def measure_rom(self,action,image): # 가동범위 측정
        self.results = self.pose.process(image)
        right_angle = 0
        left_angle = 0

        try:
            if self.results.pose_landmarks:    
                pose_landmarks = self.results.pose_landmarks
                landmarks  = pose_landmarks.landmark

                self.right_shoulder = [landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                self.right_elbow    = [landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                self.right_wrist    = [landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].x,landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
                self.right_hip      = [landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].y]

                self.left_shoulder  = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                self.left_elbow     = [landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                self.left_wrist     = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                self.left_hip       = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]


                if action == "elbow": # 팔꿈치 가동범위 측정
                    

                    right_angle = self.calculate_angle(self.right_shoulder,self.right_elbow,self.right_wrist)
                    left_angle  = self.calculate_angle(self.left_shoulder,self.left_elbow,self.left_wrist)
                
                elif action == "shoulder":
                    right_angle = self.calculate_angle(self.right_elbow,self.right_shoulder,self.right_hip)
                    left_angle  = self.calculate_angle(self.left_elbow,self.left_shoulder,self.left_hip)
        except Exception as e:
            print(e)
        
        
        return right_angle, left_angle
        """
        22-11-23
        ROM 측정 시 FLIP 기능 구현을 위해
        LEFT -> RIGHT
        RIGHT -> LEFT로 변환하도록 구현
        """
        # return left_angle, right_angle
    
    

    def calculate_angle(self, a, b, c):
        a = np.array(a) # First
        b = np.array(b) # Mid
        c = np.array(c) # End
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        
        if angle >180.0:
            angle = 360-angle
            
        return angle

    
    
    def extract_pose_landmarks(self,landmarks):
        '''
            원하는 키포인 추출
        '''
        result = {}
        #추출 키포인 인덱스
        #https://google.github.io/mediapipe/solutions/pose.html
        extract_pose_index = [16,14,12,11,13,15,24,23]
        for i in range(len(landmarks)):
            if i in extract_pose_index:
                result[str(i)] = {
                    "x": landmarks[i].x,
                    "y": landmarks[i].y
                }
        
        return result

        



