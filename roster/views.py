from django.shortcuts import render
from .models import DutyShift, DutyType, Soldier # <--- Важно: Трябва да импортнем и Soldier!
import datetime

# --- ФУНКЦИЯ 1: ГРАФИК (Това ти липсваше) ---
def roster_view(request):
    # 1. Взимаме днешната дата или избрана от потребителя
    date_str = request.GET.get('date')
    if date_str:
        selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        selected_date = datetime.date.today()

    # 2. Взимаме нарядите за тази дата
    shifts = DutyShift.objects.filter(date=selected_date).order_by('duty_type__weight')

    # 3. Пращаме ги към HTML шаблона
    context = {
        'selected_date': selected_date,
        'shifts': shifts,
    }
    return render(request, 'roster/daily_roster.html', context)

# --- ФУНКЦИЯ 2: СТАТИСТИКА (Новата) ---
def statistics_view(request):
    # 1. ТОЧКИ (Сортирани от най-много към най-малко)
    leaderboard = Soldier.objects.filter(is_active=True).order_by('-score')

    # 2. ЗА ГРУПИРАНЕ (Трябва да са сортирани, за да работи групирането в шаблона)
    by_company = Soldier.objects.filter(is_active=True).order_by('company', 'rank_group')
    by_crew = Soldier.objects.filter(is_active=True).exclude(crew="").order_by('crew', 'last_name')
    by_class = Soldier.objects.filter(is_active=True).order_by('class_section', 'faculty_number')

    context = {
        'leaderboard': leaderboard,
        'by_company': by_company,
        'by_crew': by_crew,
        'by_class': by_class,
    }
    return render(request, 'roster/statistics.html', context)