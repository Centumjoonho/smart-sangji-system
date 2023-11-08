from PIL.Image import NONE
import cv2
from random import randint
import mediapipe as mp
import numpy as np

from time import sleep
from .InfoManager import InformationManager
from .WindowManager import WindowManager 
from .MoleManager import MoleManager
from .InfoManager import InformationManager
from .utils.Criteria import Criteria
from .utils.Timer import Timer
from .utils.angle_gage import angleGage
from .utils.measure_arm_information import measure_arm_distance, measure_shoulder_elbow_wrist_loc
from .utils.Colors import ColorCode
from .utils.PoseLandmarks import LandMarks
from .utils.angle_calculaters import calculate_angle
from .utils.get_player_grid_unit_id import get_grid_unit_id
from .utils.get_mole_unit_locations import get_grid_locations, get_grid_unit_distace
from .utils.mole_show_up import mole_show_up
from .utils.remove_background import remove_bg_mediapipe_selfie

from .remove_background_module import remove_background

mpPose = mp.solutions.pose
pose = mp.solutions.pose.Pose()


class Player():
    #초기 게임 설정 
    def __init__(self, divide_units=3, arm_position='right', selfie_mode=False, goal_count_to_clear=10):
        self.divide_unit = divide_units
        self.max_angle = 160
        self.min_angle = 30
        self.num_count_left = 0
        self.num_count_right = 0
        self.shrinked_left = True


        self.shrinked_right = True
        self.success = False
        self.distance = None # will be stored with tuple (left, right distance info)
        self.angle = None # will be stored with tuple (left, right angle info)
        self.grid_color = (255,0,0)
        self.grid_thickness = 2
        self.prev_shoulder_loc = None
        self.prev_index_loc = None
        self.mole_hit_success = False
        self.current_pane_id = None
        self.target_pane_id = None
        self.IS_FIRST = True
        self.SELFIE_MODE = selfie_mode
        self.MISSION_COMPLETE = False
        self.GOAL_COUNT_TO_CLEAR = goal_count_to_clear

        self.hammer_loc_x = 0
        self.hammer_loc_y = 0

     
        
        # 좌/우 팔 선택에 따라 해당 좌표 정보를 할당
        self.arm_position = arm_position
        if self.arm_position == 'right':
            self.shoulder_position = LandMarks.RIGHT_SHOULDER
            self.wrisk_position = LandMarks.RIGHT_WRIST
            self.index_position = LandMarks.RIGHT_INDEX
        elif self.arm_position == 'left':
            self.shoulder_position = LandMarks.LEFT_SHOULDER
            self.wrisk_position = LandMarks.LEFT_WRIST
            self.index_position = LandMarks.LEFT_INDEX
        else:
            print(f'You selected arm position: {self.arm_position}')
            print("arm_position must be either 'right' or 'left'")
        
        MOVE_TO_NEW_LOCATION = True
        self.win_manager = WindowManager()
        # self.win_manager.get_screenInfo()
        # self.win_manager.display_monitorInfo()
        # self.win_manager.create_windows()
        self.player_win_name = self.win_manager.window_names['Player']

        self.bg_window_size = (
            self.win_manager.windows_info['Mole']['height'],
            self.win_manager.windows_info['Mole']['width'],
        ) 

        self.info_window_size = (
            self.win_manager.windows_info['Information']['height'],
            self.win_manager.windows_info['Information']['width'],
        )
        
        self.mole_manager = MoleManager(self.bg_window_size, divide_unit=self.divide_unit)
        self.pane_timer = Timer()
        self.info_manager = InformationManager(self.GOAL_COUNT_TO_CLEAR)
        
        # Processing Mole window
        self.frame_mole_window = self.mole_manager.create_background_image(self.win_manager)
        
        self.mole_unit_loc_list = get_grid_locations(
            self.frame_mole_window, 
            self.divide_unit        
        )
        
        self.unit_distances = get_grid_unit_distace(
            self.frame_mole_window, 
            self.divide_unit
        )

        self.last_pane_id = 0
        

        
        super().__init__()         
    
    def set_goal_cnt(self,goal_cnt):
        self.GOAL_COUNT_TO_CLEAR = goal_cnt
        self.info_manager.hit_num_to_complete = goal_cnt

    
    def calculate_frame_relative_coordinate(self, frame, results, idx):
        """cv.image.shape에서 리턴하는 상대적 좌표를 입력으로 주어진
        frame 이미지에 적용하여 이미지상에 적용할 수 있는 좌표를 리턴합니다.
        Args:
            frame (numpy array): img (cv2 object), in case we use fram from webcam
            results (mediapipe pose object): object after processing 'mediapipe의 pose.process(frame)'
            idx (int): the target landmark index in result object
        Returns:
            loc_x, loc_y (tuple): relative location of frame
        """     
        
        try:
            x = results.pose_landmarks.landmark[idx].x
            y = results.pose_landmarks.landmark[idx].y
            # z = results.pose_landmarks.landmark[idx].z # we don't use z value, only use (x, y)
        except:
            return None
        
        frame_height, frame_width, _ = frame.shape
        loc_x = int(frame_width * x)
        loc_y = int(frame_height * y)
        
        return loc_x, loc_y


    def draw_excercise_grid(self, frame):
        # Get frame dimension from image (frame)
        frame_height, frame_width, _ = frame.shape # we don't use channel info

        ### 우선 절대 격자를 먼저 그리는 방법을 테스트 ###
        unit_dist_x = frame_width / self.divide_unit
        unit_dist_y = frame_height / self.divide_unit
        
        # Draw Horizontal lines
        for x in range(1, self.divide_unit):
            cv2.line(
                frame, 
                (0, int(unit_dist_y * x)), 
                (frame_width, int(unit_dist_y * x)), 
                thickness=self.grid_thickness,
                color=self.grid_color, # green line
            )

        # Draw vertical lines
        for x in range(1, self.divide_unit):
            cv2.line(
                frame, 
                (int(unit_dist_x * x), 0), 
                (int(unit_dist_x * x), frame_height), 
                thickness=self.grid_thickness,
                color=self.grid_color, # green line
            )        

        return frame


    def draw_shoulder_and_hand_loc(self, frame):
        try:
            results = pose.process(frame) 
        except:
            return

        # Calculate soulder location
        try:
            shoulder_loc = self.calculate_frame_relative_coordinate(
                frame, 
                results, 
                self.shoulder_position
            )
            self.prev_shoulder_loc = shoulder_loc
        except:
            shoulder_loc = self.prev_shoulder_loc

        # Calculate coordinate of current index location
        try:
            index_loc = self.calculate_frame_relative_coordinate(
                frame, 
                results, 
                self.index_position
            )
        except:
            index_loc = self.prev_index_loc
        
        # Draw a ractangle marker on target shoulder position
        try:
            rectangle_end_loc = (shoulder_loc[0] + 30, shoulder_loc[1] - 3)
        except:
            return None
        
        # Draw rectangle on shoulder location
        cv2.rectangle(
            frame, 
            shoulder_loc, 
            rectangle_end_loc, 
            thickness=-1, 
            color=ColorCode.SHOULDER_MARKER
        )
        
        # Draw cicle on wrist location
        cv2.circle(
            frame, 
            (index_loc), 
            radius=10, 
            color=(0, 0, 255), 
            thickness=-1
        )

        return frame

    def update_hammer_loc(self,frame,index_pos):
        '''
            0 ~ 1 사이 위치로 변환해서 업데이트
        '''
        frame_height, frame_width, _ = frame.shape
        self.hammer_loc_x = index_pos[0] / frame_width
        self.hammer_loc_y = index_pos[1] / frame_height
    
    def get_frames(self,frame):
        '''
            카메라로부터 프레임 받아서 각각 창에맞게 이미지 처리해서 반환
            return (mole_window_frame,player_window_frame,infomation_window_frame)
                mole_window_frame: 처리된 두더지창 이미지
                player_window_frame: 처리된 player창 이미지
                infomation_window_frame: 처리된 게임정보창 이미지
                
        '''    


        

        mole_window_frame =  None # 두더지창 프레임
        player_window_frame =  None # player창 프레임
        infomation_window_frame = None# 게임정보창 프레임
        
        

        # 초기 배경화면, 준비 자세 처리q
        if not self.success:
            # 미션을 완성하고 다시 반복되는 경우는 다른 이미지 출력
            if self.MISSION_COMPLETE: 
                # cv2.imshow(self.win_manager.window_names['Mole'], self.mole_manager.mission_completed_img)
                mole_window_frame = self.mole_manager.mission_completed_img
            
            # mole grid window에 초기 화면 뿌리기
            else:  
                # cv2.imshow(self.win_manager.window_names['Mole'], self.mole_manager.start_img)
                mole_window_frame = self.mole_manager.start_img
            
            # frame = cv2.flip(frame, 1)
            # player_window_frame = frame
            
            player_window_frame , self.success, self.distance, self.angle, shoulder_loc = measure_arm_distance(
                frame, self.player_win_name
            )
            
            if self.success and self.distance and self.angle and shoulder_loc:
                self.success = True
                try:
                    results = pose.process(frame) 
                    self.prev_shoulder_loc = self.calculate_frame_relative_coordinate(
                        frame, results, self.shoulder_position
                    )
                except:
                    pass
            
                
        else:
          
            
            # 일정시간 정해진 영역에 머물러 있으면 두더지 때리기 성공으로 처리
            #   -> 각도 측정이 도저히 안됨... ㅠ
            #   대안 1: 임준환 멀티 카메라 심험결과 적용
            #   대안 2: mediapipe 3D coordinate를 활용한 추가 실험
            results = pose.process(frame) 
            # frame = cv2.flip(frame, 1)
            index_pos = self.calculate_frame_relative_coordinate(frame, results, self.index_position,)
            

            
            self.current_pane_id = get_grid_unit_id(frame, self.divide_unit, index_pos)

            if self.IS_FIRST:
                self.target_pane_id = self.current_pane_id
                self.IS_FIRST = False
            

            if self.current_pane_id != None:
                self.update_hammer_loc(frame,index_pos)
                
                

                # 두더지가 현재 pane에서 머물러 있는 시간을 체크하고,
                # 일정 시간 (Criteria.SUCCESS_ARM_ANGLE_TO_HIT_MOLE) 이상 지난 경우
                # pane ID를 랜덤하게 추출하여 두더지 위치 변경
                if self.last_pane_id != self.current_pane_id:
                    self.info_manager.append_pane_stack(self.current_pane_id)


                if self.current_pane_id == self.target_pane_id:
                    
                    pane_stay_time = self.pane_timer.update(self.target_pane_id)
                else:
                    pane_stay_time = 0.0
                    self.info_manager.increase_pane_movement() # pane을 이동하면 pane_move_num +1 증가

                self.mole_hit_success = pane_stay_time >= Criteria.MIN_STAY_TIME_IN_PANE
                
                if self.mole_hit_success:
                    MOVE_TO_NEW_LOCATION = True
                    self.info_manager.increase_hit_number() # 두더지 때리기 성공하면 current_hit_num +1 증가
                    
                    # 미션 완료 여부 체크하고, 
                    # 미션 클리어인 경우 info_manager 리셋
                    self.MISSION_COMPLETE = self.info_manager.check_mission_complete()
                    if self.MISSION_COMPLETE:
                        self.info_manager.reset_game()
                        self.success = False
                else:
                    MOVE_TO_NEW_LOCATION = False
                
                
                
                if MOVE_TO_NEW_LOCATION: 
                    while True:
                        next_pane_id = randint(0, self.divide_unit**2 - 1)
                        
                        # 0번 Pane 위치 이동이 안되어 임시로 회피하도록 설정함
                        if next_pane_id == 0:
                            continue
                        
                        if self.target_pane_id != next_pane_id:
                            self.current_pane_id = self.target_pane_id
                            self.target_pane_id = next_pane_id
                            # MOVE_TO_NEW_LOCATION = False
                            break
                self.last_pane_id = self.current_pane_id
            
            else:
                pass
                
                # raise Exception(f'self.current_pane_id: {self.current_pane_id}')
            
            
            frame_player = self.draw_shoulder_and_hand_loc(frame)
            frame_player = self.draw_excercise_grid(frame_player)
            # frame_player = cv2.flip(frame_player, 1)
            player_window_frame = frame_player
            
            # frame_info = self.info_manager.display_game_info(
            #     window_size_height=self.info_window_size[0],
            #     window_size_width=self.info_window_size[1],
            # )
            # cv2.imshow(win_manager.window_names['Information'], frame_info)
            # infomation_window_frame = frame_info

        return mole_window_frame,player_window_frame,infomation_window_frame
            
            
# if __name__=='__main__':

#     player = Player()

#     cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
#     while cv2.waitKey(33) < 0:
#         _ , frame = cap.read()


#         try:
#             mole_window_frame, player_window_frame, infomation_window_frame = player.get_frames(frame)

#             cv2.imshow(player.win_manager.window_names['Mole'], mole_window_frame)

#             cv2.imshow(player.win_manager.window_names['Player'], player_window_frame)
            
#             cv2.imshow(player.win_manager.window_names['Information'], infomation_window_frame)
#         except Exception as e:
#             print()

        
