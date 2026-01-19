import random
from django.core.management.base import BaseCommand
from roster.models import Soldier, CourseOrRank, DutyShift

class Command(BaseCommand):
    help = 'Генерира 150 тестови войници (Изтрива старите!)'

    def handle(self, *args, **kwargs):
        # 1. ЧИСТКА НА СТАРИТЕ ДАННИ
        self.stdout.write("🧹 Изтривам старите записи...")
        DutyShift.objects.all().delete() # Първо нарядите (защото са свързани с хората)
        Soldier.objects.all().delete()   # После хората
        
        # 2. Списъци с данни
        first_names = ["Иван", "Петър", "Георги", "Димитър", "Николай", "Тодор", "Александър", "Виктор", "Мартин", "Даниел", "Борис", "Калоян", "Стефан"]
        last_names = ["Иванов", "Петров", "Георгиев", "Димитров", "Стоянов", "Андреев", "Михайлов", "Попов", "Колев", "Николов", "Василев", "Тодоров"]
        
        courses = list(CourseOrRank.objects.all())
        
        if not courses:
            self.stdout.write(self.style.ERROR('ГРЕШКА: Няма курсове! Създай ги в Админа.'))
            return

        self.stdout.write("🌱 Започвам генериране на 150 нови бойци...")

        # 3. Създаваме 150 войника
        created_count = 0
        
        while created_count < 150:
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            random_course = random.choice(courses)
            
            # ПО-ГОЛЯМ ДИАПАЗОН (10000 до 99999) - по-малък шанс за дубъл
            fak_nom = f"111-{random.randint(10000, 99999)}"
            
            # Проверка дали случайно не сме генерирали същото число току-що
            if Soldier.objects.filter(faculty_number=fak_nom).exists():
                continue # Пробвай пак с ново число

            # Логика за званията
            rank = "Курсант"
            if "2" in random_course.name: rank = "Ст. II ст."
            elif "3" in random_course.name: rank = "Ст. I ст."
            elif "4" in random_course.name: rank = "Гл. старшина"
            elif "5" in random_course.name: rank = "Мичман"

            Soldier.objects.create(
                first_name=fname,
                last_name=lname,
                faculty_number=fak_nom,
                rank_title=rank,
                rank_group=random_course,
                company=random.choice(['1', '2', '3']),
                platoon=random.choice(['1', '2', '3', '4']),
                score=random.randint(0, 5) # По-малко точки в началото
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Готово! Базата е обновена с 150 уникални войника.'))