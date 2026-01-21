import datetime
from datetime import timedelta
from django.core.management.base import BaseCommand
from roster.models import Soldier, DutyType, DutyShift, Leave

class Command(BaseCommand):
    help = 'Генерира график: Приоритет на хората с НАЙ-МАЛКО точки'

    def add_arguments(self, parser):
        parser.add_argument('date', type=str, help='Дата във формат YYYY-MM-DD')

    def handle(self, *args, **kwargs):
        date_str = kwargs['date']
        target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        yesterday = target_date - timedelta(days=1)
        
        self.stdout.write(f"⚙️  ПЛАНИРАНЕ ЗА: {target_date}")

        # 1. ЧЕРЕН СПИСЪК
        tired_soldiers_ids = list(DutyShift.objects.filter(date=yesterday).values_list('soldier_id', flat=True))
        assigned_today_ids = list(DutyShift.objects.filter(date=target_date).values_list('soldier_id', flat=True))
        absent_soldiers_ids = list(Leave.objects.filter(start_date__lte=target_date, end_date__gte=target_date).values_list('soldier_id', flat=True))

        all_forbidden_ids = set(tired_soldiers_ids + assigned_today_ids + absent_soldiers_ids)
        
        self.stdout.write(f"🚫 Липсващи: Уморени ({len(tired_soldiers_ids)}) | Отпуск ({len(absent_soldiers_ids)})")

        # 2. Въртим нарядите
        duties = DutyType.objects.all().order_by('-weight')

        for duty in duties:
            required = duty.people_required
            self.stdout.write(f"\n--- {duty.name} (Търсят се: {required}) ---")

            allowed_courses = duty.allowed_ranks.all()
            candidates = Soldier.objects.filter(rank_group__in=allowed_courses, is_active=True)
            candidates = candidates.exclude(id__in=all_forbidden_ids)
            
            # Сортиране по точки
            candidates = list(candidates.order_by('score', '?'))

            if len(candidates) < required:
                self.stdout.write(self.style.ERROR(f"⚠️  НЯМА ХОРА! Налични: {len(candidates)}"))
                selected = candidates
            else:
                selected = candidates[:required]

            for s in selected:
                DutyShift.objects.create(date=target_date, duty_type=duty, soldier=s)
                
                old_score = s.score # Запазваме старите
                s.score += duty.weight
                s.save()
                
                all_forbidden_ids.add(s.id)
                
                # ДОКАЗАТЕЛСТВОТО: Номер + Промяна на точките
                self.stdout.write(self.style.SUCCESS(
                    f"   ✅ {s.rank_title} {s.last_name} ({s.faculty_number}) | Точки: {old_score} -> {s.score}"
                ))

        self.stdout.write(f"\n🏁 Готово!")