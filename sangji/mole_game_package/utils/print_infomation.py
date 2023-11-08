import cv2

def put_numCount(frame, numCount, loc=(70, 50), label_text='Num_Count', counterID=1):
    '''
    Args
        frame: img, we will use videoCaptuer img
        numCount: int, the number of extractions of arm
        loc: tuple, coordination of label_text
        label_text: str, optional arg, 
            by default we put 'Num_count_X', 
            where the x is the value of counterID
        counterID: int, the number of text areas
            if counterID is one (left arm count info)
            the loc of the 'label_text' location is (70, 50)
            
            if counterID is two (right arm count info), 
            the loc of the 'label_text' location is (500, 50)
    
    Return:
        None

    Description
        Draw 'numCount: count' on desired screen loaction
        Ex.: if numCount is 3, the text should be
            Num_Count_1: 3
        
        If counterID is two (left & right arms),
        we set the location of label_text differently
    '''

    # Set the label_text location
    if counterID==2:
        loc = (500, 150) # text for right arm info

    color_label_text = (0, 0, 255) # blue color
    color_numCount = (255, 0, 0) # red color
    
    # Draw label_text
    cv2.putText(
        img=frame,
        text='Num_Count' + str(counterID),
        org=loc,
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=3,
        color=color_label_text,
    )    

    # Draw the number of arm count
    cv2.putText(
        img=frame,
        text=str(int(numCount)),
        org=loc,
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=3,
        color=color_numCount,
    )    