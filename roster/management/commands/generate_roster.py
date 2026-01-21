import datetime
from datetime import timedelta
from django.core.management.base import BaseCommand
from roster.models import Soldier, DutyType, DutyShift, Leave

class Command(BaseCommand):
    help = 'Генерира график със строги правила за почивка'

    def add_arguments(self, parser):
        parser.add_argument('date', type=str, help='Дата във формат YYYY-MM-DD')

    def handle(self, *args, **kwargs):
        date_str = kwargs['date']
        target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        yesterday = target_date - timedelta(days=1)
        
        self.stdout.write(f"⚙️  ПЛАНИРАНЕ ЗА: {target_date}")

        # 1. СЪЗДАВАМЕ ЧЕРЕН СПИСЪК (Blacklist)
        
        # А) Хора, които са били наряд ВЧЕРА (Умора)
        tired_soldiers_ids = list(DutyShift.objects.filter(date=yesterday).values_list('soldier_id', flat=True))
        
        # Б) Хора, които ВЕЧЕ са назначени ДНЕС
        assigned_today_ids = list(DutyShift.objects.filter(date=target_date).values_list('soldier_id', flat=True))

        # В) НОВО: Хора, които са в ОТПУСК/БОЛНИЧЕН на тази дата
        # Търсим записи, където target_date попада между start и end date
        absent_soldiers_ids = list(Leave.objects.filter(
            start_date__lte=target_date, 
            end_date__gte=target_date
        ).values_list('soldier_id', flat=True))

        # Събираме всички забранени в един множество (set), за да няма дубъл
        all_forbidden_ids = set(tired_soldiers_ids + assigned_today_ids + absent_soldiers_ids)
        
        self.stdout.write(f"🚫 Статистика на липсващите:")
        self.stdout.write(f"   - Уморени от вчера: {len(tired_soldiers_ids)}")
        self.stdout.write(f"   - В отпуск/болничен: {len(absent_soldiers_ids)}")
        self.stdout.write(f"   - Общо недостъпни: {len(all_forbidden_ids)}")

        # Взимаме нарядите, сортирани по приоритет (за да напълним важните първо)
        duties = DutyType.objects.all().order_by('-weight')

        for duty in duties:
            required = duty.people_required
            self.stdout.write(f"\n--- {duty.name} (Търсят се: {required}) ---")

            # Кой има право по звание?
            allowed_courses = duty.allowed_ranks.all()
            
            # Взимаме кандидатите
            candidates = Soldier.objects.filter(rank_group__in=allowed_courses, is_active=True)
            
            # ФИЛТРАЦИЯ: Махаме всички от черния списък
            candidates = candidates.exclude(id__in=all_forbidden_ids)
            
            # Сортиране по точки
            candidates = list(candidates.order_by('score', '?'))

            # Проверка за наличност
            if len(candidates) < required:
                self.stdout.write(self.style.ERROR(f"⚠️  КРИЗА! Няма достатъчно хора за {duty.name}. Има {len(candidates)}, трябват {required}."))
                # Взимаме колкото има
                selected = candidates
            else:
                selected = candidates[:required]

            # НАЗНАЧАВАНЕ
            for s in selected:
                DutyShift.objects.create(date=target_date, duty_type=duty, soldier=s)
                
                # Добавяме точки
                s.score += duty.weight
                s.save()
                
                # ВАЖНО: Добавяме го веднага в черния списък за днес!
                all_forbidden_ids.add(s.id)
                
                self.stdout.write(self.style.SUCCESS(f"   ✅ {s.rank_title} {s.last_name}"))

        self.stdout.write(f"\n🏁 Готово!")