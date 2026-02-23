from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='roster_home'),
    path('calendar/', views.home_calendar, name='roster_calendar'),
    path('daily/', views.roster_view, name='daily_roster'),
    path('statistics/', views.statistics_view, name='roster_stats'),
    path('planner/', views.monthly_planner, name='monthly_planner'),
    path('batch-leave/save/', views.save_batch_leave, name='save_batch_leave'),
    path('soldier/<int:soldier_id>/', views.soldier_profile, name='soldier_profile'),
    path('swap/<int:shift_id>/', views.emergency_swap, name='emergency_swap'),
    path('debug/', views.debug_panel, name='debug_panel'),
    path('emergency-print/', views.emergency_list, name='emergency_print'),
    path('alert/post/', views.post_announcement, name='post_announcement'),
    path('alert/dismiss/', views.dismiss_announcement, name='dismiss_announcement'),
]