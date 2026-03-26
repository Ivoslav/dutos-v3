from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.management import call_command
from io import StringIO
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate
from django.shortcuts import render, get_object_or_404, redirect
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from .models import Announcement, AnnouncementReceipt, DutyShift, DutyType, Soldier, Leave, Announcement, ShiftPreference, AuthorizedDevice, ShiftSwapRequest
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

    # ==========================================
    # НОВО: АКТИВНИ ОПОВЕСТЯВАНИЯ И ПРОГРЕС БАР
    # ==========================================
    from .models import Announcement
    active_announcements_raw = Announcement.objects.filter(is_active=True).prefetch_related('receipts__soldier').order_by('-created_at')
    
    announcements_data = []
    for ann in active_announcements_raw:
        receipts = ann.receipts.all()
        total_count = receipts.count()
        read_count = receipts.filter(is_read=True).count()
        unread_receipts = receipts.filter(is_read=False)
        
        # Пресмятаме процента за прогрес бара
        percent = int((read_count / total_count * 100)) if total_count > 0 else 0
        
        announcements_data.append({
            'obj': ann,
            'total_count': total_count,
            'read_count': read_count,
            'unread_count': total_count - read_count,
            'percent': percent,
            'unread_soldiers': [r.soldier for r in unread_receipts]
        })

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
        'announcements_data': announcements_data,
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

    shifts = DutyShift.objects.filter(date=selected_date).select_related(
        'soldier', 
        'duty_type', 
        'soldier__rank_group'
    ).prefetch_related(
        'duty_type__allowed_ranks'
    ).order_by(
        '-soldier__rank_group__priority',
        'soldier__rank_group__name',
        '-duty_type__weight'
    )

# ДОБАВЕНО __date, ЗА ДА ИГНОРИРА ЧАСОВЕТЕ ПРИ СРАВНЕНИЕТО!
    leaves = list(Leave.objects.filter(
        start_date__date__lte=selected_date, 
        end_date__date__gte=selected_date
    ).select_related('soldier')) 
       
    all_soldiers = Soldier.objects.filter(is_active=True).order_by('-rank_group__priority', 'last_name')

    # ---------------------------------------------------------
    # НОВО: БРУТАЛНО ФИЛТРИРАНЕ ЗА МОДАЛА (UX Подобрение)
    # ---------------------------------------------------------
    yesterday = selected_date - datetime.timedelta(days=1)
    tomorrow = selected_date + datetime.timedelta(days=1)

    # 1. Намираме ID-тата на хората, които са наряд вчера, днес или утре
    busy_shift_ids = DutyShift.objects.filter(
        date__in=[yesterday, selected_date, tomorrow]
    ).values_list('soldier_id', flat=True)

    # 2. Намираме ID-тата на хората, които са в отпуск/болничен точно на тази дата
    on_leave_ids = Leave.objects.filter(
        start_date__lte=selected_date, 
        end_date__gte=selected_date
    ).values_list('soldier_id', flat=True)

    # 3. Обединяваме всички забранени в едно множество (set), за да няма дубликати
    forbidden_ids = set(list(busy_shift_ids) + list(on_leave_ids))

    # 4. Създаваме списъка за модала, КАТО ИЗКЛЮЧВАМЕ забранените!
    swap_candidates = Soldier.objects.filter(
        is_active=True
    ).exclude(
        id__in=forbidden_ids
    ).select_related('rank_group').order_by('score', 'last_name')
    # ---------------------------------------------------------
    
    report = {
        '1': {'name': '1-ва Рота (ВМС)', 'class': 'primary', 'total': 0, 'present_morning': 0, 'present_evening': 0, 'duty': [], 'sick': [], 'home': [], 'city': [], 'mission': [], 'other': []},
        '2': {'name': '2-ра Рота (Медици)', 'class': 'danger', 'total': 0, 'present_morning': 0, 'present_evening': 0, 'duty': [], 'sick': [], 'home': [], 'city': [], 'mission': [], 'other': []},
        'young': {'name': 'Млади Курсанти', 'class': 'success', 'total': 0, 'present_morning': 0, 'present_evening': 0, 'duty': [], 'sick': [], 'home': [], 'city': [], 'mission': [], 'other': []}
    }

    shift_map = {s.soldier_id: s for s in shifts}
    leave_map = {l.soldier_id: l for l in leaves}

    for s in all_soldiers:
        if s.company == 'Млади': group_key = 'young'
        elif s.company == '1': group_key = '1'
        elif s.company == '2': group_key = '2'
        else: continue

        report[group_key]['total'] += 1
        
        # По дефолт приемаме, че човекът е в строя
        is_present_morning = True
        is_present_evening = True
        
        if s.id in leave_map:
            l = leave_map[s.id]
            if l.leave_type == 'sick': 
                report[group_key]['sick'].append(l)
                is_present_morning = False; is_present_evening = False
            elif l.leave_type == 'home': 
                report[group_key]['home'].append(l)
                is_present_morning = False; is_present_evening = False
            elif l.leave_type == 'city': 
                report[group_key]['city'].append(l)
                # МАГИЯТА: Налице е сутрин, но вечерта отсъства!
                is_present_evening = False 
            elif l.leave_type == 'mission': 
                report[group_key]['mission'].append(l)
                is_present_morning = False; is_present_evening = False
            else: 
                report[group_key]['other'].append(l)
                is_present_morning = False; is_present_evening = False
        
        if s.id in shift_map:
            sh = shift_map[s.id]
            report[group_key]['duty'].append(sh)
            # Нарядът също не е в строя
            is_present_morning = False; is_present_evening = False
            
        if is_present_morning: report[group_key]['present_morning'] += 1
        if is_present_evening: report[group_key]['present_evening'] += 1

    context = {
        'selected_date': selected_date,
        'shifts': shifts,
        'report': report,
        'total_on_duty': shifts.count(),
        'all_soldiers': all_soldiers,
        'swap_candidates': swap_candidates
    }
    return render(request, 'roster/daily_roster.html', context)

def statistics_view(request):
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
    upcoming_shifts = DutyShift.objects.filter(soldier=soldier, date__gte=today).order_by('date')[:5]
    past_shifts = DutyShift.objects.filter(soldier=soldier, date__lt=today).order_by('-date')[:5]
    leaves = Leave.objects.filter(soldier=soldier).order_by('-start_date')[:5]
    active_stars = soldier.disciplinary_records.filter(record_type='star', is_active=True).count()
    active_dots = soldier.disciplinary_records.filter(record_type='dot', is_active=True).count()
    records = soldier.disciplinary_records.all()[:10]
    form = DutyShiftForm(request.POST or None)

    if request.method == 'POST':
        action = request.POST.get('action', 'assign_duty')
        
        # 1. ДОБАВЯНЕ НА ЗАПИС В ДОСИЕТО (Звездичка или Черна точка)
        if action == 'add_record':
            record_type = request.POST.get('record_type')
            reason = request.POST.get('reason')
            if record_type and reason:
                from .models import DisciplinaryRecord
                DisciplinaryRecord.objects.create(soldier=soldier, record_type=record_type, reason=reason)
                messages.success(request, f"{'⭐ Звездичката' if record_type == 'star' else '⚫ Черната точка'} е добавена успешно!")
            return redirect(request.META.get('HTTP_REFERER', 'roster_stats'))

        # 2. ИЗЧИСТВАНЕ/ВРЪЩАНЕ НА ЗАПИС
        elif action == 'toggle_record':
            record_id = request.POST.get('record_id')
            from .models import DisciplinaryRecord
            rec = get_object_or_404(DisciplinaryRecord, id=record_id)
            rec.is_active = not rec.is_active
            rec.save()
            messages.info(request, "🔄 Статусът на записа е променен.")
            return redirect(request.META.get('HTTP_REFERER', 'roster_stats'))

        # 3. НАЗНАЧАВАНЕ НА НАРЯД (Старото)
        elif action == 'assign_duty':
            if not soldier.is_active:
                 messages.error(request, "⛔ ГРЕШКА: Този военнослужещ е неактивен!")
                 return redirect(request.META.get('HTTP_REFERER', 'roster_stats'))

            if form.is_valid():
                new_date = form.cleaned_data['date']
                duty_type = form.cleaned_data['duty_type']
                
                on_leave = Leave.objects.filter(soldier=soldier, start_date__date__lte=new_date, end_date__date__gte=new_date).exists()
                has_shift_today = DutyShift.objects.filter(soldier=soldier, date=new_date).exists()
                has_shift_yesterday = DutyShift.objects.filter(soldier=soldier, date=new_date - datetime.timedelta(days=1)).exists()
                is_rank_allowed = duty_type.allowed_ranks.filter(id=soldier.rank_group.id).exists()

                if on_leave: form.add_error('date', '⛔ Грешка: Войникът е в отпуск/наказан на тази дата!')
                elif has_shift_today: form.add_error('date', '⛔ Грешка: Вече има назначен наряд!')
                elif has_shift_yesterday: form.add_error('date', '⛔ Грешка: Войникът е уморен!')
                elif not is_rank_allowed: form.add_error('duty_type', f'⛔ Грешка: Нарядът не е за {soldier.rank_group}!')
                else:
                    shift = form.save(commit=False)
                    shift.soldier = soldier
                    shift.save()
                    soldier.score += shift.duty_type.weight
                    soldier.save()
                    messages.success(request, "✅ Нарядът е добавен успешно!")
                    return redirect(request.META.get('HTTP_REFERER', 'roster_stats'))
                
    context = {
        'soldier': soldier,
        'upcoming_shifts': upcoming_shifts,
        'past_shifts': past_shifts,
        'leaves': leaves,
        'records': records,
        'active_stars': active_stars,
        'active_dots': active_dots,
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

        # Проверка за заетост (ДНЕС) и 24-часова почивка (ВЧЕРА и УТРЕ)
        has_shift = DutyShift.objects.filter(
            soldier=new_soldier,
            date__in=[
                shift.date, 
                shift.date - datetime.timedelta(days=1), 
                shift.date + datetime.timedelta(days=1)
            ]
        ).exists()
        
        if has_shift:
            messages.error(request, f"⛔ ГРЕШКА: {new_soldier.last_name} има наряд днес, вчера или утре (нарушава 24ч почивка)!")
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

@user_passes_test(lambda u: u.is_superuser)
def debug_panel(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        out = StringIO()
        
        try:
            # 1. ИНИЦИАЛИЗАЦИЯ
            if action == 'seed_data':
                call_command('seed_data', stdout=out)
                messages.success(request, "✅ Армията е презаредена успешно!")
            elif action == 'create_duties':
                call_command('create_duties', stdout=out)
                messages.success(request, "✅ Видовете наряди са създадени!")
            elif action == 'fix_duties':
                call_command('fix_duties', stdout=out)
                messages.success(request, "✅ Правилата за наряди са оправени!")

            # 2. МЕСЕЧЕН ЦИКЪЛ И БОРСА
            elif action == 'simulate_activity':
                import random
                today = datetime.date.today()
                next_month_date = (today.replace(day=28) + timedelta(days=4))
                ty, tm = next_month_date.year, next_month_date.month
                _, num_days = calendar.monthrange(ty, tm)

                Leave.objects.all().delete()
                ShiftPreference.objects.all().delete()
                soldiers = list(Soldier.objects.filter(is_active=True))
                leave_types = ['sick', 'home', 'mission', 'arrest']
                
                for _ in range(20):
                    s = random.choice(soldiers)
                    start_d = datetime.date(ty, tm, random.randint(1, num_days - 5))
                    end_d = start_d + timedelta(days=random.randint(2, 5))
                    Leave.objects.create(soldier=s, start_date=start_d, end_date=end_d, leave_type=random.choice(leave_types), reason="Авто-Симулация")

                for _ in range(80):
                    s = random.choice(soldiers)
                    p_date = datetime.date(ty, tm, random.randint(1, num_days))
                    ShiftPreference.objects.get_or_create(soldier=s, date=p_date, defaults={'preference': random.choice(['want', 'cannot'])})

                messages.success(request, f"🎭 СИМУЛАЦИЯ: Инжектирани са 20 отпуски и 80 желания за месец {tm}/{ty}!")
                
            elif action == 'generate_month':
                today = datetime.date.today()
                next_month_date = (today.replace(day=28) + timedelta(days=4))
                # Викаме алгоритъма директно
                _generate_smart_month(next_month_date.year, next_month_date.month)
                messages.success(request, f"🤖 Месечният график за {next_month_date.month}/{next_month_date.year} е генериран успешно като чернова!")

            elif action == 'simulate_swaps':
                import random
                future_shifts = list(DutyShift.objects.filter(date__gte=datetime.date.today()).exclude(status='official'))
                if not future_shifts:
                    messages.error(request, "❌ Няма бъдещи наряди! Първо генерирай месечен график.")
                    return redirect('debug_panel')

                shifts_to_swap = random.sample(future_shifts, min(10, len(future_shifts)))
                created_open, created_waiting = 0, 0

                for shift in shifts_to_swap:
                    if hasattr(shift, 'shiftswaprequest'): continue
                    if random.choice([True, False]):
                        ShiftSwapRequest.objects.create(shift=shift, requester=shift.soldier, reason="Авто Симулация", status='open')
                        created_open += 1
                    else:
                        busy_ids = DutyShift.objects.filter(date=shift.date).values_list('soldier_id', flat=True)
                        candidates = Soldier.objects.filter(rank_group=shift.soldier.rank_group, is_active=True).exclude(id__in=busy_ids).exclude(id=shift.soldier.id)
                        if candidates.exists():
                            ShiftSwapRequest.objects.create(shift=shift, requester=shift.soldier, substitute=random.choice(list(candidates)), reason="Тест", status='waiting')
                            created_waiting += 1
                messages.success(request, f"🔄 БОРСА: Генерирани {created_open} отворени и {created_waiting} чакащи заявки!")

            # 3. ОПОВЕСТЯВАНЕ И ТЕЛЕФОНИ
            elif action == 'simulate_reads':
                from .models import AnnouncementReceipt
                import random
                from django.utils import timezone
                
                active_receipts = list(AnnouncementReceipt.objects.filter(announcement__is_active=True, is_read=False))
                if not active_receipts:
                    messages.error(request, "❌ Няма активни непрочетени разписки!")
                    return redirect('debug_panel')
                    
                to_read = random.sample(active_receipts, max(1, int(len(active_receipts) * random.uniform(0.3, 0.7))))
                for r in to_read:
                    r.is_read = True
                    r.read_at = timezone.now()
                    r.save()
                messages.success(request, f"📱 СИМУЛАЦИЯ: {len(to_read)} курсанти цъкнаха РАЗБРАХ на телефоните си!")
                
            elif action == 'clear_announcements':
                Announcement.objects.all().delete()
                messages.success(request, "🧹 Всички съобщения (и техните разписки) бяха изтрити!")

            # 4. ДИСЦИПЛИНА
            elif action == 'simulate_discipline':
                from .models import DisciplinaryRecord
                import random
                soldiers = list(Soldier.objects.filter(is_active=True))
                count = 0
                for _ in range(30):
                    s = random.choice(soldiers)
                    rtype = random.choice(['star', 'dot'])
                    reason = "Отлично дежурство (Симулация)" if rtype == 'star' else "Закъснение за строй (Симулация)"
                    DisciplinaryRecord.objects.create(soldier=s, record_type=rtype, reason=reason)
                    count += 1
                messages.success(request, f"🎖️ ДОСИЕТА: Разпределени са {count} случайни звездички и черни точки!")

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
        announcement_type = request.POST.get('announcement_type', 'info') # НОВО: Взимаме типа
        title = request.POST.get('title')
        message = request.POST.get('message')
        target = request.POST.get('target', 'all')
        
        # Деактивираме старите активни съобщения
        Announcement.objects.filter(is_active=True).update(is_active=False)
        
        # Създаваме новото (Моделът автоматично ще генерира Разписките за войниците!)
        new_ann = Announcement.objects.create(
            announcement_type=announcement_type, # НОВО
            title=title, 
            message=message, 
            target=target, 
            is_active=True
        )
        messages.warning(request, f"📢 ОПОВЕСТЯВАНЕ ({new_ann.get_announcement_type_display()}) Е ОБЯВЕНО УСПЕШНО!")
    return redirect('roster_home')

@user_passes_test(lambda u: u.is_superuser)
def dismiss_announcement(request):
    # Когато Командирът отмени тревогата, тя става неактивна
    Announcement.objects.filter(is_active=True).update(is_active=False)
    messages.success(request, "✅ Оповестяването е отменено (деактивирано).")
    return redirect('roster_home')

def _generate_smart_month(year, month):
    _, num_days = calendar.monthrange(year, month)
    duties = DutyType.objects.all().order_by('-weight') # От най-тежките към най-леките
    
    # --- НОВО 1: ГРАФИКЪТ Е ГОСПОДАР ---
    # Изтриваме всички стари чернови за наряди
    DutyShift.objects.filter(date__year=year, date__month=month, status='admin_draft').delete()
    # Изтриваме всички автоматични градски отпуски (city) за месеца. 
    # Те трябва да се пускат ЧАК СЛЕД като графикът е утвърден! (Домашните ДО и Болните си остават)
    Leave.objects.filter(start_date__year=year, start_date__month=month, leave_type='city').delete()

    # Зареждаме виртуални точки (за да не пипаме базата докато е чернова)
    soldiers = Soldier.objects.filter(is_active=True)
    current_scores = {s.id: s.score for s in soldiers}

    for day in range(1, num_days + 1):
        current_date = datetime.date(year, month, day)
        yesterday = current_date - timedelta(days=1)
        
        # 1. Твърди забрани за деня
        on_leave = set(Leave.objects.filter(start_date__lte=current_date, end_date__gte=current_date).values_list('soldier_id', flat=True))
        tired = set(DutyShift.objects.filter(date=yesterday).values_list('soldier_id', flat=True))
        assigned_today = set(DutyShift.objects.filter(date=current_date).values_list('soldier_id', flat=True))
        
        # 2. Желания за деня
        wants = set(ShiftPreference.objects.filter(date=current_date, preference='want').values_list('soldier_id', flat=True))
        cannots = set(ShiftPreference.objects.filter(date=current_date, preference='cannot').values_list('soldier_id', flat=True))

        for duty in duties:
            needed = duty.people_required
            allowed_groups = duty.allowed_ranks.all()
            
            candidates = soldiers.filter(rank_group__in=allowed_groups)
            valid_candidates = [c for c in candidates if c.id not in on_leave and c.id not in tired and c.id not in assigned_today]
            
            # --- НОВО 2: ЕКСТРЕМЕН РЕЖИМ ---
            if len(valid_candidates) < needed:
                # Ако няма здрави и почивали хора, ЖЕРТВАМЕ ПОЧИВКАТА (взимаме уморените), 
                # защото военен пост не може да остане празен!
                desperate_candidates = [c for c in candidates if c.id not in on_leave and c.id not in assigned_today]
                valid_candidates = desperate_candidates
                
            if not valid_candidates:
                continue # Ако буквално всички са болни/отпуск, тогава се предаваме
                        
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
            # Създаваме черновата
            for s in selected:
                DutyShift.objects.create(
                    date=current_date, duty_type=duty, soldier=s, status='admin_draft'
                )
                assigned_today.add(s.id)

# ==========================================
# ⚖️ КАПИТАНСКИ ПУЛТ ЗА СМЕНИ (БОРСА)
# ==========================================
@user_passes_test(lambda u: u.is_superuser)
def swap_manager(request):
    if request.method == 'POST':
        swap_id = request.POST.get('swap_id')
        action = request.POST.get('action') # 'approve' или 'reject'
        
        swap = get_object_or_404(ShiftSwapRequest, id=swap_id)
        
        if action == 'approve' and swap.status == 'waiting':
            with transaction.atomic(): # Транзакция, за да сме сигурни, че всичко минава заедно
                old_soldier = swap.requester
                new_soldier = swap.substitute
                shift = swap.shift
                duty_weight = shift.duty_type.weight
                
                # 1. Разменяме точките
                old_soldier.score -= duty_weight
                if old_soldier.score < 0: old_soldier.score = 0
                old_soldier.save()
                
                new_soldier.score += duty_weight
                new_soldier.save()
                
                # 2. Разменяме наряда
                shift.soldier = new_soldier
                shift.save()
                
                # 3. Затваряме заявката
                swap.status = 'approved'
                swap.save()
                
                messages.success(request, f"✅ Смяната е ОДОБРЕНА: {old_soldier.last_name} предава наряда на {new_soldier.last_name}.")
                
        elif action == 'reject':
            swap.status = 'rejected'
            swap.save()
            messages.warning(request, "❌ Смяната беше отхвърлена.")
            
        return redirect('swap_manager')

    # Взимаме чакащите одобрение и тези, които още висят на борсата
    pending_swaps = ShiftSwapRequest.objects.filter(status='waiting').select_related('shift', 'requester', 'substitute')
    open_swaps = ShiftSwapRequest.objects.filter(status='open').select_related('shift', 'requester')

    context = {
        'pending_swaps': pending_swaps,
        'open_swaps': open_swaps,
    }
    return render(request, 'roster/swap_manager.html', context)

# ==========================================
# ⚙️ ЕДИНЕН МЕСЕЧЕН КОМАНДЕН ЦЕНТЪР
# ==========================================
@user_passes_test(lambda u: u.is_superuser)
def roster_lifecycle(request):
    today = datetime.date.today()
    # Взимаме месеца от URL-а (или по подразбиране следващия)
    next_month_date = (today.replace(day=28) + timedelta(days=4))
    target_year = int(request.GET.get('year', next_month_date.year))
    target_month = int(request.GET.get('month', next_month_date.month))

    # 1. ОПРЕДЕЛЯНЕ НА ТЕКУЩАТА ФАЗА
    shifts = DutyShift.objects.filter(date__year=target_year, date__month=target_month)
    
    if not shifts.exists():
        phase = 1 # СТЪПКА 1: Няма наряди (Събиране на желания)
    elif shifts.filter(status='admin_draft').exists():
        phase = 2 # СТЪПКА 2: Капитанска чернова (Скрити от курсантите)
    elif shifts.filter(status='public_draft').exists():
        phase = 3 # СТЪПКА 3: Отворена Борса (Курсантите се разменят)
    else:
        phase = 4 # СТЪПКА 4: Утвърден график (Всичко е official)

    # 2. ОБРАБОТКА НА ДЕЙСТВИЯТА (БУТОНИТЕ)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # --- ФАЗА 1 -> ФАЗА 2: Генериране на чернова ---
        if action == 'generate':
            _generate_smart_month(target_year, target_month) # Викаме твоя алгоритъм
            messages.success(request, f"✅ Черновата за {target_month}/{target_year} е генерирана и чака твоя преглед!")
            
        # --- ФАЗА 2 -> ФАЗА 3: Публикуване на борсата ---
        elif action == 'publish':
            shifts.filter(status='admin_draft').update(status='public_draft')
            messages.warning(request, "📢 Графикът е публикуван! Курсантите вече го виждат в приложението и могат да търсят смени.")
            
        # --- ФАЗА 3: Управление на конкретна смяна ---
        elif action in ['approve_swap', 'reject_swap']:
            swap_id = request.POST.get('swap_id')
            swap = get_object_or_404(ShiftSwapRequest, id=swap_id)
            
            if action == 'approve_swap' and swap.status == 'waiting':
                with transaction.atomic():
                    # 1. Разменяме точките
                    old_soldier = swap.requester
                    new_soldier = swap.substitute
                    duty_weight = swap.shift.duty_type.weight
                    
                    old_soldier.score = max(0, old_soldier.score - duty_weight)
                    old_soldier.save()
                    new_soldier.score += duty_weight
                    new_soldier.save()
                    
                    # 2. Сменяме човека в наряда
                    swap.shift.soldier = new_soldier
                    swap.shift.save()
                    
                    # 3. Затваряме заявката
                    swap.status = 'approved'
                    swap.save()
                    messages.success(request, f"✅ Смяната е ОДОБРЕНА: {new_soldier.last_name} поема наряда.")
            
            elif action == 'reject_swap':
                swap.status = 'rejected'
                swap.save()
                messages.error(request, "❌ Смяната беше отхвърлена.")

        # --- ФАЗА 3 -> ФАЗА 4: Финализиране и Утвърждаване ---
        elif action == 'finalize':
            # Убиваме всички останали висящи смени на борсата
            ShiftSwapRequest.objects.filter(
                shift__date__year=target_year, shift__date__month=target_month, status__in=['open', 'waiting']
            ).update(status='rejected')
            # Правим графика официален
            shifts.filter(status='public_draft').update(status='official')
            messages.success(request, "🔒 Графикът е УТВЪРДЕН! Борсата за този месец е затворена.")

        # Рефрешваме страницата след действие
        return redirect(f"/roster/lifecycle/?year={target_year}&month={target_month}")

    # 3. ПОДГОТОВКА НА ДАННИТЕ ЗА ИЗГЛЕДА
    context = {
        'target_year': target_year,
        'target_month': target_month,
        'phase': phase,
        'shifts_count': shifts.count(),
    }
    
    if phase == 1:
        context['pref_count'] = ShiftPreference.objects.filter(date__year=target_year, date__month=target_month).values('soldier').distinct().count()
    elif phase == 3:
        context['pending_swaps'] = ShiftSwapRequest.objects.filter(shift__date__year=target_year, shift__date__month=target_month, status='waiting')
        context['open_swaps'] = ShiftSwapRequest.objects.filter(shift__date__year=target_year, shift__date__month=target_month, status='open')

    return render(request, 'roster/roster_lifecycle.html', context)

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
   
# --- АПИ 1: Взимане на съобщенията за телефона ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_announcements(request):
    """ Връща разписките за АКТИВНИТЕ съобщения за този курсант """
    soldier = request.user.soldier
    
    # Тъй като бекендът вече автоматично създава разписки за правилните хора,
    # тук просто дърпаме разписките на този войник!
    receipts = AnnouncementReceipt.objects.filter(
        soldier=soldier,
        announcement__is_active=True
    ).select_related('announcement').order_by('-announcement__created_at')
    
    data = []
    for r in receipts:
        data.append({
            "receipt_id": r.id, # Важно за следващата стъпка!
            "title": r.announcement.title,
            "type": r.announcement.announcement_type,
            "type_display": r.announcement.get_announcement_type_display(),
            "message": r.announcement.message,
            "date": r.announcement.created_at.strftime('%d.%m.%Y %H:%M'),
            "is_read": r.is_read
        })
        
    return Response({
        "status": "success",
        "alerts": data
    })

# --- АПИ 2: Цъкане на бутона "РАЗБРАХ" от телефона ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_acknowledge_alert(request):
    soldier = request.user.soldier
    receipt_id = request.data.get('receipt_id')

    if not receipt_id:
        return Response({"detail": "Липсва ID на разписката."}, status=400)

    try:
        receipt = AnnouncementReceipt.objects.get(id=receipt_id, soldier=soldier)
        
        # Ако вече не го е прочел, го маркираме
        if not receipt.is_read:
            receipt.is_read = True
            receipt.read_at = timezone.now() # Записваме точния час и секунда!
            receipt.save()
            
        return Response({"status": "success", "message": "Оповестяването е маркирано като прочетено."})
        
    except AnnouncementReceipt.DoesNotExist:
        return Response({"detail": "Разписката не е намерена или нямаш достъп до нея."}, status=404)


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
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_daily_roster(request):
    date_str = request.GET.get('date')
    
    if date_str:
        try:
            target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"detail": "Грешен формат на датата. Използвайте YYYY-MM-DD."}, status=400)
    else:
        target_date = datetime.date.today()

    shifts = DutyShift.objects.filter(
        date=target_date
    ).exclude(status='admin_draft').select_related('soldier', 'duty_type').order_by('-duty_type__weight')
    
    data = []
    for shift in shifts:
        data.append({
            "duty_name": shift.duty_type.name,
            "soldier_name": f"{shift.soldier.rank_title} {shift.soldier.smart_name}",
            "company": shift.soldier.company,
            "status": shift.status # public_draft или official
        })
        
    return Response({
        "status": "success",
        "date": target_date.strftime('%Y-%m-%d'),
        "shifts": data
    })
    
from .models import ShiftSwapRequest

# --- БОРСА 1: Виж какво има на борсата (GET) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_market_list(request):
    """ Връща всички наряди, които в момента търсят заместник """
    # Взимаме само отворените заявки от бъдещи дати
    open_requests = ShiftSwapRequest.objects.filter(
        status='open',
        shift__date__gte=datetime.date.today()
    ).select_related('shift', 'shift__duty_type', 'requester')

    data = []
    for req in open_requests:
        data.append({
            "swap_id": req.id,
            "date": req.shift.date.strftime('%Y-%m-%d'),
            "duty_name": req.shift.duty_type.name,
            "requester_name": f"{req.requester.rank_title} {req.requester.last_name}",
            "reason": req.reason
        })
        
    return Response({"status": "success", "market_items": data})


# --- БОРСА 2: Пусни твоя наряд на борсата (POST) ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_market_put(request):
    """ Курсант пуска свой наряд на борсата """
    soldier = request.user.soldier
    shift_id = request.data.get('shift_id')
    reason = request.data.get('reason')

    if not shift_id or not reason:
        return Response({"detail": "Липсват данни (shift_id, reason)."}, status=400)

    try:
        shift = DutyShift.objects.get(id=shift_id, soldier=soldier)
    except DutyShift.DoesNotExist:
        return Response({"detail": "Този наряд не е твой или не съществува."}, status=403)

    if shift.date < datetime.date.today():
        return Response({"detail": "Не можеш да сменяш минали наряди."}, status=400)

    # Създаваме заявката в Борсата
    swap, created = ShiftSwapRequest.objects.get_or_create(
        shift=shift,
        defaults={'requester': soldier, 'reason': reason}
    )

    if not created:
        return Response({"detail": "Този наряд вече е пуснат на борсата!"}, status=400)

    return Response({"status": "success", "message": "Нарядът е пуснат на борсата успешно!"})


# --- БОРСА 3: Вземи чужд наряд от борсата (POST) ---
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_market_take(request):
    """ Друг курсант се съгласява да вземе наряда """
    soldier = request.user.soldier
    swap_id = request.data.get('swap_id')

    swap = get_object_or_404(ShiftSwapRequest, id=swap_id)

    if swap.status != 'open':
        return Response({"detail": "Този наряд вече не е наличен на борсата."}, status=400)
    
    if swap.requester == soldier:
        return Response({"detail": "Не можеш да вземеш собствения си наряд."}, status=400)

    # Проверяваме дали кандидатът нарушава 24-часовата почивка (Вчера, Днес или Утре)
    if DutyShift.objects.filter(
        soldier=soldier, 
        date__in=[
            swap.shift.date, 
            swap.shift.date - datetime.timedelta(days=1), 
            swap.shift.date + datetime.timedelta(days=1)
        ]
    ).exists():
        return Response({"detail": "Нарушаваш 24-часовата почивка! Вече си наряд вчера, днес или утре."}, status=400)

    # Променяме статуса и записваме кандидата
    swap.substitute = soldier
    swap.status = 'waiting' # Чака Капитана!
    swap.save()

    return Response({"status": "success", "message": "Ти предложи да вземеш наряда. Чака се одобрение от Капитан."})

# ==========================================
# 🖨️ ЕКСПОРТ НА ГРАФИКА ЗА ПРИНТЕР (PDF)
# ==========================================
from collections import OrderedDict

@user_passes_test(lambda u: u.is_superuser)
def monthly_export_print(request, year, month):
    # Взимаме САМО утвърдените наряди
    shifts = DutyShift.objects.filter(
        date__year=year, 
        date__month=month,
        status='official'
    ).select_related('soldier', 'duty_type', 'soldier__rank_group').order_by(
        '-soldier__rank_group__priority', 'soldier__last_name', 'date'
    )
    
    # Речник за структуриране: { '5-ти курс': { soldier_id: { 'soldier': obj, 'shifts': [shift1, shift2] } } }
    course_data = OrderedDict()
    
    for shift in shifts:
        course = shift.soldier.rank_group.name
        if course not in course_data:
            course_data[course] = OrderedDict()
            
        s_id = shift.soldier.id
        if s_id not in course_data[course]:
            course_data[course][s_id] = {
                'soldier': shift.soldier,
                'shifts': []
            }
            
        course_data[course][s_id]['shifts'].append(shift)
        
    # Преобразуваме речниците в списъци, за да е лесно за HTML шаблона
    final_export_data = []
    for course, soldiers_dict in course_data.items():
        final_export_data.append({
            'course_name': course,
            'records': list(soldiers_dict.values())
        })
        
    month_date = datetime.date(year, month, 1)
    
    context = {
        'year': year,
        'month': month,
        'month_date': month_date,
        'export_data': final_export_data,
    }
    return render(request, 'roster/monthly_print.html', context)

# ==========================================
# 🌴 ГЕНЕРАТОР НА ОТПУСКИ (УИКЕНД)
# ==========================================
@user_passes_test(lambda u: u.is_superuser)
def generate_weekend_leaves(request):
    if request.method == 'POST':
        friday_str = request.POST.get('friday_date')
        company = request.POST.get('company')
        
        try:
            # Използваме datetime.datetime за да не се бърка с обикновения date
            friday_date = datetime.datetime.strptime(friday_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "❌ Невалидна дата!")
            return redirect('roster_stats')

        # Филтрираме войниците според избраната рота
        soldiers = Soldier.objects.filter(is_active=True)
        if company != 'all':
            soldiers = soldiers.filter(company=company)

        saturday = friday_date + datetime.timedelta(days=1)
        sunday = friday_date + datetime.timedelta(days=2)
        monday = friday_date + datetime.timedelta(days=3)

        created_count = 0

        with transaction.atomic():
            # Защита: Изтриваме старите автоматични отпуски за този уикенд, 
            # за да не се дублират, ако цъкнеш бутона два пъти по погрешка!
            Leave.objects.filter(
                soldier__in=soldiers,
                leave_type='city',
                reason="Авто-Уикенд",
                start_date__gte=datetime.datetime.combine(friday_date, datetime.time(0, 0))
            ).delete()

            for soldier in soldiers:
                # Взимаме курса (напр. "4-ти курс" -> 4)
                try:
                    course_year = int(soldier.rank_group.name.split('-')[0])
                except ValueError:
                    course_year = 1 # Дефолт

                # Проверяваме нарядите
                has_fri_duty = DutyShift.objects.filter(soldier=soldier, date=friday_date).exists()
                has_sat_duty = DutyShift.objects.filter(soldier=soldier, date=saturday).exists()
                has_sun_duty = DutyShift.objects.filter(soldier=soldier, date=sunday).exists()

                # СТАНДАРТЕН КРАЙ НА ОТПУСКАТА
                if course_year == 5:
                    standard_end = datetime.datetime.combine(monday, datetime.time(6, 30))
                else:
                    standard_end = datetime.datetime.combine(sunday, datetime.time(21, 0))

                leaves_to_create = []

                if has_sat_duty:
                    # ⚠️ Наряд Събота -> Две разкъсани отпуски
                    if not has_fri_duty:
                        leaves_to_create.append({
                            'start': datetime.datetime.combine(friday_date, datetime.time(17, 30)),
                            'end': datetime.datetime.combine(friday_date, datetime.time(21, 0))
                        })
                    if not has_sun_duty:
                        leaves_to_create.append({
                            'start': datetime.datetime.combine(sunday, datetime.time(8, 0)),
                            'end': standard_end
                        })
                elif has_sun_duty:
                    # ⚠️ Наряд Неделя -> Съкратена отпуска
                    if not has_fri_duty:
                        leaves_to_create.append({
                            'start': datetime.datetime.combine(friday_date, datetime.time(17, 30)),
                            'end': datetime.datetime.combine(saturday, datetime.time(21, 0))
                        })
                else:
                    # ✅ Свободен уикенд (Ако е бил наряд петък, излиза събота 08:00)
                    start_time = datetime.datetime.combine(saturday, datetime.time(8, 0)) if has_fri_duty else datetime.datetime.combine(friday_date, datetime.time(17, 30))
                    leaves_to_create.append({
                        'start': start_time,
                        'end': standard_end
                    })

                # Записваме в базата
                for l in leaves_to_create:
                    Leave.objects.create(
                        soldier=soldier,
                        start_date=l['start'],
                        end_date=l['end'],
                        leave_type='city',
                        reason="Авто-Уикенд"
                    )
                    created_count += 1

        messages.success(request, f"✅ Успешно генерирани {created_count} отпуски за {soldiers.count()} души!")
        return redirect('roster_stats')

    return redirect('roster_stats')

# ==========================================
# 🛂 КПП / ЕЖЕДНЕВНИ ОТПУСКИ
# ==========================================
@user_passes_test(lambda u: u.is_superuser)
def daily_leave_manager(request):
    
    date_str = request.GET.get('date') or request.POST.get('date')
    if date_str:
        try:
            target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = datetime.date.today()
    else:
        target_date = datetime.date.today()

    next_day = target_date + datetime.timedelta(days=1)
    weekday = target_date.weekday() # 0=Пон, 1=Вто, 2=Сря, 3=Чет, 4=Пет, 5=Съб, 6=Нед

    if request.method == 'POST':
        action = request.POST.get('action')
        
        # --- 1. ГЕНЕРИРАНЕ ПО ПРАВИЛА ---
        if action == 'generate':
            # Изтриваме стари чернови за деня
            Leave.objects.filter(start_date__date=target_date, leave_type='city', status='draft').delete()
            
            soldiers = Soldier.objects.filter(is_active=True)
            created_count = 0
            
            for s in soldiers:
                # Ако днес е наряд, не излиза!
                if DutyShift.objects.filter(soldier=s, date=target_date).exists():
                    continue

                try: course_year = int(s.rank_group.name.split('-')[0])
                except ValueError: course_year = 1
                
                has_duty_next = DutyShift.objects.filter(soldier=s, date=next_day).exists()
                
                should_go = False
                return_date = target_date
                return_time = datetime.time(21, 0) # По дефолт 21:00 същия ден
                
                # --- ЛОГИКА ПЕТЪК (УИКЕНД) ---
                if weekday == 4:
                    should_go = True
                    if course_year == 5:
                        return_date = target_date + datetime.timedelta(days=3) # Понеделник
                        return_time = datetime.time(6, 30)
                    else:
                        return_date = target_date + datetime.timedelta(days=2) # Неделя
                        return_time = datetime.time(21, 0)
                
                # --- ЛОГИКА ДЕЛНИК (ПОН-ЧЕТВЪРТЪК) ---
                elif weekday in [0, 1, 2, 3]:
                    if course_year == 5:
                        should_go = True
                        return_date = next_day
                        return_time = datetime.time(6, 30)
                    elif course_year == 4:
                        should_go = True
                        if s.has_scholarship:
                            return_date = next_day
                            return_time = datetime.time(5, 40)
                        else:
                            return_time = datetime.time(21, 0)
                    elif course_year in [2, 3] and weekday == 2 and s.has_scholarship: # Сряда със стипендия
                        should_go = True
                        return_time = datetime.time(21, 0)
                
                if should_go:
                    # ЖЕЛЯЗНО ПРАВИЛО: Ако утре си наряд, се прибираш днес в 21:00!
                    if has_duty_next:
                        return_date = target_date
                        return_time = datetime.time(21, 0)
                        
                    start_dt = datetime.datetime.combine(target_date, datetime.time(17, 30))
                    end_dt = datetime.datetime.combine(return_date, return_time)
                    
                    Leave.objects.create(soldier=s, start_date=start_dt, end_date=end_dt, leave_type='city', reason="Автоматична", status='draft')
                    created_count += 1
            
            messages.success(request, f"✅ Успешно генерирана чернова с {created_count} отпуски по устав!")

# --- 2. РЪЧНО ДОБАВЯНЕ (ПО ЗАСЛУГИ / РАБОТНА ГРУПА) ---
        elif action == 'add_manual':
            soldier_ids = request.POST.getlist('soldier_ids') # ВЕЧЕ ВЗИМАМЕ СПИСЪК С ХОРА
            custom_return = request.POST.get('custom_return', '21:00')
            
            for sid in soldier_ids:
                s = Soldier.objects.get(id=sid)
                
                # Определяме часа спрямо избора на Капитана
                return_date = target_date
                if custom_return == '05:40':
                    return_date = next_day
                    return_time = datetime.time(5, 40)
                elif custom_return == '06:30':
                    return_date = next_day
                    return_time = datetime.time(6, 30)
                else:
                    return_time = datetime.time(21, 0)
                
                # ЖЕЛЯЗНО: Ако утре е наряд, задължително го връщаме в 21:00!
                has_duty_next = DutyShift.objects.filter(soldier=s, date=next_day).exists()
                if has_duty_next and custom_return in ['05:40', '06:30']:
                    return_date = target_date
                    return_time = datetime.time(21, 0)
                    messages.warning(request, f"⚠️ {s.last_name} е наряд утре! Часът му автоматично бе върнат на 21:00.")

                start_dt = datetime.datetime.combine(target_date, datetime.time(17, 30))
                end_dt = datetime.datetime.combine(return_date, return_time)
                
                Leave.objects.create(soldier=s, start_date=start_dt, end_date=end_dt, leave_type='city', reason="Група/Заслуги", status='draft')
                active_star = s.disciplinary_records.filter(record_type='star', is_active=True).first()
                if active_star:
                    active_star.is_active = False
                    active_star.reason += " (⭐ Използвана за отпуска)"
                    active_star.save()            
            if soldier_ids:
                messages.success(request, f"🎖️ Успешно добавени {len(soldier_ids)} души в списъка!")

        # --- 3. УТВЪРЖДАВАНЕ ---
        elif action == 'publish':
            Leave.objects.filter(start_date__date=target_date, leave_type='city', status='draft').update(status='official')
            messages.warning(request, "📢 Отпуските са утвърдени! Вече се виждат в приложението и на КПП-то.")

        # --- 4. ПРЕМАХВАНЕ НА КОНКРЕТЕН ЧОВЕК (НОВО) ---
        elif action == 'remove_leave':
            leave_id = request.POST.get('leave_id')
            if leave_id:
                leave_to_delete = get_object_or_404(Leave, id=leave_id)
                soldier_name = leave_to_delete.soldier.last_name
                leave_to_delete.delete()
                messages.success(request, f"🗑️ {soldier_name} беше премахнат от списъка за днес.")
                
# --- 5. ПРОМЯНА НА ЧАСА С МОЛИВЧЕТО (НОВО) ---
        elif action == 'edit_time':
            leave_id = request.POST.get('leave_id')
            new_datetime = request.POST.get('new_datetime')
            if leave_id and new_datetime:
                try:
                    dt = datetime.datetime.strptime(new_datetime, '%Y-%m-%dT%H:%M')
                    Leave.objects.filter(id=leave_id).update(end_date=dt)
                    messages.success(request, "⏱️ Часът за прибиране е обновен успешно!")
                except ValueError:
                    messages.error(request, "❌ Невалиден формат на датата/часа.")

        return redirect(f"/roster/leaves/daily/?date={target_date.strftime('%Y-%m-%d')}")
    

    # --- ДАННИ ЗА ИЗГЛЕДА ---
    leaves = Leave.objects.filter(
        start_date__date=target_date, 
        leave_type__in=['city', 'home']
    ).select_related('soldier', 'soldier__rank_group').order_by(
        '-soldier__rank_group__priority', 'soldier__company', 'soldier__last_name'
    )
    
    # За падащото меню изключваме хората, които вече имат генерирана отпуска днес
    busy_ids = leaves.values_list('soldier_id', flat=True)
    available_soldiers = Soldier.objects.filter(is_active=True).exclude(id__in=busy_ids).annotate(
        stars_count=Count('disciplinary_records', filter=Q(disciplinary_records__record_type='star', disciplinary_records__is_active=True))
    ).order_by('-stars_count', 'company', 'last_name')
    context = {
        'target_date': target_date,
        'leaves': leaves,
        'available_soldiers': available_soldiers,
        'has_drafts': leaves.filter(status='draft').exists(),
        'has_official': leaves.filter(status='official').exists()
    }
    return render(request, 'roster/daily_leave_manager.html', context)

# ==========================================
# 🖨️ ЕКСПОРТ НА ОТПУСКИ ЗА КПП (PDF)
# ==========================================
@user_passes_test(lambda u: u.is_superuser)
def daily_leave_print(request, date_str):
    try:
        target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        target_date = datetime.date.today()

    # Взимаме САМО утвърдените отпуски (ГО и ДО) за тази дата
    leaves = Leave.objects.filter(
        start_date__date=target_date, 
        leave_type__in=['city', 'home'],
        status='official'
    ).select_related('soldier', 'soldier__rank_group').order_by(
        'soldier__company', 'soldier__platoon', 'soldier__last_name'
    )
    
    # Групираме ги по Роти за по-лесно четене на КПП-то
    from collections import OrderedDict
    leaves_by_company = OrderedDict()
    
    for l in leaves:
        comp = f"{l.soldier.company} рота" if l.soldier.company in ['1', '2'] else "Млади курсанти"
        if comp not in leaves_by_company:
            leaves_by_company[comp] = []
        leaves_by_company[comp].append(l)

    context = {
        'target_date': target_date,
        'leaves_by_company': leaves_by_company,
    }
    return render(request, 'roster/daily_leave_print.html', context)