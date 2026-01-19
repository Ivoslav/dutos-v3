from django.core.management.base import BaseCommand
from roster.models import DutyType, CourseOrRank

class Command(BaseCommand):
    help = 'Настройва нарядите по новите строги правила'

    def handle(self, *args, **kwargs):
        self.stdout.write("⚙️ Настройване на правилата за наряди...")

        # 1. Намираме курсовете
        try:
            c1 = CourseOrRank.objects.get(name__icontains="1") # 1-ви курс
            c2 = CourseOrRank.objects.get(name__icontains="2") # 2-ри курс
            c3 = CourseOrRank.objects.get(name__icontains="3") # 3-ти курс
            c4 = CourseOrRank.objects.get(name__icontains="4") # 4-ти курс
            c5 = CourseOrRank.objects.get(name__icontains="5") # 5-ти курс
        except CourseOrRank.DoesNotExist:
            self.stdout.write(self.style.ERROR("ГРЕШКА: Някой курс липсва! Първо пусни seed_data."))
            return

        # 2. Изчистваме старите правила за всички наряди (за всеки случай)
        for d in DutyType.objects.all():
            d.allowed_ranks.clear()

        # --- ПРАВИЛО 1: ДБПК -> 5-ти курс ---
        # Важно: Търсим да ЗАПОЧВА с ДБПК, за да не хване ПДБПК
        dbpk_duties = DutyType.objects.filter(name__startswith="ДБПК")
        for d in dbpk_duties:
            d.allowed_ranks.set([c5])
            self.stdout.write(f"   -> {d.name}: 5-ти курс")

        # --- ПРАВИЛО 2: ПДБПК и ПДУ -> 4-ти курс ---
        # Regex означава: името започва с ПДБПК ИЛИ ПДУ
        senior_duties = DutyType.objects.filter(name__regex=r'^(ПДБПК|ПДУ)')
        for d in senior_duties:
            d.allowed_ranks.set([c4])
            self.stdout.write(f"   -> {d.name}: 4-ти курс")

        # --- ПРАВИЛО 3: ДР (Дежурен Рота) -> 3-ти курс ---
        dr_duties = DutyType.objects.filter(name__startswith="ДР")
        for d in dr_duties:
            d.allowed_ranks.set([c3])
            self.stdout.write(f"   -> {d.name}: 3-ти курс")

        # --- ПРАВИЛО 4: ДУСК и ПДКПП -> 2-ри курс ---
        mid_duties = DutyType.objects.filter(name__regex=r'^(ДУСК|ПДКПП)')
        for d in mid_duties:
            d.allowed_ranks.set([c2])
            self.stdout.write(f"   -> {d.name}: 2-ри курс")

        # --- ПРАВИЛО 5: ДН (Дневални) -> 1-ви и 2-ри курс ---
        dn_duties = DutyType.objects.filter(name__startswith="ДН")
        for d in dn_duties:
            d.allowed_ranks.set([c1, c2])
            self.stdout.write(f"   -> {d.name}: 1-ви и 2-ри курс")

        self.stdout.write(self.style.SUCCESS("✅ Правилата са коригирани успешно!"))