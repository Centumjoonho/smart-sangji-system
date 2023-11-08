import os
import cv2
from PIL import Image
import face_recognition
from deepface import DeepFace

RESULT_OUTPUT_PATH = "/home/marketian/project/sangji/"
USER_FACE_DIR = os.path.join(RESULT_OUTPUT_PATH, "media/user_face")
NAEUN_IMAGE_PATH = os.path.join(USER_FACE_DIR, "naeun.jpg")
NAEUN_2_IMAGE_PATH = os.path.join(USER_FACE_DIR, "naeun2.jpg")
KJK_IMAGE_PATH = os.path.join(USER_FACE_DIR, "jk.jpg")
TOM_IMAGE_PATH = os.path.join(USER_FACE_DIR, "tom.jpg")
UNKNOWN_IMAGE_PATH = os.path.join(USER_FACE_DIR, "jy.jpg")
RECT_IMAGE_PATH = os.path.join(RESULT_OUTPUT_PATH, "download.png")
USE_IMAGE_PATH = NAEUN_IMAGE_PATH

def run_face_recognition() -> bool:
    image = face_recognition.load_image_file(USE_IMAGE_PATH)
    face_locations = face_recognition.face_locations(image)

    # if face is not detected, face locations returns []
    # if face is detected, face locations returns coordication.
    if not face_locations:
        print("Not Detected Face in image")
        return False
    
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    for (top, right, bottom, left) in face_locations:
        face_image = image[top:bottom, left:right]
        face_output_path = os.path.join(RESULT_OUTPUT_PATH, 'result.png')
        cv2.imwrite(face_output_path, face_image)
    
    print("It is done!")
    return True

def load_face_encoding(image_path: str):
    image = face_recognition.load_image_file(image_path)
    return face_recognition.face_encodings(image)[0]

def run_face_identification_with_bytes(picture_byte):
    """
     STATUS 
     0 : 인식 안됨
     1 : 얼굴 인식
     2 : 유저 매칭 실패
     3 : 유저 매칭
    """
    status = 0
    extra = {}
    is_user = False
    user_name = ""

    try:
        result = DeepFace.find(img_path=picture_byte, 
                            db_path=USER_FACE_DIR, 
                            enforce_detection=True)
        print(result)
        if len(result) > 0:
            status = 1
            for i, row in result[0].iterrows():
                user_name = get_user_name_from_file(row['identity']) # /home/marketian/project/sangji/media/user_face/jk.jpg
                if  not user_name:
                    status = 2
                status = 3
                
    except ValueError:
        print("Face is not detected in image")
        status = 0
        
    extra['user_name'] = user_name
    
    return status, extra

def run_face_identification(my_picture) -> bool:
    is_user = False
    user_name = ""
    # my_face_encoding now contains a universal 'encoding' of my facial features that can be compared to any other picture of a face!
    my_face_encoding = load_face_encoding(my_picture)

    # check i am a user in this system.
    face_list = os.listdir(USER_FACE_DIR)
    for face in face_list:
        face_encoding = load_face_encoding(os.path.join(USER_FACE_DIR, face))
        result = face_recognition.compare_faces([face_encoding], my_face_encoding)
        #TODO change this value to user identifier value
        user_name = face 
        if result[0]:
            is_user = True
            print(is_user, user_name)
            break

    return is_user

def get_user_name_from_file(img_path):
    return img_path.split('/')[-1].split('.')[0]

if __name__ == "__main__":
    # run_face_recognition()
    run_face_identification(NAEUN_IMAGE_PATH)