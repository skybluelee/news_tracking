"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from main import views

# url 패턴을 추가하는 함수
# 첫번째 인자는 사용할 url로 기존 주소 + / + 첫번째 인자로 적용
# 두번째 인자는 views.py에서 정의된 함수
# 세번째 인자는 이름으로 optional 값이며 
# 템플릿에서 url을 동적으로 생성하거나, reverse()를 사용해 url을 역으로 해석하는데 사용
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name="index"),
    path('tracking/', views.tracking, name="tracking"),
    path('show_news/', views.show_news, name="show_news"),    
    path('show_news/<int:page>/', views.show_specific_news, name='show_specific_news'),
]
