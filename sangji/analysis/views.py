from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.conf import settings
from django.core.paginator import Paginator

from app_socket.models import *

def index(request):
    return render(request, 'main/analysis/index.html')

def anaylsis_user(request):
    template = settings.TEMPLATES_ROOT.get('ANALYSIS_USER') + '/index.html'
    # Number of users to display per page
    view_length = request.GET.get('view_length', 10)  # Default to 10 users per page
    page_number = request.GET.get('page', 1)  # Default to the first page

    users = User.objects.all()

    paginator = Paginator(users, view_length)
    page_obj = paginator.get_page(page_number)

    for user in page_obj:
        results = MuscleFunctionLogData.objects.filter(user_id=user)
        if not results:
            setattr(user, 'last_measure', "운동 이력이 없습니다.")
        else:
            setattr(user, 'last_measure', results.last().musclefunction_infomation_str())

    return render(request, template, {
        'page_obj': page_obj,
        'users': page_obj.object_list,
    })

def search_users(request):
    template = settings.TEMPLATES_ROOT.get('ANALYSIS_USER') + '/user_items.html'
    search_keyword = request.GET.get('search_keyword')

    view_length = request.GET.get('view_length', 10)  # Default to 10 users per page
    page_number = request.GET.get('page', 1)  # Default to the first page

    users = User.objects.filter(username__icontains=search_keyword)

    paginator = Paginator(users, view_length)
    page_obj = paginator.get_page(page_number)

    return render(request, template, {
        'page_obj': page_obj,
        'users': page_obj.object_list,
    })

def analysis(request):
    infomations = UserInfomation.objects.all().order_by('-pk')
    
    return render(request, 'main/analysis/index.html', {
        'infomations' : infomations
    })

def user_exercise_index(request):
    """
    사용자 운동 조회
    """
    template = settings.TEMPLATES_ROOT.get('ANALYSIS_USER') + '/exercise_index.html'
    view_length = request.GET.get('view_length', 
                                  settings.PAGINATION_OPTIONS.get('VIEW_LENGTH'))  # Default to 10 users per page
    page_number = request.GET.get('page', 1)  # Default to the first page

    musclefunction_data = MuscleFunctionLogData.objects.all() \
                                                       .order_by('-created_at')

    paginator = Paginator(musclefunction_data, view_length)
    page_obj = paginator.get_page(page_number)
    
    return render(request, template, {
        'title' : "유저 운동 조회",
        'page_obj' : page_obj
    })

def user_exercise_detail(request, log_pk):
    """
    사용자 운동 상세 조회
    """
    template = settings.TEMPLATES_ROOT.get('ANALYSIS_USER') + '/exercise_detail.html'
    
    log = get_object_or_404(MuscleFunctionLogData, pk=log_pk)
    user = get_object_or_404(User, username=log.user_id)
    
    return render(request, template, {
        'title' : '유저 운동 결과 조회',
        'log' : log,
        'user' : user
    })


def user_report_index(request, user_id):
    template = settings.TEMPLATES_ROOT.get('ANALYSIS_REPORT') + '/index.html'
    user = get_object_or_404(User, username=user_id)
    print(user)
    
    return render(request, template, {
        'user' : user,
    })

def user_report_isometric(request, user_id):
    template = settings.TEMPLATES_ROOT.get('ANALYSIS_REPORT') + '/isometric.html'
    user = get_object_or_404(User, username=user_id)
    print(user)
    
    return render(request, template, {
        'user' : user,
    })
