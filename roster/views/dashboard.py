from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
import datetime
from datetime import timedelta
import random
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.views.decorators.http import require_POST

from roster.models import (
    Soldier, DutyShift, Leave, Announcement, 
    AnnouncementReceipt, ShiftPreference, DisciplinaryRecord
)


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
    # НОВО: РАЗДЕЛЯНЕ НА ТРЕВОГИ И ДНЕВЕН РЕД
    # ==========================================
    active_announcements_raw = Announcement.objects.filter(is_active=True).prefetch_related('receipts__soldier').order_by('-created_at')
    
    emergencies_data = []
    routine_data = []
    
    for ann in active_announcements_raw:
        receipts = ann.receipts.all()
        total_count = receipts.count()
        read_count = receipts.filter(is_read=True).count()
        unread_receipts = receipts.filter(is_read=False)
        
        percent = int((read_count / total_count * 100)) if total_count > 0 else 0
        
        data_dict = {
            'obj': ann,
            'total_count': total_count,
            'read_count': read_count,
            'unread_count': total_count - read_count,
            'percent': percent,
            'unread_soldiers': [r.soldier for r in unread_receipts]
        }
        
        if ann.announcement_type in ['alarm', 'fire', 'assembly']:
            emergencies_data.append(data_dict)
        else:
            routine_data.append(data_dict)

    # ИНТЕЛИГЕНТНО ВГРАЖДАНЕ В ДНЕВНИЯ РЕД
    schedule = {
        'morning': {'default': '08:00', 'override': None},
        'lunch': {'default': '13:30', 'override': None},
        'evening': {'default': '20:30', 'override': None},
        'other': []
    }
    
    for item in routine_data:
        t = item['obj'].title.lower()
        if ('сутрин' in t or 'сутрешен' in t) and not schedule['morning']['override']:
            schedule['morning']['override'] = item
        elif ('обед' in t or 'обяд' in t) and not schedule['lunch']['override']:
            schedule['lunch']['override'] = item
        elif 'вечер' in t and not schedule['evening']['override']:
            schedule['evening']['override'] = item
        else:
            schedule['other'].append(item)

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
        'emergencies_data': emergencies_data,
        'schedule': schedule,
    }
    return render(request, 'roster/dashboard.html', context)

@user_passes_test(lambda u: u.is_superuser)
def post_announcement(request):
    if request.method == 'POST':
        announcement_type = request.POST.get('announcement_type', 'info') # НОВО: Взимаме типа
        title = request.POST.get('title')
        message = request.POST.get('message')
        target = request.POST.get('target', 'all')
                
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
    ann_id = request.POST.get('announcement_id')
    if ann_id:
        Announcement.objects.filter(id=ann_id).update(is_active=False)
    else:
        Announcement.objects.filter(is_active=True).update(is_active=False)
        
    messages.success(request, "✅ Оповестяването е отменено (премахнато от таблото).")
    return redirect('roster_home')