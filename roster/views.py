from django.shortcuts import render, get_object_or_404, redirect
from datetime import timedelta # <--- ВАЖНО: Добави това!
from .models import DutyShift, DutyType, Soldier, Leave # <--- Важно: Трябва да импортнем и Soldier!
from .forms import DutyShiftForm
import calendar
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
    # 1. Определяме година и месец (от URL или текущи)
    today = datetime.date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # 2. Изчисляваме Предишен и Следващ месец (за бутоните)
    prev_date = datetime.date(year, month, 1) - timedelta(days=1)
    next_date = datetime.date(year, month, 1) + timedelta(days=32)
    next_date = next_date.replace(day=1)

    # 3. Взимаме матрицата на месеца (Списък от седмици, където 0 е празен ден)
    cal = calendar.Calendar(firstweekday=0) # 0 = Понеделник
    month_days = cal.monthdayscalendar(year, month)

    # 4. Взимаме всички наряди за този месец
    shifts = DutyShift.objects.filter(date__year=year, date__month=month)

    # 5. Групираме нарядите по дни: { 21: [Shift1, Shift2...], 22: [...] }
    shifts_by_day = {}
    for shift in shifts:
        day = shift.date.day
        if day not in shifts_by_day:
            shifts_by_day[day] = []
        shifts_by_day[day].append(shift)

    # 6. Търсим кой е ДБПК за всеки ден (за да го покажем на календара)
    # Правим речник: { 21: "Мичман Иванов", 22: "..." }
    dbpk_by_day = {}
    for day, day_shifts in shifts_by_day.items():
        for s in day_shifts:
            if 'ДБПК' in s.duty_type.name and 'ПДБПК' not in s.duty_type.name:
                dbpk_by_day[day] = f"{s.soldier.rank_title} {s.soldier.last_name}"
                break

    month_name = datetime.date(year, month, 1).strftime('%B %Y') # Име на месеца

    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'month_days': month_days,   # Матрицата на календара
        'shifts_by_day': shifts_by_day, # Всички наряди
        'dbpk_by_day': dbpk_by_day,     # Само главните (за красота)
        'prev_year': prev_date.year,
        'prev_month': prev_date.month,
        'next_year': next_date.year,
        'next_month': next_date.month,
        'today': today,
    }
    return render(request, 'roster/home_calendar.html', context)