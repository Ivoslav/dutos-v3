from django.urls import path
from . import views

urlpatterns = [
    # 1. График (Това име 'daily_roster' се търси от HTML-а)
    path('daily/', views.roster_view, name='daily_roster'), 
    
    # 2. Статистика (където сложихме новия таб)
    path('statistics/', views.statistics_view, name='roster_stats'),

    # 3. НОВО: Линкът, който записва масовата отпуска
    path('batch-leave/save/', views.save_batch_leave, name='save_batch_leave'),

    # 4. Профил на войник
    path('soldier/<int:soldier_id>/', views.soldier_profile, name='soldier_profile'),
    
    # 5. Смяна
    path('swap/<int:shift_id>/', views.emergency_swap, name='emergency_swap'),

    # Redirect от главната страница на roster към графика
    path('', views.roster_view, name='roster_home'),
]