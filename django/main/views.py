from django.shortcuts import render
from django.http import HttpResponse
from .functions import *

# 데이터 형식
# title_list = [
#    {'title': '제목1', 'count': 2},
#    {'title': '제목2', 'count': 3},
#    {'title': '제목3', 'count': 1}
# ]

# article_list = [
#     {'representative_title': '제목1', 'title': '제목1-1', 'article': '기사내용 1-1', 'link': '링크 1-1'},
#     {'representative_title': '제목1', 'title': '제목1-2', 'article': '기사내용 1-2', 'link': '링크 1-1'},
#     {'representative_title': '제목2', 'title': '제목2-1', 'article': '기사내용 2-1', 'link': '링크 2-1'},
#     {'representative_title': '제목3', 'title': '제목3-1', 'article': '기사내용 3-1', 'link': '링크 3-1'},
# ]

# 페이지에서 변수를 사용하기 위한 global 선언
# global title_list
# global sorted_article_list
# global repre_idx
# global page_list

# Create your views here.
# 초기 화면
def index(request):
    return render(request, 'templates/index.html')

# 추적 뉴스만 확인하는 화면
def tracking(request):
    title_list, article_list = get_track_news()

    page_num = 1
    page_list = list(range(1, page_num + 1))

    context = {'title_list' : title_list, 'article_list': article_list, 'page_list': page_list}
    return render(request, 'templates/tracking.html', context)

def show_news(request):
    if request.method == 'POST':
        # 제목을 사용하여 track 업데이트
        if 'title' in request.POST:
            title = request.POST['title']
            track_value = get_track_value()
            update_track_value(title, track_value)
            return HttpResponse("추적 상태가 업데이트 되었습니다")

        # 시간 + 검색
        elif request.POST['startDate'] != '' and request.POST['searchContent'] != '':
            title_list, sorted_article_list, repre_idx = get_news_w_time_w_search(request)
            
            page_num = int(len(title_list) / 10) + 1
            page_list = list(range(1, page_num + 1))

            if len(title_list) > 10:
                sorted_article_list_idx = 10
            else:
                sorted_article_list_idx = len(title_list)

            context = {'title_list' : title_list[:10], 'article_list': sorted_article_list[:repre_idx[sorted_article_list_idx-1]], 'page_list': page_list}
            return render(request, 'templates/show_news.html', context)
        # 검색
        elif request.POST['startDate'] == '' and request.POST['searchContent'] != '':
            title_list, sorted_article_list, repre_idx = get_news_wo_time_w_search(request)
            
            page_num = int(len(title_list) / 10) + 1
            page_list = list(range(1, page_num + 1))

            if len(title_list) > 10:
                sorted_article_list_idx = 10
            else:
                sorted_article_list_idx = len(title_list)

            context = {'title_list' : title_list[:10], 'article_list': sorted_article_list[:repre_idx[sorted_article_list_idx-1]], 'page_list': page_list}
            return render(request, 'templates/show_news.html', context)
        # 시간
        elif request.POST['startDate'] != '' and request.POST['searchContent'] == '':
            title_list, sorted_article_list, repre_idx = get_news_w_time_wo_search(request)
            
            page_num = int(len(title_list) / 10) + 1
            page_list = list(range(1, page_num + 1))

            if len(title_list) > 10:
                sorted_article_list_idx = 10
            else:
                sorted_article_list_idx = len(title_list)

            context = {'title_list' : title_list[:10], 'article_list': sorted_article_list[:repre_idx[sorted_article_list_idx-1]], 'page_list': page_list}
            return render(request, 'templates/show_news.html', context)
    
def show_specific_news(request, page, title_list, article_list, repre_idx, page_list):
    title_start = 10 * (page - 1)
    title_end =  10 * (page) - 1 if len(title_list) // 10 == 0 else title_start + len(title_list) // 10
    article_start, article_end = repre_idx[title_start], repre_idx[title_end]
    
    context = {'title_list' : title_list[title_start:title_end], 'article_list': article_list[article_start:article_end], 'page_list': page_list}
    return render(request, 'show_specific_news.html', context)    