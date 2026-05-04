from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
import datetime
from datetime import timedelta
import random
import re
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.views.decorators.http import require_POST
from roster.forms import DutyShiftForm, BatchLeaveForm

from roster.models import (
    Soldier, DutyShift, Leave, Announcement, 
    AnnouncementReceipt, ShiftPreference, DisciplinaryRecord
)

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

def emergency_list(request):
    soldiers = Soldier.objects.filter(is_active=True).order_by('company', 'platoon', 'last_name')
    
    context = {
        'soldiers': soldiers,
        # ПРОМЯНАТА Е ТУК: Ползваме .now(), а не .today()
        'today': datetime.datetime.now(), 
    }
    return render(request, 'roster/emergency_print.html', context)

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