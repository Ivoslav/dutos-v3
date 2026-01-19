from django.shortcuts import render, get_object_or_404, redirect
from .models import DutyShift, DutyType, Soldier # <--- Важно: Трябва да импортнем и Soldier!
from .forms import DutyShiftForm
import datetime

# --- ФУНКЦИЯ 1: ГРАФИК (Това ти липсваше) ---
def roster_view(request):
    # 1. Взимаме днешната дата
    date_str = request.GET.get('date')
    if date_str:
        selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        selected_date = datetime.date.today()

    # 2. ПРОМЯНА: Сортираме по Старшинство на курса (5-ти най-горе), после по тежест на наряда
    shifts = DutyShift.objects.filter(date=selected_date).order_by(
        '-soldier__rank_group__priority',  # Групиране (5 -> 1)
        '-duty_type__weight'               # Най-тежките наряди най-горе
    )

    context = {
        'selected_date': selected_date,
        'shifts': shifts,
    }
    return render(request, 'roster/daily_roster.html', context)

# --- ФУНКЦИЯ 2: СТАТИСТИКА (Новата) ---
def statistics_view(request):
    # 1. ТОЧКИ (Leaderboard) - Без промяна
    leaderboard = Soldier.objects.filter(is_active=True).order_by('rank_group__priority', '-score')

    # 2. ПОДГОТОВКА ЗА КОЛОНИТЕ (НОВО!)
    
    # Колона 1: 1-ва Рота (БЕЗ младите)
    company_1 = Soldier.objects.filter(company='1', is_active=True)\
        .exclude(platoon='Млади')\
        .order_by('-rank_group__priority', 'last_name')

    # Колона 2: 2-ра Рота (БЕЗ младите)
    company_2 = Soldier.objects.filter(company='2', is_active=True)\
        .exclude(platoon='Млади')\
        .order_by('-rank_group__priority', 'last_name')

    # Колона 3: Млади Курсанти (Всички, независимо от ротата, защото са отделен взвод)
    young_cadets = Soldier.objects.filter(platoon='Млади', is_active=True)\
        .order_by('faculty_number') # Тях ги подреждаме по номер, защото са с равни звания

    # Другите групирания
    by_crew = Soldier.objects.filter(is_active=True).exclude(crew="").order_by('crew', 'last_name')
    by_class = Soldier.objects.filter(is_active=True).order_by('class_section', 'faculty_number')

    context = {
        'leaderboard': leaderboard,
        'company_1': company_1,      # <--- Пращаме списък 1
        'company_2': company_2,      # <--- Пращаме списък 2
        'young_cadets': young_cadets,# <--- Пращаме списък 3
        'by_crew': by_crew,
        'by_class': by_class,
    }
    return render(request, 'roster/statistics.html', context)


def soldier_profile(request, soldier_id):
    soldier = get_object_or_404(Soldier, id=soldier_id)
    
    # 1. История на нарядите (Последните първи)
    history = DutyShift.objects.filter(soldier=soldier).order_by('-date')

    # 2. Обработка на формата за НОВ наряд
    if request.method == 'POST':
        form = DutyShiftForm(request.POST)
        if form.is_valid():
            shift = form.save(commit=False)
            shift.soldier = soldier # Слагаме войника автоматично
            shift.save()
            
            # Добавяме точките веднага
            soldier.score += shift.duty_type.weight
            soldier.save()
            
            # Връщаме се на статистиката
            return redirect('roster_stats')
    else:
        form = DutyShiftForm()

    context = {
        'soldier': soldier,
        'history': history,
        'form': form,
    }
    # Връщаме само парче HTML, не цяла страница!
    return render(request, 'roster/modal_profile.html', context)