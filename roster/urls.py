from django.urls import path
from . import views

urlpatterns = [
    # 1. ГЛАВНА СТРАНИЦА -> КАЛЕНДАР (Това ти липсваше!)
    path('', views.home_calendar, name='roster_home'),

    # 2. ДНЕВЕН ГРАФИК (Дежурната служба)
    path('daily/', views.roster_view, name='daily_roster'), 
    
    # 3. СТАТИСТИКА
    path('statistics/', views.statistics_view, name='roster_stats'),

    # 4. ЕКШЪНИ (Запазване на масова отпуска)
    path('batch-leave/save/', views.save_batch_leave, name='save_batch_leave'),

    # 5. ПРОФИЛИ И СМЕНИ
    path('soldier/<int:soldier_id>/', views.soldier_profile, name='soldier_profile'),
    path('swap/<int:shift_id>/', views.emergency_swap, name='emergency_swap'),
]