from django.urls import path
from . import views  # Тук вече импортваме views от текущата папка

urlpatterns = [
    # СЕГА 'home_calendar' Е НАЧАЛНАТА СТРАНИЦА:
    path('', views.home_calendar, name='roster_home'),
    
    # Старият график го местим на /daily/ (или го оставяме достъпен през календара)
    path('daily/', views.roster_view, name='roster_daily'), 
    
    path('stats/', views.statistics_view, name='roster_stats'),
    path('soldier/<int:soldier_id>/', views.soldier_profile, name='soldier_profile'),
]