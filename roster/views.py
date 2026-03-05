from django.core.management import call_command
from io import StringIO
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate
from django.shortcuts import render, get_object_or_404, redirect
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from .models import Announcement, DutyShift, DutyType, Soldier, Leave, Announcement, ShiftPreference, AuthorizedDevice
from .forms import DutyShiftForm, BatchLeaveForm
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.contrib import messages
from django.db import transaction
import calendar
import datetime
import re

def dashboard_view(request):
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    # 1. ОСНОВНИ БРОЯЧИ (KPIs)
    total_soldiers = Soldier.objects.filter(is_active=True).count()
    
    # Колко са наряд днес
    on_duty_today_count = DutyShift.objects.filter(date=today).exclude(status='admin_draft').count()    
    # Колко са в отпуск/болничен днес (активни leave записи)
    on_leave_today_count = Leave.objects.filter(
        start_date__lte=today, 
        end_date__gte=today
    ).count()

    # Изчисляваме наличните (Тотал - (Наряд + Отсъстващи))
    present_count = total_soldiers - (on_duty_today_count + on_leave_today_count)

    # 2. ВАЖНИТЕ НАРЯДИ ДНЕС (Сортирани по тежест - ДБПК най-горе)
    key_shifts_today = DutyShift.objects.filter(date=today).exclude(status='admin_draft').select_related('soldier', 'duty_type').order_by('-duty_type__weight')[:5]

    # 3. ПРОВЕРКА ЗА УТРЕ (Има ли ОФИЦИАЛЕН график?)
    is_tomorrow_ready = DutyShift.objects.filter(date=tomorrow).exclude(status='admin_draft').exists()
    
    if not is_tomorrow_ready:
        tomorrow_status = "⚠️ ЛИПСВА ГРАФИК"
        tomorrow_class = "danger"
    else:
        tomorrow_count = DutyShift.objects.filter(date=tomorrow).exclude(status='admin_draft').count()
        tomorrow_status = f"✅ Утвърден ({tomorrow_count})"
        tomorrow_class = "success"

    # 4. БЪРЗ ПОГЛЕД КЪМ БОЛНИТЕ (За сводката)
    sick_today = Leave.objects.filter(
        start_date__lte=today, 
        end_date__gte=today,
        leave_type='sick'
    ).select_related('soldier')

    active_alert = Announcement.objects.filter(is_active=True).order_by('-created_at').first()
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
        'active_alert': active_alert,
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
        if s.company == 'Млади': group_key = 'young'
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
    # --- МАГИЯ ЗА СОРТИРАНЕ НА ДЛЪЖНОСТИ ---
    # Придаваме числова тежест на длъжностите (1 е най-важно, 99 са редовите)
    position_order = Case(
        When(position='ДК', then=Value(1)),
        When(position='ЗДК', then=Value(2)),
        When(position='ОК', then=Value(3)),
        When(position='ЗОК', then=Value(4)),
        When(position='ЕК', then=Value(5)),
        When(position='ЗЕК', then=Value(6)),
        When(position='КВД', then=Value(7)), # Най-старши при Младите
        When(position='ЗКВ', then=Value(8)),
        When(position='КО', then=Value(9)),
        default=Value(99),
        output_field=IntegerField()
    )

    # --- БАЗОВ ФИЛТЪР ---
    # Взимаме само активните и ИЗКЛЮЧВАМЕ Офицерските Кандидати (КВ) от статистиката
    base_qs = Soldier.objects.filter(is_active=True).exclude(position='КВ')

    # 1. ТАБ: ТОЧКИ (Класация)
    leaderboard = base_qs.select_related('rank_group').order_by(
        'rank_group__priority', 'rank_group__name', '-score'
    )
    
    # 2. ТАБ: ПО РОТИ
    # Тъй като seed_data.py вече слага КО, ЗКВ и КВД в компания "Млади", 
    # кодът тук става супер прост и чист!
    
    company_1 = base_qs.filter(company='1').annotate(
        pos_order=position_order
    ).order_by('pos_order', '-rank_group__priority', 'last_name')
    
    company_2 = base_qs.filter(company='2').annotate(
        pos_order=position_order
    ).order_by('pos_order', '-rank_group__priority', 'last_name')

    young_cadets = base_qs.filter(company='Млади').annotate(
        pos_order=position_order
    ).order_by('pos_order', '-rank_group__priority', 'last_name')

    # 3. ТАБ: ЕКИПАЖИ И ЩАБ
    high_command_positions = ['ДК', 'ЗДК', 'ОК', 'ЗОК']
    
    # Само Щабът (Големите командири)
    high_command = base_qs.filter(
        position__in=high_command_positions
    ).annotate(pos_order=position_order).order_by('pos_order', '-rank_group__priority', 'last_name')

    # Всички останали в екипажите (без Щаба)
    # Всички останали в екипажите (без Щаба и СТРОГО БЕЗ МЛАДИТЕ)
    crews_raw = base_qs.exclude(crew="").exclude(
        position__in=high_command_positions
    ).exclude(
        company='Млади'
    ).annotate(pos_order=position_order).order_by('pos_order', '-rank_group__priority', 'last_name')
    
    # Групираме ги и ги сортираме математически (1, 2, 3... 16)
    crews_dict = {}
    for s in crews_raw:
        crews_dict.setdefault(s.crew, []).append(s)
    
    def extract_num(crew_name):
        nums = re.findall(r'\d+', crew_name)
        return int(nums[0]) if nums else 999
    
    sorted_crew_keys = sorted(crews_dict.keys(), key=extract_num)
    by_crew = [{'name': key, 'members': crews_dict[key]} for key in sorted_crew_keys]

    # 4. ТАБ: КЛАСНИ ОТДЕЛЕНИЯ
    by_class_raw = base_qs.exclude(class_section="").order_by(
        '-rank_group__priority', 'class_section', 'faculty_number'
    )
    
    class_dict = {}
    for s in by_class_raw:
        class_dict.setdefault(s.class_section, []).append(s)
        
    by_class = [{'name': key, 'members': class_dict[key]} for key in class_dict.keys()]

    batch_form = BatchLeaveForm()

    context = {
        'leaderboard': leaderboard,
        'company_1': company_1,
        'company_2': company_2,
        'young_cadets': young_cadets,
        'high_command': high_command,
        'by_crew': by_crew,
        'by_class': by_class,
        'all_soldiers': leaderboard, # Използваме го за масовата отпуска
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
        
        # Броим хората по роти за дадения ден
        for s in day_shifts:
            if s.soldier.company == 'Млади': # Вече ги търсим по company
                count_young += 1
            elif s.soldier.company == '1':
                count_c1 += 1
            elif s.soldier.company == '2':
                count_c2 += 1
        
        # Проверяваме дали нарядите за деня са чернови
        is_draft = False
        if day_shifts and day_shifts[0].status == 'admin_draft':
            is_draft = True
            
        stats_by_day[day] = {
            'c1': count_c1, 
            'c2': count_c2, 
            'young': count_young,
            'is_draft': is_draft
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

def emergency_list(request):
    soldiers = Soldier.objects.filter(is_active=True).order_by('company', 'platoon', 'last_name')
    
    context = {
        'soldiers': soldiers,
        # ПРОМЯНАТА Е ТУК: Ползваме .now(), а не .today()
        'today': datetime.datetime.now(), 
    }
    return render(request, 'roster/emergency_print.html', context)

@user_passes_test(lambda u: u.is_superuser)
def post_announcement(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        target = request.POST.get('target') # <--- ВАЖНО
        
        Announcement.objects.filter(is_active=True).update(is_active=False)
        
        # Записваме и target, за да е доволна базата
        Announcement.objects.create(
            title=title, 
            message=message, 
            target=target, 
            is_active=True
        )
        messages.warning(request, "🚨 ТРЕВОГАТА Е ОБЯВЕНА УСПЕШНО!")
    return redirect('roster_home')

@user_passes_test(lambda u: u.is_superuser)
def dismiss_announcement(request):
    Announcement.objects.filter(is_active=True).update(is_active=False)
    messages.success(request, "✅ Тревогата е отменена.")
    return redirect('roster_home')

def _generate_smart_month(year, month):
    _, num_days = calendar.monthrange(year, month)
    duties = DutyType.objects.all().order_by('-weight') # От най-тежките към най-леките
    
    # Зареждаме виртуални точки (за да не пипаме базата докато е чернова)
    soldiers = Soldier.objects.filter(is_active=True)
    current_scores = {s.id: s.score for s in soldiers}
    
    # Изтриваме старите чернови за този месец (за да можем да прегенерираме)
    DutyShift.objects.filter(date__year=year, date__month=month, status='admin_draft').delete()

    for day in range(1, num_days + 1):
        current_date = datetime.date(year, month, day)
        yesterday = current_date - timedelta(days=1)
        
        # 1. Твърди забрани за деня
        on_leave = Leave.objects.filter(start_date__lte=current_date, end_date__gte=current_date).values_list('soldier_id', flat=True)
        tired = DutyShift.objects.filter(date=yesterday).values_list('soldier_id', flat=True)
        assigned_today = DutyShift.objects.filter(date=current_date).values_list('soldier_id', flat=True)
        
        # 2. Желания за деня
        wants = ShiftPreference.objects.filter(date=current_date, preference='want').values_list('soldier_id', flat=True)
        cannots = ShiftPreference.objects.filter(date=current_date, preference='cannot').values_list('soldier_id', flat=True)

        for duty in duties:
            needed = duty.people_required
            allowed_groups = duty.allowed_ranks.all() # ЗЛАТНОТО ПРАВИЛО (Курсовете)
            
            candidates = soldiers.filter(rank_group__in=allowed_groups)
            valid_candidates = [c for c in candidates if c.id not in on_leave and c.id not in tired and c.id not in assigned_today]
            
            if not valid_candidates:
                continue # Ако буквално няма живи хора, прескачаме (или хвърляме грешка)
            
            # Разпределяме в кофи и сортираме по виртуалните точки
            volunteers = sorted([c for c in valid_candidates if c.id in wants], key=lambda x: current_scores[x.id])
            neutrals = sorted([c for c in valid_candidates if c.id not in wants and c.id not in cannots], key=lambda x: current_scores[x.id])
            blocked = sorted([c for c in valid_candidates if c.id in cannots], key=lambda x: current_scores[x.id])
            
            selected = []
            
            # Пълним: Първо доброволци -> После неутрални -> Накрая "под ножа"
            for lst in [volunteers, neutrals, blocked]:
                while len(selected) < needed and lst:
                    chosen = lst.pop(0)
                    selected.append(chosen)
                    # Добавяме виртуални точки, за да не го избере пак утре
                    current_scores[chosen.id] += duty.weight
                    
            # Създаваме черновата
            for s in selected:
                DutyShift.objects.create(
                    date=current_date, duty_type=duty, soldier=s, status='admin_draft'
                )


# --- 2. ИЗГЛЕДЪТ ЗА АДМИНА ---
@user_passes_test(lambda u: u.is_superuser)
def monthly_planner(request):
    today = datetime.date.today()
    # По подразбиране предлагаме следващия месец
    next_month_date = (today.replace(day=28) + timedelta(days=4))
    target_year = next_month_date.year
    target_month = next_month_date.month

    if request.method == 'POST':
        target_year = int(request.POST.get('year'))
        target_month = int(request.POST.get('month'))
        
        # Стартираме умния алгоритъм
        _generate_smart_month(target_year, target_month)
        
        messages.success(request, f"✅ Скритата чернова за {target_month}/{target_year} е генерирана успешно и чака преглед!")
        return redirect('monthly_planner')

    # Взимаме статистика колко чернови имаме генерирани
    draft_count = DutyShift.objects.filter(date__year=target_year, date__month=target_month, status='admin_draft').count()

    context = {
        'target_year': target_year,
        'target_month': target_month,
        'draft_count': draft_count,
    }
    return render(request, 'roster/monthly_planner.html', context)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, AllowAny, IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_my_shifts(request):
    user = request.user 
    soldier = user.soldier
    today = datetime.date.today()
    my_shifts = DutyShift.objects.filter(
        soldier=soldier, 
        date__gte=today
    ).order_by('date')
    data = []
    for shift in my_shifts:
        data.append({
            "date": shift.date.strftime('%Y-%m-%d'),
            "duty_name": shift.duty_type.name,
            "status": shift.status
        })
        
    return Response({
        "status": "success",
        "soldier_name": f"{soldier.rank_title} {soldier.last_name}",
        "faculty_number": soldier.faculty_number,
        "upcoming_shifts": data
    })
   
# --- АПИ ЗА ТАБ 2: СЪОБЩЕНИЯ ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_announcements(request):
    """ Връща само съобщенията, които се отнасят за този курсант """
    soldier = request.user.soldier
    
    # Определяме кои съобщения го касаят
    valid_targets = ['all']
    if soldier.company == '1': valid_targets.append('1')
    elif soldier.company == '2': valid_targets.append('2')
    elif soldier.company == 'Млади': valid_targets.extend(['young', 'Млади'])
    
    # Ако е от щаба/висшия състав
    if soldier.position in ['ДК', 'ЗДК', 'ОК', 'ЗОК', 'КВ']:
        valid_targets.append('staff')

    alerts = Announcement.objects.filter(is_active=True, target__in=valid_targets).order_by('-created_at')
    
    data = []
    for a in alerts:
        data.append({
            "title": a.title,
            "message": a.message,
            "date": a.created_at.strftime('%d.%m.%Y %H:%M')
        })
        
    return Response({
        "status": "success",
        "alerts": data
    })


# --- АПИ ЗА ТАБ 3: ЖЕЛАНИЯ / БОРСА ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_submit_preference(request):
    """ Позволява на курсанта да каже кога ИСКА или НЕ МОЖЕ да е наряд """
    soldier = request.user.soldier
    
    date_str = request.data.get('date')
    preference = request.data.get('preference') # Очакваме 'want' или 'cannot'

    if not date_str or preference not in ['want', 'cannot']:
        return Response({"detail": "Невалидни данни. Изпратете 'date' и 'preference'."}, status=400)

    try:
        pref_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({"detail": "Грешен формат на датата. Използвайте YYYY-MM-DD."}, status=400)

    # Не могат да дават желания за минали дати
    if pref_date < datetime.date.today():
        return Response({"detail": "Не можете да заявявате желания за минали дати."}, status=400)

    # Записваме или обновяваме желанието (ако вече е цъкнал веднъж)
    obj, created = ShiftPreference.objects.update_or_create(
        soldier=soldier,
        date=pref_date,
        defaults={'preference': preference}
    )

    action_text = "доброволец" if preference == 'want' else "блокиран"
    return Response({
        "status": "success", 
        "message": f"Денят {date_str} е маркиран като {action_text}."
    })
 
@api_view(['POST'])
@permission_classes([AllowAny]) 
def api_device_login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    device_id = request.data.get('device_id') # <--- Хардуерният отпечатък
    device_name = request.data.get('device_name', 'Unknown Device')

    if not username or not password or not device_id:
        return Response({"detail": "Липсват задължителни данни (username, password, device_id)."}, status=400)

    # 1. Проверяваме паролата
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response({"detail": "Грешен факултетен номер или парола."}, status=401)
        
    soldier = getattr(user, 'soldier', None)
    if not soldier or not soldier.is_active:
        return Response({"detail": "Акаунтът е неактивен."}, status=403)

    # 2. ПРОВЕРКА НА УСТРОЙСТВОТО (Zero Trust магията)
    # Опитваме се да намерим това устройство в базата
    device, created = AuthorizedDevice.objects.get_or_create(
        device_id=device_id,
        defaults={
            'soldier': soldier,
            'device_name': device_name
        }
    )

    # Ако устройството вече съществува, но е вързано за ДРУГ курсант -> КРАЖБА!
    if device.soldier != soldier:
        return Response({"detail": "ВНИМАНИЕ: Това устройство е регистрирано на друг курсант!"}, status=403)

    # Ако си го блокирал през Админ панела
    if not device.is_active:
        return Response({"detail": "Достъпът от това устройство е забранен от Администратор."}, status=403)

    # Записваме от кое IP влиза (За следене)
    client_ip = request.META.get('REMOTE_ADDR')
    device.last_ip_address = client_ip
    device.save()

    # 3. ВСИЧКО Е ТОЧНО -> ИЗДАВАМЕ СЕРТИФИКАТА (JWT)
    refresh = RefreshToken.for_user(user)

    return Response({
        "status": "success",
        "message": f"Добре дошли, {soldier.last_name}",
        "tokens": {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
    })
    
# --- АПИ ЗА ТАБ 1/3: ПРОФИЛ И ТОЧКИ ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_profile(request):
    """ Връща пълното досие на курсанта за екрана 'Моят Профил' """
    soldier = request.user.soldier
    today = datetime.date.today()

    # 1. Взимаме предстоящите отпуски/болнични
    upcoming_leaves = Leave.objects.filter(
        soldier=soldier,
        end_date__gte=today
    ).order_by('start_date')

    leaves_data = []
    for l in upcoming_leaves:
        leaves_data.append({
            "type": l.get_leave_type_display(),
            "start": l.start_date.strftime('%Y-%m-%d'),
            "end": l.end_date.strftime('%Y-%m-%d'),
            "reason": l.reason or ""
        })

    # 2. Взимаме заявените желания (за да може приложението да ги оцвети в календара)
    preferences = ShiftPreference.objects.filter(
        soldier=soldier,
        date__gte=today
    )
    
    # Правим го на речник { "2026-10-25": "want", "2026-10-26": "cannot" } за лесно четене от телефона
    pref_data = { p.date.strftime('%Y-%m-%d'): p.preference for p in preferences }

    # 3. Пакетираме всичко
    return Response({
        "status": "success",
        "profile": {
            "first_name": soldier.first_name,
            "last_name": soldier.last_name,
            "rank_title": soldier.rank_title,
            "position": soldier.get_position_display(),
            "company": soldier.company,
            "platoon": soldier.platoon,
            "score": soldier.score,
        },
        "upcoming_leaves": leaves_data,
        "preferences": pref_data
    })