from django.core.management.base import BaseCommand
from roster.models import DutyType

class Command(BaseCommand):
    help = 'Създава основните видове наряди за ВВМУ'

    def handle(self, *args, **kwargs):
        self.stdout.write("⚙️ Създаване на видове наряди...")

        # Списък с нарядите, които fix_duties.py очаква
        duties_data = [
            # 5-ти курс
            {"name": "ДБПК (Дежурен по БПК)", "weight": 6, "people": 1},
            
            # 4-ти курс
            {"name": "ПДБПК (Пом. дежурен по БПК)", "weight": 5, "people": 1},
            {"name": "ПДУ (Пом. дежурен по училище)", "weight": 5, "people": 1},
            
            # 3-ти курс
            {"name": "ДР 1-ва Рота (Дежурен)", "weight": 4, "people": 1},
            {"name": "ДР 2-ра Рота (Дежурен)", "weight": 4, "people": 1},
            
            # 2-ри курс
            {"name": "ДУСК (Дежурен учебен корпус)", "weight": 3, "people": 1},
            {"name": "ПДКПП (Пом. дежурен КПП)", "weight": 3, "people": 1},
            
            # 1-ви и 2-ри курс Стоянов, ПЕтров, Михайлов
            {"name": "ДН 1-ва Рота (Дневален)", "weight": 2, "people": 3},
            {"name": "ДН 2-ра Рота (Дневален)", "weight": 2, "people": 3},
        ]

        created_count = 0
        for data in duties_data:
            obj, created = DutyType.objects.get_or_create(
                name=data["name"],
                defaults={
                    "weight": data["weight"],
                    "people_required": data["people"]
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Готово! Създадени са {created_count} вида наряди."))