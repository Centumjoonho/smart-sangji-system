import json
from enum import Enum

from django.conf import settings
from django.db import models



class ExerciseLog(models.Model):
    """
    재활운동 종료 후 저장되는 필드
    """
    # 사용자 정보
    uuid = models.CharField(max_length=100, null=True, blank=True)
    user_sex = models.CharField(max_length=2, null=True, blank=True)
    user_age = models.CharField(max_length=2, null=True, blank=True)
    user_height = models.CharField(max_length=3, null=True, blank=True)
    user_weight = models.CharField(max_length=3, null=True, blank=True)
    user_name = models.CharField(max_length=10, null=True, blank=True)
    user_handicapped_type = models.CharField(max_length=10, null=True, blank=True)
    # ROM 
    angle_elbow1 = models.CharField(max_length=3, null=True, blank=True)
    angle_shoulder1 = models.CharField(max_length=3, null=True, blank=True)
    angle_shoulder2 = models.CharField(max_length=3, null=True, blank=True)
    # 운동 정보
    exercise_type = models.CharField(max_length=50)
    count = models.IntegerField(default=0)
    running_time = models.CharField(max_length=20, null=True, blank=True)
    # 기본 필드
    created_at = models.DateTimeField(auto_now=True)

class UserInfomation(models.Model):
    uuid = models.CharField(max_length=100, null=True, blank=True)
    user_sex = models.CharField(max_length=2, null=True, blank=True)
    user_age = models.CharField(max_length=2, null=True, blank=True)
    user_height = models.CharField(max_length=3, null=True, blank=True)
    user_weight = models.CharField(max_length=3, null=True, blank=True)
    user_name = models.CharField(max_length=10, null=True, blank=True)
    user_handicapped_type = models.CharField(max_length=10, null=True, blank=True)
    # =========ROM========= 
    #====팔꿈치굴곡====
    #왼쪽팔꿈치굴곡
    step1_left_elbow_flextion_angle = models.CharField(max_length=3, null=True, blank=True) #1차측정된 왼쪽팔꿈치굴곡 각도
    step1_left_elbow_flextion_image =  models.TextField(null=True,blank=True) # 1차측정된 왼쪽팔꿈치이미지
    step2_left_elbow_flextion_angle = models.CharField(max_length=3, null=True, blank=True) #2차측정된 왼쪽팔꿈치굴곡 각도
    step2_left_elbow_flextion_image =  models.TextField(null=True,blank=True) # 2차측정된 왼쪽팔꿈치이미지
    step3_left_elbow_flextion_angle = models.CharField(max_length=3, null=True, blank=True) #3차측정된 왼쪽팔꿈치굴곡 각도
    step3_left_elbow_flextion_image =  models.TextField(null=True,blank=True) # 3차측정된 왼쪽팔꿈치이미지
    left_elbow_flextion_max_angle  =  models.CharField(max_length=3, null=True, blank=True) #왼쪽팔꿈치굴곡 1,2,3차 중 최대각도
    left_elbow_flextion_avg_angle  =  models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # 왼쪽팔꿈치굴곡 1,2,3차 중 평균각도
    #오른쪽팔꿈치굴곡 
    step1_right_elbow_flextion_angle = models.CharField(max_length=3, null=True, blank=True) #1차측정된 오른쪽팔꿈치굴곡 각도
    step1_right_elbow_flextion_image =  models.TextField(null=True,blank=True) # 1차측정된 오른쪽팔꿈치이미지
    step2_right_elbow_flextion_angle = models.CharField(max_length=3, null=True, blank=True) #2차측정된 오른쪽팔꿈치굴곡 각도
    step2_right_elbow_flextion_image =  models.TextField(null=True,blank=True) # 2차측정된 오른쪽팔꿈치이미지
    step3_right_elbow_flextion_angle = models.CharField(max_length=3, null=True, blank=True) #3차측정된 오른쪽팔꿈치굴곡 각도
    step3_right_elbow_flextion_image =  models.TextField(null=True,blank=True) # 3차측정된 오른쪽팔꿈치이미지
    right_elbow_flextion_max_angle   =  models.CharField(max_length=3, null=True, blank=True) #오른쪽팔꿈치굴곡 1,2,3차 중 최대각도
    right_elbow_flextion_avg_angle   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # 오른쪽팔꿈치굴곡 1,2,3차 중 평균각도

    #====팔꿈치신전====
    #왼쪽팔꿈치신전
    step1_left_elbow_extension_angle = models.CharField(max_length=3, null=True, blank=True) #1차측정된 왼쪽팔꿈치신전 각도
    step1_left_elbow_extension_image =  models.TextField(null=True,blank=True) # 1차측정된 왼쪽팔꿈치신전 이미지
    step2_left_elbow_extension_angle = models.CharField(max_length=3, null=True, blank=True) #2차측정된 왼쪽팔꿈치신전 각도
    step2_left_elbow_extension_image =  models.TextField(null=True,blank=True) # 2차측정된 왼쪽팔꿈치내전 이미지
    step3_left_elbow_extension_angle = models.CharField(max_length=3, null=True, blank=True) #3차측정된 왼쪽팔꿈치내전 각도
    step3_left_elbow_extension_image =  models.TextField(null=True,blank=True) # 3차측정된 왼쪽팔꿈치내전 이미지
    left_elbow_extension_min_angle  = models.CharField(max_length=3, null=True, blank=True) #왼쪽팔꿈치굴곡 1,2,3차 중 최소각도
    left_elbow_extension_avg_angle  = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # 왼쪽팔꿈치굴곡 1,2,3차 중 평균각도
    #오른쪽팔꿈치신전
    step1_right_elbow_extension_angle = models.CharField(max_length=3, null=True, blank=True) #1차측정된 오른쪽팔꿈치신전 각도
    step1_right_elbow_extension_image =  models.TextField(null=True,blank=True) # 1차측정된 오른쪽팔꿈치신전 이미지
    step2_right_elbow_extension_angle = models.CharField(max_length=3, null=True, blank=True) #2차측정된 오른쪽팔꿈치신전 각도
    step2_right_elbow_extension_image =  models.TextField(null=True,blank=True) # 2차측정된 오른쪽팔꿈치내전 이미지
    step3_right_elbow_extension_angle = models.CharField(max_length=3, null=True, blank=True) #3차측정된 오른쪽팔꿈치내전 각도
    step3_right_elbow_extension_image =  models.TextField(null=True,blank=True) # 3차측정된 오른쪽팔꿈치내전 이미지
    right_elbow_extension_min_angle  = models.CharField(max_length=3, null=True, blank=True) #오른쪽팔꿈치굴곡 1,2,3차 중 최소각도
    right_elbow_extension_avg_angle  = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # 오른쪽팔꿈치굴곡 1,2,3차 중 평균각도
    
    #====어깨외전====
    #왼쪽어깨외전
    step1_left_shoulder_abduction_angle = models.CharField(max_length=3, null=True, blank=True) #1차측정된 왼쪽어깨외전각도
    step1_left_shoulder_abduction_image = models.TextField(null=True,blank=True) # 1차측정된 왼쪽어깨외전이미지
    step2_left_shoulder_abduction_angle = models.CharField(max_length=3, null=True, blank=True) #2차측정된 왼쪽어깨외전각도
    step2_left_shoulder_abduction_image = models.TextField(null=True,blank=True) # 2차측정된 왼쪽어깨외전이미지
    step3_left_shoulder_abduction_angle = models.CharField(max_length=3, null=True, blank=True) #3차측정된 왼쪽어깨외전각도
    step3_left_shoulder_abduction_image = models.TextField(null=True,blank=True) # 3차측정된 왼쪽어깨외전이미지
    left_shoulder_abduction_max_angle = models.CharField(max_length=3, null=True, blank=True) #왼쪽어깨외전 1,2,3차 중 최대각도
    left_shoulder_abduction_avg_angle  = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # 왼쪽어깨외전 1,2,3차 중 평균각도
    #오른쪽어깨외전
    step1_right_shoulder_abduction_angle = models.CharField(max_length=3, null=True, blank=True) #1차측정된 오른쪽어깨외전각도
    step1_right_shoulder_abduction_image = models.TextField(null=True,blank=True) # 1차측정된 오른쪽어깨외전이미지
    step2_right_shoulder_abduction_angle = models.CharField(max_length=3, null=True, blank=True) #2차측정된 오른쪽어깨외전각도
    step2_right_shoulder_abduction_image = models.TextField(null=True,blank=True) # 2차측정된 오른쪽어깨외전이미지
    step3_right_shoulder_abduction_angle = models.CharField(max_length=3, null=True, blank=True) #3차측정된 오른쪽어깨외전각도
    step3_right_shoulder_abduction_image = models.TextField(null=True,blank=True) # 3차측정된 오른쪽어깨외전이미지
    right_shoulder_abduction_max_angle = models.CharField(max_length=3, null=True, blank=True) #오른쪽어깨외전 1,2,3차 중 최대각도
    right_shoulder_abduction_avg_angle  = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # 오른쪽어깨외전 1,2,3차 중 평균각도

    #====어깨내전=====
    #왼쪽어깨내전
    step1_left_shoulder_adduction_angle = models.CharField(max_length=3, null=True, blank=True) #1차측정된 왼쪽어깨내전각도
    step1_left_shoulder_adduction_image = models.TextField(null=True,blank=True) # 1차측정된 왼쪽어깨내전이미지
    step2_left_shoulder_adduction_angle = models.CharField(max_length=3, null=True, blank=True) #2차측정된 왼쪽어깨내전각도
    step2_left_shoulder_adduction_image = models.TextField(null=True,blank=True) # 2차측정된 왼쪽어깨내전이미지
    step3_left_shoulder_adduction_angle = models.CharField(max_length=3, null=True, blank=True) #3차측정된 왼쪽어깨내전각도
    step3_left_shoulder_adduction_image = models.TextField(null=True,blank=True) # 3차측정된 왼쪽어깨내전이미지
    left_shoulder_adduction_min_angle   = models.CharField(max_length=3, null=True, blank=True) # 왼쪽어깨내전 1,2,3차 중 최소각도
    left_shoulder_adduction_avg_angle   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) #왼쪽어깨내전 1,2,3차 중 평균각도

    #오른쪽어깨내전
    step1_right_shoulder_adduction_angle = models.CharField(max_length=3, null=True, blank=True) #1차측정된 오른쪽어깨내전각도
    step1_right_shoulder_adduction_image = models.TextField(null=True,blank=True) # 1차측정된 오른쪽어깨내전이미지
    step2_right_shoulder_adduction_angle = models.CharField(max_length=3, null=True, blank=True) #2차측정된 오른쪽어깨내전각도
    step2_right_shoulder_adduction_image = models.TextField(null=True,blank=True) # 2차측정된 오른쪽어깨내전이미지
    step3_right_shoulder_adduction_angle = models.CharField(max_length=3, null=True, blank=True) #3차측정된 오른쪽어깨내전각도
    step3_right_shoulder_adduction_image = models.TextField(null=True,blank=True) # 3차측정된 오른쪽어깨내전이미지
    right_shoulder_adduction_min_angle   = models.CharField(max_length=3, null=True, blank=True) # 오른쪽어깨내전 1,2,3차 중 최소각도
    right_shoulder_adduction_avg_angle   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) #오른쪽어깨내전 1,2,3차 중 평균각도
    
    #어깨 굴곡/신전
    #====어깨굴곡====
    #왼쪽어깨굴곡
    step1_left_shoulder_flextion_angle = models.CharField(max_length=3, null=True, blank=True) #1차측정된 왼쪽어깨굴곡각도
    step1_left_shoulder_flextion_image = models.TextField(null=True,blank=True) # 1차측정된 왼쪽어깨굴곡이미지
    step2_left_shoulder_flextion_angle = models.CharField(max_length=3, null=True, blank=True) #2차측정된 왼쪽어깨굴곡각도
    step2_left_shoulder_flextion_image = models.TextField(null=True,blank=True) # 2차측정된 왼쪽어깨굴곡이미지
    step3_left_shoulder_flextion_angle = models.CharField(max_length=3, null=True, blank=True) #3차측정된 왼쪽어깨굴곡각도
    step3_left_shoulder_flextion_image = models.TextField(null=True,blank=True) # 3차측정된 왼쪽어깨굴곡이미지
    left_shoulder_flextion_max_angle   = models.CharField(max_length=3, null=True, blank=True) # 왼쪽어깨굴곡 1,2,3차 중 최소각도
    left_shoulder_flextion_avg_angle   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) #왼쪽어깨굴곡 1,2,3차 중 평균각도
    #오른쪽어깨굴곡
    step1_right_shoulder_flextion_angle = models.CharField(max_length=3, null=True, blank=True) #1차측정된 오른쪽어깨굴곡각도
    step1_right_shoulder_flextion_image = models.TextField(null=True,blank=True) # 1차측정된 오른쪽어깨굴곡이미지
    step2_right_shoulder_flextion_angle = models.CharField(max_length=3, null=True, blank=True) #2차측정된 오른쪽어깨굴곡각도
    step2_right_shoulder_flextion_image = models.TextField(null=True,blank=True) # 2차측정된 오른쪽어깨굴곡이미지
    step3_right_shoulder_flextion_angle = models.CharField(max_length=3, null=True, blank=True) #3차측정된 오른쪽어깨굴곡각도
    step3_right_shoulder_flextion_image = models.TextField(null=True,blank=True) # 3차측정된 오른쪽어깨굴곡이미지
    right_shoulder_flextion_max_angle   = models.CharField(max_length=3, null=True, blank=True) # 오른쪽어깨굴곡 1,2,3차 중 최소각도
    right_shoulder_flextion_avg_angle   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) #오른쪽어깨굴곡 1,2,3차 중 평균각도

    #왼쪽어깨신전
    step1_left_shoulder_extension_angle = models.CharField(max_length=3, null=True, blank=True) #1차측정된 왼쪽어깨신전각도
    step1_left_shoulder_extension_image = models.TextField(null=True,blank=True) # 1차측정된 왼쪽어깨신전이미지
    step2_left_shoulder_extension_angle = models.CharField(max_length=3, null=True, blank=True) #2차측정된 왼쪽어깨신전각도
    step2_left_shoulder_extension_image = models.TextField(null=True,blank=True) # 2차측정된 왼쪽어깨신전이미지
    step3_left_shoulder_extension_angle = models.CharField(max_length=3, null=True, blank=True) #3차측정된 왼쪽어깨신전각도
    step3_left_shoulder_extension_image = models.TextField(null=True,blank=True) # 3차측정된 왼쪽어깨신전이미지
    left_shoulder_extension_max_angle   = models.CharField(max_length=3, null=True, blank=True) # 왼쪽어깨신전 1,2,3차 중 최소각도
    left_shoulder_extension_avg_angle   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) #왼쪽어깨신전 1,2,3차 중 평균각도

    #오른쪽어깨신전
    step1_right_shoulder_extension_angle = models.CharField(max_length=3, null=True, blank=True) #1차측정된 오른쪽어깨신전각도
    step1_right_shoulder_extension_image = models.TextField(null=True,blank=True) # 1차측정된 오른쪽어깨신전이미지
    step2_right_shoulder_extension_angle = models.CharField(max_length=3, null=True, blank=True) #2차측정된 오른쪽어깨신전각도
    step2_right_shoulder_extension_image = models.TextField(null=True,blank=True) # 2차측정된 오른쪽어깨신전이미지
    step3_right_shoulder_extension_angle = models.CharField(max_length=3, null=True, blank=True) #3차측정된 오른쪽어깨신전각도
    step3_right_shoulder_extension_image = models.TextField(null=True,blank=True) # 3차측정된 오른쪽어깨신전이미지
    right_shoulder_extension_max_angle   = models.CharField(max_length=3, null=True, blank=True) # 오른쪽어깨신전 1,2,3차 중 최소각도
    right_shoulder_extension_avg_angle   = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) #오른쪽어깨신전 1,2,3차 중 평균각도

    # 최대 근력
    maxium_strengh = models.CharField(max_length=3, null=True, blank=True)
    minium_strengh = models.CharField(max_length=3, null=True, blank=True)
    midium_strengh = models.CharField(max_length=3, null=True, blank=True)

    strength_logs = models.TextField(null=True, blank=True)

    # 구간별 평균 각도
    isometric_latpulldown_max_position_last_elbow_left_angle = models.CharField(max_length=3, null=True, blank=True)
    isometric_latpulldown_max_position_last_elbow_right_angle = models.CharField(max_length=3, null=True, blank=True)
    isometric_latpulldown_max_position_last_shoulder_right_angle = models.CharField(max_length=3, null=True, blank=True)
    isometric_latpulldown_max_position_last_shoulder_left_angle = models.CharField(max_length=3, null=True, blank=True)
    
    isometric_latpulldown_mid_position_last_elbow_left_angle = models.CharField(max_length=3, null=True, blank=True)
    isometric_latpulldown_mid_position_last_elbow_right_angle = models.CharField(max_length=3, null=True, blank=True)
    isometric_latpulldown_mid_position_last_shoulder_right_angle = models.CharField(max_length=3, null=True, blank=True)
    isometric_latpulldown_mid_position_last_shoulder_left_angle = models.CharField(max_length=3, null=True, blank=True)
    
    isometric_latpulldown_min_position_last_elbow_left_angle = models.CharField(max_length=3, null=True, blank=True)
    isometric_latpulldown_min_position_last_elbow_right_angle = models.CharField(max_length=3, null=True, blank=True)
    isometric_latpulldown_min_position_last_shoulder_right_angle = models.CharField(max_length=3, null=True, blank=True)
    isometric_latpulldown_min_position_last_shoulder_left_angle = models.CharField(max_length=3, null=True, blank=True)
    
    # 재활운동 랫 풀다운 평균 각도
    revital_latpulldown_maxium_strengh = models.CharField(max_length=3, null=True, blank=True)
    revital_latpulldown_minium_strengh = models.CharField(max_length=3, null=True, blank=True)
    revital_latpulldown_midium_strengh = models.CharField(max_length=3, null=True, blank=True)
    revital_latpulldown_strength_logs = models.TextField(null=True, blank=True)
    revital_latpulldown_max_position_last_elbow_left_angle = models.CharField(max_length=3, null=True, blank=True)
    revital_latpulldown_max_position_last_elbow_right_angle = models.CharField(max_length=3, null=True, blank=True)
    revital_latpulldown_max_position_last_shoulder_right_angle = models.CharField(max_length=3, null=True, blank=True)
    revital_latpulldown_max_position_last_shoulder_left_angle = models.CharField(max_length=3, null=True, blank=True)
    
    revital_latpulldown_mid_position_last_elbow_left_angle = models.CharField(max_length=3, null=True, blank=True)
    revital_latpulldown_mid_position_last_elbow_right_angle = models.CharField(max_length=3, null=True, blank=True)
    revital_latpulldown_mid_position_last_shoulder_right_angle = models.CharField(max_length=3, null=True, blank=True)
    revital_latpulldown_mid_position_last_shoulder_left_angle = models.CharField(max_length=3, null=True, blank=True)
    
    revital_latpulldown_min_position_last_elbow_left_angle = models.CharField(max_length=3, null=True, blank=True)
    revital_latpulldown_min_position_last_elbow_right_angle = models.CharField(max_length=3, null=True, blank=True)
    revital_latpulldown_min_position_last_shoulder_right_angle = models.CharField(max_length=3, null=True, blank=True)
    revital_latpulldown_min_position_last_shoulder_left_angle = models.CharField(max_length=3, null=True, blank=True)
    

    # RM
    RM_5_min = models.CharField(max_length=5, null=True, blank=True) 
    RM_5_max = models.CharField(max_length=5, null=True, blank=True) 
    RM_5_mid = models.CharField(max_length=5, null=True, blank=True) 

    # ROM 등장성 22.06.23
    ROM_isotonic_start_ypos = models.CharField(max_length=5, null=True, blank=True)
    ROM_isotonic_end_ypos = models.CharField(max_length=5, null=True, blank=True)
    ROM_isotonic_1rm = models.CharField(max_length=5, null=True, blank=True)

    # ROM 등척성 22.06.28
    ROM_isometric_1rm = models.CharField(verbose_name="등척성 최대근력", max_length=5, null=True, blank=True)

    # ROM 등속성 22.07.29
    ROM_isokinetic_1rm = models.CharField(verbose_name="등속성 최대근력", max_length=5, null=True, blank=True)

    # 랫 풀 다운 단계
    latpulldown_level = models.IntegerField(default=10) 
    created_at = models.DateTimeField(auto_now=True)

class ExerciseStampLog(models.Model):
    type = models.CharField(max_length=1, null=True, blank=True)
    uuid = models.CharField(max_length=100, null=True, blank=True)
    time = models.CharField(max_length=100, null=True, blank=True)
    sensor_1 = models.CharField(max_length=100, null=True, blank=True)
    sensor_2 = models.CharField(max_length=100, null=True, blank=True)
    elbow_left_angle = models.CharField(max_length=100, null=True, blank=True)
    elbow_right_angle = models.CharField(max_length=100, null=True, blank=True)
    shoulder_right_angle = models.CharField(max_length=100, null=True, blank=True)
    shoulder_left_angle = models.CharField(max_length=100, null=True, blank=True)

class ROMMeasureLog(models.Model):
    uuid = models.CharField(verbose_name="사용자", max_length=100, null=True, blank=True)
    type = models.CharField(verbose_name="운동 종류", max_length=20)
    value = models.CharField(verbose_name="값", max_length=5)
    created_at = models.DateTimeField(verbose_name="측정일시", auto_now_add=True)
    
class MoleDataLog(models.Model):
    """
    두더지 잡기 로그
    """
    game_id = models.CharField(max_length=50, null=True, blank=True)
    username = models.CharField(max_length=20, null=True, blank=True)
    grid_size = models.CharField(max_length=3, null=True, blank=True)
    timestamp = models.CharField(max_length=20, null=True, blank=True)
    hit_count = models.CharField(max_length=3, null=True, blank=True)
    mole_position = models.CharField(max_length=3, null=True, blank=True)
    pane_count = models.CharField(max_length=5, null=True, blank=True)
    hammer_position =  models.CharField(max_length=3, null=True, blank=True) # 손 위치
    angle_1 = models.CharField(max_length=3, null=True, blank=True) # 겨드랑이 각도
    angle_2 = models.CharField(max_length=3, null=True, blank=True) # 팔꿈치 각도

class MuscleFunctionLogData(models.Model):
    """
    2022-10-27
    근기능검사 측정 로그 저장
    """

    class ExerciseType(Enum):
        musclefunction_isometric = ('등척성', 'musclefunction_isometric')
        musclefunction_isokinetic = ('등속성', 'musclefunction_isokinetic')
        musclefunction_isotonic = ('등장성', 'musclefunction_isotonic')
        # Add more exercise types and translations as needed

        def __init__(self, translation_kr, translation_en):
            self.translation_kr = translation_kr
            self.translation_en = translation_en
            
    user_id = models.CharField(verbose_name="사용자", max_length=100, null=True, blank=True)
    exercise_type = models.CharField(verbose_name="운동 종류", max_length=50)
    log = models.TextField(verbose_name="측정기록")
    extra = models.TextField(null=True, blank=True, verbose_name="추가 데이터")
    created_at = models.DateTimeField(verbose_name="측정일시", auto_now_add=True)

    def musclefunction_infomation_str_with_date(self):
        exercise = self.ExerciseType[self.exercise_type]

        return '{} | {}'.format(exercise.translation_kr,
                                self.created_at.strftime('%Y-%m-%d'))
                            
    def musclefunction_infomation_str(self):
        exercise = self.ExerciseType[self.exercise_type]

        return '{}'.format(exercise.translation_kr)
    
    def get_extra_value(self, value):
        try:
            extra_json = json.loads(self.extra)
            return extra_json[value]
        except KeyError as err:
            return None
    
    def get_hand_value(self):
        return settings.EN_KR_LABEL_MAPPING \
                       .get(self.get_extra_value('hand_type'))
    
    def get_exercise_value(self):
        return settings.EN_KR_LABEL_MAPPING \
                       .get(self.get_extra_value('exercise'))
    
    def get_set_value(self):
        return self.get_extra_value('set')

    def get_count_value(self):
        return self.get_extra_value('count')

class ROMLogData(models.Model):
    """
        ROM 측정 결과 저장을 위한 Table
    """
    user_id = models.CharField(verbose_name="사용자", max_length=100, null=True, blank=True)
    data = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)