import mediapipe as mp

mpPose = mp.solutions.pose
pose = mpPose.Pose()

def estimate_arm_coordinates(landmark):
    
    # 왼쪽팔 좌표 
    LEFT_WRIST = [
        landmark[mpPose.PoseLandmark.RIGHT_WRIST].x,
        landmark[mpPose.PoseLandmark.RIGHT_WRIST].y,
    ]
    
    LEFT_ELBOW = [
        landmark[mpPose.PoseLandmark.RIGHT_ELBOW].x,
        landmark[mpPose.PoseLandmark.RIGHT_ELBOW].y,
    ]
    
    LEFT_SLOULDER = [
        landmark[mpPose.PoseLandmark.RIGHT_SHOULDER].x,
        landmark[mpPose.PoseLandmark.RIGHT_SHOULDER].y
    ]

    # 오른팔 좌표
    RIGHT_WRIST = [
        landmark[mpPose.PoseLandmark.LEFT_WRIST].x,
        landmark[mpPose.PoseLandmark.LEFT_WRIST].y,
    ]
    
    RIGHT_ELBOW = [
        landmark[mpPose.PoseLandmark.LEFT_ELBOW].x,
        landmark[mpPose.PoseLandmark.LEFT_ELBOW].y,
    ]
    
    RIGHT_SHOULDER = [
        landmark[mpPose.PoseLandmark.LEFT_SHOULDER].x,
        landmark[mpPose.PoseLandmark.LEFT_SHOULDER].y,
    ]

    # Coordinates for each arm
    arm_coordiates = (
        (LEFT_WRIST, LEFT_ELBOW, LEFT_SLOULDER),
        (RIGHT_WRIST, RIGHT_ELBOW, RIGHT_SHOULDER),
    )

    return arm_coordiates
