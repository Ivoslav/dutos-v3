from django.core.management import call_command
from io import StringIO
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from datetime import timedelta
from .models import DutyShift, DutyType, Soldier, Leave
from .forms import DutyShiftForm, BatchLeaveForm
from django.db.models import Count, Q
from django.contrib import messages
import calendar
import datetime

def dashboard_view(request):
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    # 1. ОСНОВНИ БРОЯЧИ (KPIs)
    total_soldiers = Soldier.objects.filter(is_active=True).count()
    
    # Колко са наряд днес
    on_duty_today_count = DutyShift.objects.filter(date=today).count()
    
    # Колко са в отпуск/болничен днес (активни leave записи)
    on_leave_today_count = Leave.objects.filter(
        start_date__lte=today, 
        end_date__gte=today
    ).count()

    # Изчисляваме наличните (Тотал - (Наряд + Отсъстващи))
    present_count = total_soldiers - (on_duty_today_count + on_leave_today_count)

    # 2. ВАЖНИТЕ НАРЯДИ ДНЕС (Сортирани по тежест - ДБПК най-горе)
    key_shifts_today = DutyShift.objects.filter(date=today).select_related('soldier', 'duty_type').order_by('-duty_type__weight')[:5]

    # 3. ПРОВЕРКА ЗА УТРЕ (Има ли график?)
    is_tomorrow_ready = DutyShift.objects.filter(date=tomorrow).exists()
    tomorrow_missing_count = 0
    if not is_tomorrow_ready:
        tomorrow_status = "⚠️ НЯМА ГРАФИК"
        tomorrow_class = "danger"
    else:
        tomorrow_count = DutyShift.objects.filter(date=tomorrow).count()
        tomorrow_status = f"✅ Готов ({tomorrow_count} наряд)"
        tomorrow_class = "success"

    # 4. БЪРЗ ПОГЛЕД КЪМ БОЛНИТЕ (За сводката)
    sick_today = Leave.objects.filter(
        start_date__lte=today, 
        end_date__gte=today,
        leave_type='sick'
    ).select_related('soldier')

    context = {
        'today': today,
        'total_soldiers': total_soldiers,
        'on_duty_today_count': on_duty_today_count,
        'on_leave_today_count': on_leave_today_count,
        'present_count': present_count,
        'key_shifts_today': key_shifts_today,
        'is_tomorrow_ready': is_tomorrow_ready,
        'tomorrow_status': tomorrow_status,
        'tomorrow_class': tomorrow_class,
        'sick_today': sick_today,
    }
    return render(request, 'roster/dashboard.html', context)

def roster_view(request):
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = datetime.date.today()
    else:
        selected_date = datetime.date.today()

    # ПОПРАВКА ТУК:
    # 1. Добавихме 'soldier__rank_group' в select_related, за да дръпне данните веднага.
    # 2. Сортираме по ID ('soldier__rank_group'), което е най-безопасно за regroup.
    shifts = DutyShift.objects.filter(date=selected_date).select_related(
        'soldier', 
        'duty_type', 
        'soldier__rank_group'
    ).order_by(
        '-soldier__rank_group__priority',  # 1. Приоритет
        'soldier__rank_group__name',       # <--- ВАЖНО: Сортираме по ТЕКСТ (Име)
        '-duty_type__weight'
    )

    leaves = list(Leave.objects.filter(start_date__lte=selected_date, end_date__gte=selected_date).select_related('soldier'))
    
    all_soldiers = Soldier.objects.filter(is_active=True).order_by('rank_group__priority', 'last_name')

    # ... (кодът за report речника си остава същият) ...
    report = {
        '1': {'name': '1-ва Рота (ВМС)', 'class': 'primary', 'total': 0, 'present': 0, 'duty': [], 'sick': [], 'home': [], 'mission': [], 'other': []},
        '2': {'name': '2-ра Рота (Медици)', 'class': 'danger', 'total': 0, 'present': 0, 'duty': [], 'sick': [], 'home': [], 'mission': [], 'other': []},
        'young': {'name': 'Млади Курсанти', 'class': 'success', 'total': 0, 'present': 0, 'duty': [], 'sick': [], 'home': [], 'mission': [], 'other': []}
    }

    shift_map = {s.soldier_id: s for s in shifts}
    leave_map = {l.soldier_id: l for l in leaves}

    for s in all_soldiers:
        if s.platoon == 'Млади': group_key = 'young'
        elif s.company == '1': group_key = '1'
        elif s.company == '2': group_key = '2'
        else: continue

        report[group_key]['total'] += 1
        
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
        'shifts': shifts,
        'report': report,
        'total_on_duty': shifts.count(),
        'all_soldiers': all_soldiers
    }
    return render(request, 'roster/daily_roster.html', context)

def statistics_view(request):
    # 1. Класация (Leaderboard)
    # ВАЖНО: Сортираме ПЪРВО по име на курса, за да не се нацепват групите, ако приоритетите са еднакви!
    # След това по точки (-score).
    leaderboard = Soldier.objects.filter(is_active=True).select_related('rank_group').order_by(
        'rank_group__priority', # Първо по важност (ако е настроено)
        'rank_group__name',     # Второ по име (за да са групирани 1-ви, 2-ри и т.н.)
        '-score'                # Трето по точки
    )
    
    # 2. Списъци по роти 
    # .exclude(platoon='Млади') маха младите от списъка на старите
    company_1 = Soldier.objects.filter(company='1', is_active=True).exclude(platoon='Млади').order_by('last_name')
    company_2 = Soldier.objects.filter(company='2', is_active=True).exclude(platoon='Млади').order_by('last_name')

    # 3. Младите (само те)
    young_cadets = Soldier.objects.filter(platoon='Млади', is_active=True).order_by('faculty_number')
        
    by_crew = Soldier.objects.filter(is_active=True).exclude(crew="").order_by('crew', 'last_name')
    by_class = Soldier.objects.filter(is_active=True).order_by('class_section', 'faculty_number')
    
    # Форма за масовата отпуска
    batch_form = BatchLeaveForm()

    context = {
        'leaderboard': leaderboard,
        'company_1': company_1,
        'company_2': company_2,
        'young_cadets': young_cadets,
        'by_crew': by_crew,
        'by_class': by_class,
        'all_soldiers': leaderboard, # Използваме същия списък за масовата таблица
        'batch_form': batch_form,
    }
    return render(request, 'roster/statistics.html', context)

def soldier_profile(request, soldier_id):
    soldier = get_object_or_404(Soldier, id=soldier_id)
    today = datetime.date.today()

    upcoming_shifts = DutyShift.objects.filter(soldier=soldier, date__gte=today).order_by('date')
    past_shifts = DutyShift.objects.filter(soldier=soldier, date__lt=today).order_by('-date')
    leaves = Leave.objects.filter(soldier=soldier).order_by('-start_date')

    form = DutyShiftForm(request.POST or None)

    if request.method == 'POST':
        # 1. ЗАЩИТА ОТ "ЗОМБИТА" (Още преди валидацията на формата)
        if not soldier.is_active: # <--- НОВА ЗАЩИТА 1
             messages.error(request, "⛔ ГРЕШКА: Този военнослужещ е неактивен!")
             return redirect('roster_stats') # Изхвърляме го веднага

        if form.is_valid():
            new_date = form.cleaned_data['date']
            duty_type = form.cleaned_data['duty_type'] # Взимаме вида наряд от формата
            
            # 2. ПРОВЕРКИ ЗА СЪВМЕСТИМОСТ (Leave, Shift, Rank)
            
            # А) Отпуск
            on_leave = Leave.objects.filter(
                soldier=soldier,
                start_date__lte=new_date,
                end_date__gte=new_date
            ).exists()

            # Б) Вече има наряд днес
            has_shift_today = DutyShift.objects.filter(
                soldier=soldier, 
                date=new_date
            ).exists()

            # В) Умора (вчера)
            yesterday = new_date - timedelta(days=1)
            has_shift_yesterday = DutyShift.objects.filter(
                soldier=soldier, 
                date=yesterday
            ).exists()

            # Г) РАНГОВА ЗАЩИТА (Съвпада ли званието?)
            # Проверяваме дали rank_group на войника присъства в allowed_ranks на наряда
            is_rank_allowed = duty_type.allowed_ranks.filter(id=soldier.rank_group.id).exists() # <--- НОВА ЗАЩИТА 2

            # --- ВАЛИДАЦИЯ ---
            if on_leave:
                form.add_error('date', '⛔ Грешка: Войникът е в отпуск на тази дата!')
            
            elif has_shift_today:
                form.add_error('date', '⛔ Грешка: Вече има назначен наряд за този ден!')
                
            elif has_shift_yesterday:
                form.add_error('date', '⛔ Грешка: Войникът е уморен (наряд вчера)!')

            elif not is_rank_allowed: # <--- АКО ЗВАНИЕТО НЕ ОТГОВАРЯ
                form.add_error('duty_type', f'⛔ Грешка: Този наряд не е позволен за "{soldier.rank_group}"!')

            else:
                # Всичко е точно -> ЗАПИСВАМЕ
                shift = form.save(commit=False)
                shift.soldier = soldier
                shift.save()
                
                soldier.score += shift.duty_type.weight
                soldier.save()
                
                messages.success(request, "✅ Нарядът е добавен успешно!")
                return redirect('roster_stats') # Или където трябва да води

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
        'stats_by_day': stats_by_day,
        'prev_year': prev_date.year,
        'prev_month': prev_date.month,
        'next_year': next_date.year,
        'next_month': next_date.month,
        'today': today,
    }
    return render(request, 'roster/home_calendar.html', context)

def emergency_swap(request, shift_id):
    shift = get_object_or_404(DutyShift, id=shift_id)
    
    # <--- НОВА ЗАЩИТА: ИСТОРИЯТА Е НЕПРИКОСНОВЕНА
    if shift.date < datetime.date.today():
        messages.error(request, "⛔ ГРЕШКА: Не може да се правят промени в минали дати!")
        return redirect(f"/roster/daily/?date={shift.date}")
    # ----------------------------------------------------

    if request.method == 'POST':
        new_soldier_id = request.POST.get('new_soldier')
        reason = request.POST.get('reason')
        
        new_soldier = get_object_or_404(Soldier, id=new_soldier_id)
        old_soldier = shift.soldier
        
        # Проверка за отпуск
        on_leave = Leave.objects.filter(
            soldier=new_soldier,
            start_date__lte=shift.date,
            end_date__gte=shift.date
        ).exists()
        
        if on_leave:
            messages.error(request, f"⛔ ГРЕШКА: {new_soldier.last_name} е в отпуск/болничен на тази дата!")
            return redirect(f"/roster/daily/?date={shift.date}")

        # Проверка за заетост
        has_shift = DutyShift.objects.filter(
            soldier=new_soldier,
            date=shift.date
        ).exists()
        
        if has_shift:
            messages.error(request, f"⛔ ГРЕШКА: {new_soldier.last_name} вече има друг наряд на тази дата!")
            return redirect(f"/roster/daily/?date={shift.date}")

        # Смяна на точките
        old_soldier.score -= shift.duty_type.weight
        if old_soldier.score < 0: old_soldier.score = 0
        old_soldier.save()
        
        new_soldier.score += shift.duty_type.weight
        new_soldier.save()
        
        # Запис
        shift.soldier = new_soldier
        shift.save()
        
        messages.success(request, f"✅ Успешна смяна: {old_soldier.last_name} ➡️ {new_soldier.last_name}")
        
    return redirect(f"/roster/daily/?date={shift.date}")

from django.views.decorators.http import require_POST

@require_POST # Само POST заявки
def save_batch_leave(request):
    form = BatchLeaveForm(request.POST)
    
    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        leave_type = form.cleaned_data['leave_type']
        reason = form.cleaned_data['reason']
        
        # Взимаме ID-тата на избраните хора
        soldier_ids = request.POST.getlist('selected_soldiers')
        
        count = 0
        for s_id in soldier_ids:
            soldier = get_object_or_404(Soldier, id=s_id)
            
            # Създаваме отпуската (Това автоматично ще изтрие нарядите благодарение на кода ни в models.py)
            Leave.objects.create(
                soldier=soldier,
                start_date=start_date,
                end_date=end_date,
                leave_type=leave_type,
                reason=reason
            )
            count += 1
            
        messages.success(request, f"✅ Успешно записани отпуски/награди на {count} военнослужещи!")
    else:
        messages.error(request, "⛔ Грешка в данните! Проверете датите.")
        
    return redirect('roster_stats')

@user_passes_test(lambda u: u.is_superuser) # Само за Админи!
def debug_panel(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        out = StringIO() # Тук ще ловим отговора от терминала
        
        try:
            if action == 'seed_data':
                call_command('seed_data', stdout=out)
                messages.success(request, "✅ Армията е презаредена успешно!")
            
            elif action == 'create_duties':
                call_command('create_duties', stdout=out) # Скриптът от предния ни разговор
                messages.success(request, "✅ Видовете наряди са създадени!")

            elif action == 'fix_duties':
                call_command('fix_duties', stdout=out)
                messages.success(request, "✅ Правилата за наряди са оправени!")
            
            elif action == 'generate_today':
                today = datetime.date.today().strftime('%Y-%m-%d')
                call_command('generate_roster', today, stdout=out)
                messages.success(request, f"✅ Графикът за днес ({today}) е генериран!")

            elif action == 'generate_tomorrow':
                tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                call_command('generate_roster', tomorrow, stdout=out)
                messages.success(request, f"✅ Графикът за утре ({tomorrow}) е генериран!")

        except Exception as e:
            messages.error(request, f"❌ ГРЕШКА: {str(e)}")
        
        messages.info(request, out.getvalue())

        return redirect('debug_panel')

    return render(request, 'roster/debug_tools.html')