from django.urls import path
from . import views  # Тук вече импортваме views от текущата папка

urlpatterns = [
    # Главна страница на графика (http://.../roster/)
    path('', views.roster_view, name='roster_home'),
    
    # Страница за статистика (http://.../roster/stats/)
    path('stats/', views.statistics_view, name='roster_stats'),
]