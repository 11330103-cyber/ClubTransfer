from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('apply/', views.apply_transfer, name='apply_transfer'),
    path('progress/', views.progress, name='progress'),
    #path('approve/<int:request_id>/', views.approve_request, name='approve_request'),
    path('approves/',views.approve_request,name='approve_list'),
]