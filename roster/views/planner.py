from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
import datetime
from datetime import timedelta
import random
import calendar
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.views.decorators.http import require_POST

from roster.models import (
    ShiftSwapRequest, Soldier, DutyShift, Leave, Announcement, 
    AnnouncementReceipt, ShiftPreference, DisciplinaryRecord, DutyType
)
    
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
            for s in selected:
                DutyShift.objects.create(
                    date=current_date, duty_type=duty, soldier=s, status='admin_draft'
                )
                assigned_today.add(s.id)
                
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


