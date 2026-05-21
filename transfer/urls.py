from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('apply/', views.apply_transfer, name='apply_transfer'),
    path('progress/', views.progress, name='progress'),
    path('approve/', views.pending_approvals, name='pending_approvals'),
]