from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_calendar, name='roster_home'),
    path('daily/', views.roster_view, name='roster_daily'), 
    path('statistics/', views.statistics_view, name='roster_stats'),
    path('soldier/<int:soldier_id>/', views.soldier_profile, name='soldier_profile'),
    path('swap/<int:shift_id>/', views.emergency_swap, name='emergency_swap'),
]