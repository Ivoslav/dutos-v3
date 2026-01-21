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
    # 1. Дата
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = datetime.date.today()
    else:
        selected_date = datetime.date.today()

    # 2. НАРЯДИ - ТУК Е ПОПРАВКАТА (order_by)
    shifts = DutyShift.objects.filter(date=selected_date).select_related('soldier', 'duty_type').order_by(
        '-soldier__rank_group__priority', 
        '-duty_type__weight'
    )

    # 3. Отпуски
    leaves = list(Leave.objects.filter(start_date__lte=selected_date, end_date__gte=selected_date).select_related('soldier'))
    
    # 4. Всички войници (за статистиката)
    all_soldiers = Soldier.objects.filter(is_active=True).order_by('rank_group__priority', 'last_name')

    # 5. Генериране на Строевата Записка (Report)
    report = {
        '1': {'name': '1-ва Рота (ВМС)', 'class': 'primary', 'total': 0, 'present': 0, 'duty': [], 'sick': [], 'home': [], 'mission': [], 'other': []},
        '2': {'name': '2-ра Рота (Медици)', 'class': 'danger', 'total': 0, 'present': 0, 'duty': [], 'sick': [], 'home': [], 'mission': [], 'other': []},
        'young': {'name': 'Млади Курсанти', 'class': 'success', 'total': 0, 'present': 0, 'duty': [], 'sick': [], 'home': [], 'mission': [], 'other': []}
    }

    # Помощни мапове за бързодействие
    shift_map = {s.soldier_id: s for s in shifts}
    leave_map = {l.soldier_id: l for l in leaves}

    for s in all_soldiers:
        # Определяме групата
        if s.platoon == 'Млади':
            group_key = 'young'
        elif s.company == '1':
            group_key = '1'
        elif s.company == '2':
            group_key = '2'
        else:
            continue

        report[group_key]['total'] += 1
        
        # Проверяваме статуса
        if s.id in leave_map:
            l = leave_map[s.id]
            if l.leave_type == 'sick': report[group_key]['sick'].append(l)
            elif l.leave_type == 'home': report[group_key]['home'].append(l)
            elif l.leave_type == 'mission': report[group_key]['mission'].append(l)
            else: report[group_key]['other'].append(l)
        
        elif s.id in shift_map:
            sh = shift_map[s.id]
            report[group_key]['duty'].append(sh)
            
        else:
            report[group_key]['present'] += 1

    context = {
        'selected_date': selected_date,
        'shifts': shifts,     # Вече е сортирано правилно
        'report': report,
        'total_on_duty': shifts.count(),
        'all_soldiers': all_soldiers
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