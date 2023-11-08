import unittest
import json
import csv
import numpy as np
import pandas as pd
from deepface import DeepFace

from django.test import TestCase
from django.contrib.auth.models import User

from app_socket.models import *
from main.models import (
    UserMuscleFunctionRange, 
    UserMuscleFunctionRange, 
    Profile,
    UserInfo
)
from main.face_recognition_module import get_user_name_from_file

class CreateUserTestCase(unittest.TestCase):
    def test_create_user(self):
        for i in range(100):
            user = User.objects.create_user(
                username = f's{i+1}',
                password = 's'
            )

            profile = Profile.objects.create(
                user = user,
                name = '',
                both = '2023-06-26',
                sex  = '',
                phone = '',
                email = '')

            userinfo = UserInfo.objects.create(
                user=user,
            )

    def test_update_password(self):
        for user in User.objects.all():
            user.set_password('nf1yfa23')
            user.save()


class MuscleFunctionTestCase(unittest.TestCase):
    def test_musclefunction_to_csv(self):
        # with open('./muscle_function_range.csv', 'w', newline='') as _file: 
        #     writer = csv.writer(_file)
        HEADER = ['USER', 'DATETIME', 'TYPE', '시작지점', '종료지점', '지점 계급값', '좌 팔꿈치 계급값', '우 팔꿈치 계급값']
        data = UserMuscleFunctionRange.objects.all().order_by('-pk')
        with open('./muscle_function_range.csv', 'w', newline='', encoding='utf-8-sig') as _file: 
            writer = csv.writer(_file)
            writer.writerow(HEADER)
            for d in data: 
                row = [
                    d.user.username,
                    d.did_at,
                    d.exercise_type,
                    d.start_positions_y,
                    d.end_positions_y,
                    d.y_positions,
                    d.left_angles,
                    d.right_angles,
                ]
                writer.writerow(row)


    def test_isotonic_muscle_function_to_csv(self):
        HEADER = ['USER', 'DATETIME', 'TYPE', 'HAND TYPE', 'EXERCISE TYPE']
        with open('./isotonic.csv', 'w', newline='') as _file: 
            writer = csv.writer(_file)

            data = MuscleFunctionLogData.objects.filter(exercise_type='musclefunction_isotonic') \
                                                .order_by('-pk')
            for dt in data:
                if dt.extra is None: continue
                # print(dt.extra)
                try:
                    # {'speed': '120', 'set': '3', 'count': '3', 'hand_type': 'left_hand', 'exercise': 'latpulldown'}
                    extra = json.loads(dt.extra) 
                    log_data = json.loads(dt.log)

                    row = [
                        dt.user_id,
                        dt.created_at.strftime('%Y-%m-%d %H:%M'),
                        dt.exercise_type,
                    ] + [
                        extra[value] for value in extra
                    ]

                    writer.writerow(HEADER)
                    writer.writerow(row)
                    writer.writerow([])
                    writer.writerow(['last weight(KG)', log_data.get('lastSuccessWeight')])
                    writer.writerow([])
                    writer.writerow([])

                except Exception as err:
                    pass

    def test_isokinetic_muscle_function_to_csv(self):
        HEADER = ['USER', 'DATETIME', 'TYPE', 'SPEED', 'SET', 'COUNT', 'HAND TYPE', 'EXERCISE TYPE']
        with open('./isokinetic.csv', 'w', newline='') as _file: 
            writer = csv.writer(_file)

            data = MuscleFunctionLogData.objects.filter(exercise_type='musclefunction_isokinetic') \
                                                .order_by('-pk')

            for dt in data:
                if dt.extra is None: continue
                # print(dt.extra)
                try:
                    # {'speed': '120', 'set': '3', 'count': '3', 'hand_type': 'left_hand', 'exercise': 'latpulldown'}
                    extra = json.loads(dt.extra) 
                    log_data = json.loads(dt.log)

                    row = [
                        dt.user_id,
                        dt.created_at.strftime('%Y-%m-%d %H:%M'),
                        dt.exercise_type,
                    ] + [
                        extra[value] for value in extra
                    ]

                    # {'position': 349, 'value': 4.035}
                    set_index, position, value = [], [], []

                    # print('first len:', len(log_data))
                    for i, set_data in enumerate(log_data): # set
                        for set_i, t in enumerate(set_data): # count
                            for z in t:
                                set_index.append(set_i+1)
                                position.append(z.get('position'))
                                value.append(z.get('value'))

                    writer.writerow(HEADER)
                    writer.writerow(row)
                    writer.writerow([])
                    writer.writerow(['count'] + set_index)
                    writer.writerow(['position'] + position)
                    writer.writerow(['value(kg)'] + value) 
                    writer.writerow(['MAX KG'] + [max(value)]) 
                    writer.writerow(['MIN KG'] + [min(value)]) 
                    writer.writerow(['AVG KG'] + [np.mean(value)]) 
                    writer.writerow([])
                    writer.writerow([])

                except Exception as err:
                    pass

    def test_isometric_muscle_function_to_csv(self):
        HEADER = ['USER', 'DATETIME', 'TYPE', 'LEVEL', 'TIME', 'HAND TYPE', 'EXERCISE TYPE']
        with open('./isometric.csv', 'w', newline='') as _file: 
            writer = csv.writer(_file)

            print(self.__str__())
            # data = MuscleFunctionLogData.objects.all()
            data = MuscleFunctionLogData.objects.filter(exercise_type='musclefunction_isometric') \
                                                .order_by('-pk')
            self.assertFalse(len(data) == 0)
            final_rows = []
            for dt in data:
                if dt.extra is None: continue
                # {'level': '6', 'time': '10', 'hand_type': 'both_hand', 'exercise': 'blatpulldown'}
                extra = json.loads(dt.extra) 
                log_data = json.loads(dt.log)
                if extra.get('hand_type') is None: continue
                
                row = [
                    dt.user_id,
                    dt.created_at.strftime('%Y-%m-%d %H:%M'),
                    dt.exercise_type,
                ] + [
                    extra[value] for value in extra
                ]

                time, value = [], []
            
                for i, set_data in enumerate(log_data):
                    for t in set_data:
                        print(i, t)
                        time.append(t.get('time'))
                        value.append(t.get('value'))
                
                writer.writerow(HEADER)
                writer.writerow(row)
                writer.writerow([])
                writer.writerow(['time(ms)'] + time)
                writer.writerow(['value(kg)'] + value) 
                writer.writerow(['MAX KG'] + [max(value)]) 
                writer.writerow(['MIN KG'] + [min(value)]) 
                writer.writerow(['AVG KG'] + [np.mean(value)]) 
                writer.writerow([])
                writer.writerow([])

class DataToExcelTestCase(unittest.TestCase):
    def export_header_name(self, model, exclude_fields, extra_fields=None):
        fields = [field.name for field in model._meta.fields 
                  if not field.name in exclude_fields]
        
        if extra_fields:
            fields += extra_fields
        
        return fields
    

    def export_exclude_fields(self, model):
        if model == Profile:
            return ['picture']
    
        if model == UserInfomation:
            image_fields = [field.name 
                            for field in UserInfomation._meta.fields
                            if 'image' in field.name]
            return image_fields
        
        if model == MoleDataLog:
            return ['angle_1', 'angle_2']
    
        return []

    def process_field(self, obj, col, default=""):
        # this called because some field need to process for processing
        value = getattr(obj, col, default)

        if obj._meta.model == ROMLogData and col == 'data':
            return json.loads(value)
        
        return value
    
    def test_romlogdata_export_to_excel(self):
        userinfo = ROMLogData.objects.all() \
                                  .order_by('-pk')
        export_exculde_fields = self.export_exclude_fields(ROMLogData)
        table_header = self.export_header_name(ROMLogData, 
                                               export_exculde_fields)
        
        with open(f'./{self.__str__()}.csv', 'w', newline='', encoding='utf-8-sig') as _file: 
            writer = csv.writer(_file)  
            writer.writerow(table_header)

            for info in userinfo:
                row = []
                for col in table_header:
                    if not col in export_exculde_fields:
                        value = self.process_field(info, col)
                        if type(value) is list:
                            row += value
                            
                            if len(value) != 3:
                                for _ in range(len(value), 3):
                                    row.append('')
                        else:
                            row.append(value)
                writer.writerow(row)

                # writer.writerow([self.process_field if col == 'data' else getattr(info, col, '')
                #                 for col in table_header 
                #                 if not col in export_exculde_fields])


    def test_profiles_export_to_excel(self):
        # this can describe business logic for this. 

        # split this into selector
        profiles = Profile.objects.all() \
                                  .prefetch_related('obstacle_set') \
                                  .order_by('-pk')
        
        # this can be changed in the futer -> encapsulation with func and cls
        # i selected to used function for this encapsulation
        extra_fields = ['obstacle']
        export_exculde_fields = self.export_exclude_fields(Profile)
        table_header = self.export_header_name(Profile, 
                                               export_exculde_fields, 
                                               extra_fields)
        
        with open('./profile.csv', 'w', newline='', encoding='utf-8-sig') as _file: 
            writer = csv.writer(_file)  
            writer.writerow(table_header)

            for profile in profiles:
                if hasattr(profile, 'obstacle_set'):
                    write_row = [getattr(profile, col, '') 
                                for col in table_header 
                                if not col in export_exculde_fields]
                    write_row += ['{}/{}/{}'.format(obs.step1, obs.step2, obs.step3)
                                  for obs in profile.obstacle_set.all()]
                    writer.writerow(write_row)
                else:
                    writer.writerow([getattr(profile, col, '') 
                                    for col in table_header 
                                    if not col in export_exculde_fields])

    def test_uesrinfomation_export_to_excel(self):
        userinfo = UserInfomation.objects.all() \
                                  .order_by('-pk')
        export_exculde_fields = self.export_exclude_fields(UserInfomation)
        table_header = self.export_header_name(UserInfomation, 
                                               export_exculde_fields)

        with open(f'./{self.__str__()}.csv', 'w', newline='', encoding='utf-8-sig') as _file: 
            writer = csv.writer(_file)  
            writer.writerow(table_header)

            for info in userinfo:
                writer.writerow([getattr(info, col, '') 
                                for col in table_header 
                                if not col in export_exculde_fields])

    def test_molegame_export_to_excel(self):
        romdata = MoleDataLog.objects.all() \
                                    .order_by('-pk')
        export_exculde_fields = self.export_exclude_fields(MoleDataLog)
        table_header = self.export_header_name(MoleDataLog, 
                                               export_exculde_fields)

        with open(f'./{self.__str__()}.csv', 'w', newline='', encoding='utf-8-sig') as _file: 
            writer = csv.writer(_file)  
            writer.writerow(table_header)

            for info in romdata:
                writer.writerow([getattr(info, col, '') 
                                for col in table_header 
                                if not col in export_exculde_fields])
                

class FaceVerification(unittest.TestCase):
    def test_verify_two_images_not_same(self):
        result = DeepFace.verify(img1_path = "/home/marketian/project/sangji/media/user_face/jk.jpg", 
                                 img2_path = "/home/marketian/project/sangji/media/user_face/naeun.jpg")
        isVerified = result['verified']
        self.assertFalse(isVerified)

    def test_verify_two_images_same(self):
        result = DeepFace.verify(img1_path = "/home/marketian/project/sangji/media/user_face/naeun.jpg", 
                                 img2_path = "/home/marketian/project/sangji/media/user_face/naeun2.jpg")
        isVerified = result['verified']
        self.assertTrue(isVerified)
    
    def test_deepface_face_recogntion(self):
        """
        Deepface Module issue that
        1. face recogntion : find verifcation someone in DB dir.
        2. face verificatin : compare two faces for checking whether those are same.
        """
        # dfs = DeepFace.find(img_path = "img1.jpg", db_path = "C:/workspace/my_db")
        dir_path = "/home/marketian/project/sangji/media/user_face"
        test_user_img_path = "/home/marketian/project/sangji/media/user_face/jk.jpg"
        result = DeepFace.find(img_path=test_user_img_path, db_path=dir_path, enforce_detection=False)
    
        if len(result) > 0:
            for i, row in result[0].iterrows():
                name = get_user_name_from_file(row['identity']) # /home/marketian/project/sangji/media/user_face/jk.jpg
                print(name)

        
class ModelInfomation(TestCase):

    def test_get_table_info(self):
        import openpyxl
        import os
        # Create a new Workbook
        wb = openpyxl.Workbook()

        # Get all the models from the installed apps
        import django.apps
        models = django.apps.apps.get_models()

        # Iterate over the models and create a sheet for each model
        for model in models:
            ws = wb.create_sheet(title=model.__name__)  # Create a sheet with the model name
            ws.append(["Table Name", model.__name__])  # Add model name as a header
            ws.append(["name", "type", "constraint"])
            for field in model._meta.get_fields():
                ws.append([field.name, field.get_internal_type(), ])  # Add field names as a row

        # Remove the default sheet created by openpyxl
        default_sheet = wb['Sheet']
        wb.remove(default_sheet)

        # Specify the file path to save the XLSX file
        file_path = os.path.join('./model_info.xlsx')

        # Save the workbook to the file path
        wb.save(file_path)
