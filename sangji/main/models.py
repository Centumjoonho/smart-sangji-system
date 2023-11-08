from django.db import models
from django.contrib.auth.models import User



class Profile(models.Model):
    user  = models.OneToOneField(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=20)
    both = models.DateField()
    sex  = models.CharField(max_length=5)
    phone = models.CharField(max_length=20)
    email = models.CharField(max_length=100)
    picture = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{}/{}".format(self.id, self.user.username) 

class Obstacle(models.Model):
    user = models.ForeignKey(Profile,on_delete=models.CASCADE)
    step1 = models.CharField(max_length=60, null=True, blank=True)
    step2 = models.CharField(max_length=60, null=True, blank=True)
    step3 = models.CharField(max_length=60, null=True, blank=True)

class UserInfo(models.Model):
    # 유저 측정 정보
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # ROM 등장성 22.06.23
    ROM_isotonic_start_ypos = models.CharField(max_length=5, null=True, blank=True)
    ROM_isotonic_end_ypos = models.CharField(max_length=5, null=True, blank=True)
    ROM_isotonic_1rm = models.CharField(max_length=5, null=True, blank=True)
    isotonic_b_1rm = models.CharField(max_length=5, null=True, blank=True)
    isotonic_c_1rm = models.CharField(max_length=5, null=True, blank=True)
    isotonic_s_1rm = models.CharField(max_length=5, null=True, blank=True)
    # 가동범위 22.10.13
    l_start_ypos = models.CharField(max_length=5, null=True, blank=True)
    b_start_ypos = models.CharField(max_length=5, null=True, blank=True)
    c_start_ypos = models.CharField(max_length=5, null=True, blank=True)
    s_start_ypos = models.CharField(max_length=5, null=True, blank=True)
    l_end_ypos = models.CharField(max_length=5, null=True, blank=True)
    b_end_ypos = models.CharField(max_length=5, null=True, blank=True)
    c_end_ypos = models.CharField(max_length=5, null=True, blank=True)
    s_end_ypos = models.CharField(max_length=5, null=True, blank=True)

    # ROM 등척성 22.06.28
    ROM_isometric_1rm = models.CharField(verbose_name="등척성 최대근력", max_length=5, null=True, blank=True)
    isometric_b_1rm = models.CharField(verbose_name="비하인드 랫 풀 다운 등척성 최대근력", max_length=5, null=True, blank=True)
    isometric_c_1rm = models.CharField(verbose_name="체스트프레스 등척성 최대근력", max_length=5, null=True, blank=True)
    isometric_s_1rm = models.CharField(verbose_name="시티드 로우 등척성 최대근력", max_length=5, null=True, blank=True)

    # ROM 등속성 22.07.29
    ROM_isokinetic_1rm = models.CharField(verbose_name="등속성 최대근력", max_length=5, null=True, blank=True)
    isokinetic_b_1rm = models.CharField(verbose_name="비하인드 랫 풀 다운 등속성 최대근력", max_length=5, null=True, blank=True)
    isokinetic_c_1rm = models.CharField(verbose_name="체스트프레스 등속성 최대근력", max_length=5, null=True, blank=True)
    isokinetic_s_1rm = models.CharField(verbose_name="시티드 등속성 최대근력 로우", max_length=5, null=True, blank=True)

class UserMuscleFunctionRange(models.Model):
    """
    사용자 가동범위 측정 로그 22.10.13
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise_type = models.CharField(verbose_name="운동 종류", max_length=5, null=True, blank=True)
    start_positions_y = models.TextField(verbose_name="시작지점 계급값",  null=True, blank=True)
    end_positions_y = models.TextField(verbose_name="종료지점 계급값",  null=True, blank=True)
    y_positions = models.TextField(verbose_name="지점 계급값",  null=True, blank=True)
    left_angles = models.TextField(verbose_name="좌 팔꿈치 계급값",  null=True, blank=True)
    right_angles = models.TextField(verbose_name="우 팔꿈치 계급값",  null=True, blank=True)
    did_at = models.DateTimeField(verbose_name="측정일시", auto_now_add=True)

class ExternalExerciseLog(models.Model):
    """실외용 운동 기록
    
    user, datetime, repetition"""

    user = models.CharField(verbose_name="사용자", max_length=30)
    excericse = models.CharField(verbose_name="운동 종류", max_length=30)
    datetime = models.DateTimeField()
    repetition = models.IntegerField()

