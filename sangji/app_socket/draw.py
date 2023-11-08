import math
import numpy as np
import cv2 


# SHOULDER_FLEXTION ="shoulder_flextion"
SHOULDER_FLEXTION ="shoulder_flexion"
SHOULDER_EXTENSION = "shoulder_extension"
ELBOW_FELEXTION_EXTENSION = "elbow_flextion_extension"
SHOULDER_ABDUCTION_ADDUCTION = "shoulder_abduction_adduction"
LEFT = "left"
RIGHT = "right"

def calculate_angle(a, b, c):
    a = np.array(a) # First
    b = np.array(b) # Mid
    c = np.array(c) # End
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle >180.0:
        angle = 360-angle
        
    return angle
def distance(x1, y1, x2, y2):
    result = math.sqrt( math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))
    return result


def draw_angle(img,position,degree,action,sortation,color=(0,0,255)): # img: numpy, position: [x1,y1,x2,y2], degree: '40', to = [ 'numpy','pillow']
    
    end_degree = 0
    start = position[:2]
    end   = position[2:]
    centerx = int((start[0]+end[0])/2)
    centery = int((start[1]+end[1])/2)
    center  = [centerx,centery]
    radius  = int(distance(centerx,centery,end[0],end[1]) )
    
    zero_degree_point = [centerx+radius,centery]

    
    # print(f"zero:{zero_degree_point}, center:{center},start:{start}")

    
    if zero_degree_point[1] > start[1]:    
        st_degree  = -calculate_angle(zero_degree_point,center,start)
    else:
        st_degree  = calculate_angle(zero_degree_point,center,start)
    
    
    # print(action, sortation)
    if action == SHOULDER_FLEXTION and sortation == LEFT: #왼쪽 어깨굴곡이면
        end_degree = (st_degree - 180)
    
    elif action == SHOULDER_FLEXTION and sortation == RIGHT: #오른쪽 어깨굴곡이면
        end_degree = (st_degree + 180)
    
    elif action == SHOULDER_EXTENSION and sortation == LEFT: #왼쪽 어깨신전이면
        end_degree = (st_degree + 180)

    elif action == SHOULDER_EXTENSION and sortation == RIGHT: #오른쪽 어깨신전이면
        end_degree = (st_degree - 180)

    elif action == SHOULDER_ABDUCTION_ADDUCTION and sortation == LEFT: #왼쪽 어깨외전/내전
        end_degree = (st_degree + 180)
    
    elif action == SHOULDER_ABDUCTION_ADDUCTION and sortation == RIGHT: #오른쪽 어깨외전/내전
        end_degree = (st_degree - 180)
    
    elif action == ELBOW_FELEXTION_EXTENSION and sortation == RIGHT: #오른쪽 팔꿈치 굴곡/신전 이면
        end_degree = (st_degree - 180)
    
    elif action == ELBOW_FELEXTION_EXTENSION and sortation == LEFT: #오른쪽 팔꿈치 굴곡/신전 이면
        end_degree = (st_degree + 180)


    # print(st_degree,end_degree)

    
    cv2.putText(img,str(degree),tuple(center),cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2,cv2.LINE_AA)

    drawn_img = cv2.ellipse(img=img,center=(centerx,centery),axes=(radius,radius),angle=0,startAngle=st_degree,endAngle=end_degree,color=color,thickness=2) 
    
    return drawn_img




# img = 
# draw_angle(img,position = [50,50,100,100],degree='50')