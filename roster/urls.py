from django.urls import path
from . import views

urlpatterns = [
    # 1. ГЛАВНА СТРАНИЦА -> ВЕЧЕ Е ДАШБОРДЪТ
    path('', views.dashboard_view, name='roster_home'),

    # 2. Календарът отива на свой адрес
    path('calendar/', views.home_calendar, name='roster_calendar'),

    # ... останалите пътища са същите ...
    path('daily/', views.roster_view, name='daily_roster'),
    path('statistics/', views.statistics_view, name='roster_stats'),
    path('batch-leave/save/', views.save_batch_leave, name='save_batch_leave'),
    path('soldier/<int:soldier_id>/', views.soldier_profile, name='soldier_profile'),
    path('swap/<int:shift_id>/', views.emergency_swap, name='emergency_swap'),
    path('debug/', views.debug_panel, name='debug_panel'),
]