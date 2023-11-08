import datetime

from django.shortcuts import render
from app_socket.models import *

def analysis(request):
    infomations = UserInfomation.objects.all().order_by('-pk')
    
    return render(request, 'main/analysis/index.html', {
        'infomations' : infomations
    })

def exercise_log(request, uuid):
    logs = ExerciseStampLog.objects.filter(uuid=uuid)
    return render(request, 'main/analysis/detail.html', {
        'logs' : logs
    })

def mole_log_main(request):
    moledatas = MoleDataLog.objects.values('game_id', 'username').distinct()
    for moledata in moledatas:
        datas = MoleDataLog.objects.filter(game_id=moledata.get('game_id'))
        try:
            # setattr(moledata, 'did_at', datas.last().timestamp)
            moledata['did_at'] = datetime.datetime.fromtimestamp(int(datas.last().timestamp) / 1000)
        except Exception as err:
            print(err)
            # setattr(moledata, 'did_at', None)
            moledata['did_at'] = None

    return render(request, 'main/mole/index.html', {
        'moledatas' : moledatas
    })

def mole_log_detail(request, game_id):
    moledatas = MoleDataLog.objects.filter(game_id=game_id, angle_1__isnull=True) # 각도가 없는 것 (게임 로그)
    moledatas_angle = MoleDataLog.objects.filter(game_id=game_id, angle_1__isnull=False)
    mole_analysis_data = {
        'hit_count' : None,
        'pane_count' : None,
        'mole_position' : [],
        'mole_show_time' : {}, # 등장 시간
        'mole_catched_time' : [],
        'mole_pane' : {},
        "avg_response_time" : 0,# 평균 반응시간
        "avg_pane" : 0 # 평균 pane
    }
    # 상세 로그
    for moledata in moledatas:
        try:
            setattr(moledata, 'timeStr', datetime.datetime.fromtimestamp(int(moledata.timestamp)/1000))
        except Exception as err:
            setattr(moledata, 'timeStr', '0')
    
    # 협응 게임 분석
    if moledatas:
        total_time = int(moledatas.last().timestamp) - int(moledatas.first().timestamp)

        # 1. 잡은 두더지 수
        mole_analysis_data['hit_count'] = int(moledatas.last().hit_count)
        # 2. 전체 Pane 수
        mole_analysis_data['pane_count'] = int(moledatas.last().pane_count)

        for moledata in moledatas: 
            hitcount = int(moledata.hit_count)
            # 3. 각각 두더지를 잡는데 걸린 시간
            """
            mole_catched_time : {
                0 : 1647067056031 0번이 나온 시간
                1 : 1647067060640 1번이 나온 시간 (1번 나온 시간 - 0번 나온 시간 = 0번 잡은 시간)
                2 : 1647067065564
            }
            """
            if not hitcount in mole_analysis_data['mole_show_time']:
                mole_analysis_data['mole_show_time'][hitcount] = int(moledata.timestamp)
                if hitcount != 0:
                    # 첫 두더지가 아니면 잡은 시간 계산
                    timestamp_diff = int(moledata.timestamp) - mole_analysis_data['mole_show_time'][hitcount-1]
                    mole_analysis_data['mole_catched_time'].append(
                        (timestamp_diff, (timestamp_diff // 1000) )
                    )
            
            # 4. 각각 두더지가 나타났던 좌표
            # if not moledata.mole_position in mole_analysis_data['mole_position']: => 같은 좌표가 있을 경우 처리 못함
            if len(mole_analysis_data['mole_position']) == 0 or mole_analysis_data['mole_position'][ len(mole_analysis_data['mole_position'])-1 ] != moledata.mole_position: 
                mole_analysis_data['mole_position'].append(moledata.mole_position)

            # 5. 각각 두더지를 잡을 때 Pane 수
            if not hitcount in mole_analysis_data['mole_pane']:
                mole_analysis_data['mole_pane'][hitcount] = []
            mole_analysis_data['mole_pane'][hitcount].append(moledata.pane_count)

        # 6. 평균 반응시간
        mole_analysis_data['avg_response_time'] = total_time // mole_analysis_data['hit_count']
        # 7. 평균 Pane
        mole_analysis_data['avg_pane'] = mole_analysis_data['pane_count'] / mole_analysis_data['hit_count']

        # 각도 데이터
        for moledata_angle in moledatas_angle: 
            try:
                setattr(moledata_angle, 'timeStr', datetime.datetime.fromtimestamp(int(moledata_angle.timestamp)/1000))
            except Exception as err:
                setattr(moledata_angle, 'timeStr', '0')

        print(mole_analysis_data)

    return render(request, 'main/mole/detail.html', {
        'moledatas' : moledatas,
        'mole_analysis_data' : mole_analysis_data,
        'moledatas_angle' : moledatas_angle
    })