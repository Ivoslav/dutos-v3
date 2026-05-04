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