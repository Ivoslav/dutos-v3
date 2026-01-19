import random
from django.core.management.base import BaseCommand
from roster.models import Soldier, CourseOrRank

class Command(BaseCommand):
    help = 'Генерира тестови войници (Dummy Data)'

    def handle(self, *args, **kwargs):
        # 1. Списъци с данни за миксиране
        first_names = ["Иван", "Петър", "Георги", "Димитър", "Николай", "Тодор", "Александър", "Виктор", "Мартин", "Даниел"]
        last_names = ["Иванов", "Петров", "Георгиев", "Димитров", "Стоянов", "Андреев", "Михайлов", "Попов", "Колев", "Николов"]
        
        # Намираме курсовете, които вече си създал в Админа
        courses = list(CourseOrRank.objects.all())
        
        if not courses:
            self.stdout.write(self.style.ERROR('ГРЕШКА: Няма създадени курсове! Първо създай "1-ви курс" и т.н. в Админ панела.'))
            return

        self.stdout.write("Започвам генериране на бойци...")

        # 2. Създаваме 30 войника
        for i in range(30):
            # Избираме случайно име
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            
            # Избираме случаен курс от наличните
            random_course = random.choice(courses)
            
            # Генерираме случаен факултетен номер (напр. 111-24001)
            # random.randint(10000, 99999) прави 5-цифрено число
            fak_nom = f"111-{random.randint(24000, 24999)}"
            
            # Определяме звание спрямо курса (за по-реалистично)
            # Тук е проста логика, може да я усложним
            rank = "Курсант"
            if "2" in random_course.name: rank = "Ст. II ст."
            elif "3" in random_course.name: rank = "Ст. I ст."
            elif "4" in random_course.name: rank = "Гл. старшина"
            elif "5" in random_course.name: rank = "Мичман"

            # Създаваме записа
            Soldier.objects.create(
                first_name=fname,
                last_name=lname,
                faculty_number=fak_nom,
                rank_title=rank,
                rank_group=random_course,
                company=random.choice(['1', '2', '3']),
                platoon=random.choice(['1', '2', '3', '4']),
                score=random.randint(0, 10) # Случайни точки, все едно са давали наряди
            )

        self.stdout.write(self.style.SUCCESS(f'✅ Готово! Успешно добавени 30 нови бойци.'))