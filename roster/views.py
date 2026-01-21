from django.shortcuts import render, get_object_or_404, redirect
from datetime import timedelta # <--- ВАЖНО: Добави това!
from .models import DutyShift, DutyType, Soldier, Leave # <--- Важно: Трябва да импортнем и Soldier!
from .forms import DutyShiftForm
from django.db.models import Count, Q # <--- Трябва ни за броенето
from django.contrib import messages    # <--- За съобщения "Успешна смяна"
import calendar
import datetime

# --- ФУНКЦИЯ 1: ГРАФИК (Това ти липсваше) ---
def roster_view(request):
    # ... (стандартното начало за датата) ...
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = datetime.date.today()
    else:
        selected_date = datetime.date.today()

    # 1. Наряди (Хората в строя)
    shifts = DutyShift.objects.filter(date=selected_date).order_by(
        '-soldier__rank_group__priority', 
        '-duty_type__weight'
    )

    # 2. Отсъстващи (Хората извън строя)
    absentees = Leave.objects.filter(
        start_date__lte=selected_date, 
        end_date__gte=selected_date
    ).select_related('soldier').order_by('leave_type', 'soldier__last_name')

    # --- НОВО: Изчисляваме дните и броим по роти ---
    absent_c1 = 0
    absent_c2 = 0
    absent_young = 0

    # Обработваме списъка, за да добавим полезна инфо
    for leave in absentees:
        # Изчисляваме оставащи дни (чисто число)
        delta = leave.end_date - selected_date
        leave.days_left = delta.days 
        
        # Броим ги
        if leave.soldier.platoon == 'Млади':
            absent_young += 1
        elif leave.soldier.company == '1':
            absent_c1 += 1
        elif leave.soldier.company == '2':
            absent_c2 += 1

    # 3. Статистика за НАРЯДИТЕ (както преди)
    platoon_stats = shifts.values('soldier__platoon').annotate(count=Count('id')).order_by('soldier__platoon')
    
    duty_c1 = shifts.filter(soldier__company='1').count()
    duty_c2 = shifts.filter(soldier__company='2').count()
    duty_young = shifts.filter(soldier__platoon='Млади').count()

    context = {
        'selected_date': selected_date,
        'shifts': shifts,
        'platoon_stats': platoon_stats,
        
        # Пращаме разбивката: Наряд / Отсъстващи
        'c1_stats': {'duty': duty_c1, 'absent': absent_c1},
        'c2_stats': {'duty': duty_c2, 'absent': absent_c2},
        'young_stats': {'duty': duty_young, 'absent': absent_young},
        
        'absent_count': absentees.count(),
        'absentees': absentees,
        'total_on_duty': shifts.count(),
        'all_soldiers': Soldier.objects.filter(is_active=True).order_by('last_name')
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
    today = datetime.date.today()

    # 1. Списъци за визуализация
    upcoming_shifts = DutyShift.objects.filter(soldier=soldier, date__gte=today).order_by('date')
    past_shifts = DutyShift.objects.filter(soldier=soldier, date__lt=today).order_by('-date')
    leaves = Leave.objects.filter(soldier=soldier).order_by('-start_date')

    form = DutyShiftForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            new_date = form.cleaned_data['date']
            
            # --- ПРОВЕРКА 1: ОТПУСК ---
            on_leave = Leave.objects.filter(
                soldier=soldier,
                start_date__lte=new_date,
                end_date__gte=new_date
            ).exists()

            # --- ПРОВЕРКА 2: ДУБЛИРАНЕ (Вече има наряд днес?) ---
            has_shift_today = DutyShift.objects.filter(
                soldier=soldier, 
                date=new_date
            ).exists()

            # --- ПРОВЕРКА 3: УМОРА (Бил ли е наряд вчера?) ---
            yesterday = new_date - timedelta(days=1)
            has_shift_yesterday = DutyShift.objects.filter(
                soldier=soldier, 
                date=yesterday
            ).exists()

            # --- ЛОГИКА ЗА СПИРАНЕ ---
            if on_leave:
                form.add_error('date', '⛔ Грешка: Войникът е в отпуск на тази дата!')
            
            elif has_shift_today:
                form.add_error('date', '⛔ Грешка: Вече има назначен наряд за този ден!')
                
            elif has_shift_yesterday:
                form.add_error('date', '⛔ Грешка: Войникът е уморен (наряд вчера)!')

            else:
                # Всичко е чисто -> Записваме!
                shift = form.save(commit=False)
                shift.soldier = soldier
                shift.save()
                
                soldier.score += shift.duty_type.weight
                soldier.save()
                
                # Ако заявката е AJAX (от поп-ъпа), ще върне redirect, който JS ще хване
                return redirect('roster_stats')

    context = {
        'soldier': soldier,
        'upcoming_shifts': upcoming_shifts,
        'past_shifts': past_shifts,
        'leaves': leaves,
        'form': form,
    }
    return render(request, 'roster/modal_profile.html', context)

def home_calendar(request):
    today = datetime.date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    prev_date = datetime.date(year, month, 1) - timedelta(days=1)
    next_date = datetime.date(year, month, 1) + timedelta(days=32)
    next_date = next_date.replace(day=1)

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)

    shifts = DutyShift.objects.filter(date__year=year, date__month=month)

    shifts_by_day = {}
    for shift in shifts:
        day = shift.date.day
        if day not in shifts_by_day:
            shifts_by_day[day] = []
        shifts_by_day[day].append(shift)

    # --- НОВА ЛОГИКА: Броим разхода по роти ---
    # Резултатът ще е: { 21: {'c1': 5, 'c2': 3}, 22: ... }
    stats_by_day = {}
    
    for day, day_shifts in shifts_by_day.items():
        count_c1 = 0
        count_c2 = 0
        count_young = 0
        for s in day_shifts:
            if s.soldier.platoon == 'Млади':
                count_young += 1
            elif s.soldier.company == '1':
                count_c1 += 1
            elif s.soldier.company == '2':
                count_c2 += 1
        
        stats_by_day[day] = {
                    'c1': count_c1, 
                    'c2': count_c2, 
                    'young': count_young
                }
        
    month_name = datetime.date(year, month, 1).strftime('%B %Y')

    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'month_days': month_days,
        'shifts_by_day': shifts_by_day,
        'stats_by_day': stats_by_day, # <--- Пращаме новата статистика
        'prev_year': prev_date.year,
        'prev_month': prev_date.month,
        'next_year': next_date.year,
        'next_month': next_date.month,
        'today': today,
    }
    return render(request, 'roster/home_calendar.html', context)

def emergency_swap(request, shift_id):
    shift = get_object_or_404(DutyShift, id=shift_id)
    
    if request.method == 'POST':
        new_soldier_id = request.POST.get('new_soldier')
        reason = request.POST.get('reason')
        
        new_soldier = get_object_or_404(Soldier, id=new_soldier_id)
        old_soldier = shift.soldier
        
        # 1. Махаме точките на стария
        old_soldier.score -= shift.duty_type.weight
        if old_soldier.score < 0: old_soldier.score = 0
        old_soldier.save()
        
        # 2. Сменяме човека в наряда
        shift.soldier = new_soldier
        shift.save()
        
        # 3. Даваме точките на новия
        new_soldier.score += shift.duty_type.weight
        new_soldier.save()
        
        messages.success(request, f"🔄 Смяна успешна: {old_soldier.last_name} -> {new_soldier.last_name}")
        
    # Връщаме се обратно на датата на наряда
    return redirect(f"/roster/daily/?date={shift.date}")