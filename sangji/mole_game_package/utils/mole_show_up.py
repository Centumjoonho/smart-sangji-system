import cv2
from random import randint


def mole_show_up(
    img_top, img_bg, 
    hpos=10, vpos=10, 
    img_top_x=300, img_top_y=300, 
    img_bg_x=800, img_bg_y=600,
    mole_switch=True
):
    '''
    Overlay top image (top_img) on top of background image (img_bg)
    using top and background image coordinations (locations).
    This function will return overlayed image (cv2.imread).
    Note: This function will work only when the mole_swithc is True.
    
    Referenced Blogs: 
        1. (Main Blog) https://bit.ly/3rec0Cg
        2. https://bit.ly/3nWDiek
        3. https://bit.ly/3DZNsAB

    Params:
        img_top [cv2 image]: foreground image, the mole image in our case
        img_bg [cv2 image]: background image
        
        hpos [int]: optional, horizontal length, x location in (x, y) coordinate
        vpos [int]: optional, vertical length, y location in (x, y) coordinate
            -> (hpos, vpos) is the starting point of img_top
        
        img_top_x [int]: optional, x value (length) of foreground image
        img_top_y [int]: optional, y value (length) of foreground image
        
        img_bg_x [int]: optional, x value (length) of background image
        img_bg_y [int]: optional, y value (length) of background image

        mole_switch [bool]: if true, return overlayed image. 
                           Otherwise do nothing
    
    return
        overlayed_img [cv2 image]: overlayed image with forground on background image
    '''    
    
    if mole_switch:
        
        # 배경 이미지 크기 조정
        img_bg_resized = cv2.resize(img_bg, (img_bg_x, img_bg_y), cv2.INTER_CUBIC)
        # cv2.imshow('img_bg_resized', img_bg_resized)

        # 상단 이미지 크기 조정
        img_top_resized = cv2.resize(img_top, (img_top_x, img_top_y), cv2.INTER_CUBIC)
        # cv2.imshow('img_top_resized', img_top_resized)

        rows, cols, channels = img_top_resized.shape
        
        # hpos, vpos 파라미터를 이용해 관심영역 ROI (Region of Interest) 설정
        roi = img_bg_resized[vpos:vpos+rows, hpos:hpos+cols]


        # 상단 이미지를 흑백(gray)으로 전환
        img_top_resized_gray = cv2.cvtColor(img_top_resized, cv2.COLOR_BGR2GRAY)
        # cv2.imshow('img_top_resized_gray', img_top_resized_gray)
        
        # Mask 생성 
        #   -> 픽셀값이 254 이상인 부분을 255(흰색)으로 변환
        _, mask = cv2.threshold(img_top_resized_gray, 240, 255, cv2.THRESH_BINARY)
        
        # Inverse Mask 생성
        #   -> Mask에서 흰색인 부분을 검은색으로 변환(반전시킴)
        mask_inv = cv2.bitwise_not(mask)

        # Mask를 roi 영역에 적용
        #   -> 
        img_bg_resized_masked = cv2.bitwise_and(roi, roi, mask=mask)
        # cv2.imshow('img_bg_resized_masked', img_bg_resized_masked)

        # 상단 원본 이미지에 역마스크 적용 
        #   -> 색이 있는 부분만 남김
        img_top_resized_invMasked = cv2.bitwise_and(img_top_resized, img_top_resized, mask=mask_inv)
        # cv2.imshow('img_top_resized_invMasked', img_top_resized_invMasked)

        combined_img = cv2.bitwise_or(img_bg_resized_masked, img_top_resized_invMasked)
        # cv2.imshow('combined_img', combined_img)

        # 이미지 합성
        img_bg_resized[vpos:vpos+rows, hpos:hpos+cols] = combined_img
        overlayed_img = img_bg_resized
        # cv2.cv2.imshow('img_bg_resized', overlayed_img)

        return overlayed_img


if __name__=='__main__':
    mole_img = cv2.imread('./imgs/mole_jklee.jpg')
    
    cap = cv2.VideoCapture(0)
    while cv2.waitKey(33) < 0:
        _ , frame = cap.read()
        hpos_rand_loc = randint(0, 500)
        vpos_rand_loc = randint(0, 300)
        frame = mole_show_up(mole_img, frame, hpos=hpos_rand_loc, vpos=vpos_rand_loc)
        cv2.imshow('Overlayed Image', frame)
        
    cv2.destroyAllWindows()
