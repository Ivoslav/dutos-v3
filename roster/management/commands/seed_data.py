import random
from django.core.management.base import BaseCommand
from roster.models import Soldier, CourseOrRank, DutyShift

class Command(BaseCommand):
    help = 'Генерира СТРОГА йерархия: 5-ти курс са само Мичмани, 109-231 са само в 3-ти курс'

    def handle(self, *args, **kwargs):
        self.stdout.write("🧹 Изтривам старата армия...")
        DutyShift.objects.all().delete()
        Soldier.objects.all().delete()
        
        # 1. СЪЗДАВАНЕ НА КУРСОВЕТЕ (Ако ги няма)
        required_courses = [
            ("1-ви курс", 1), ("2-ри курс", 2), ("3-ти курс", 3),
            ("4-ти курс", 4), ("5-ти курс", 5)
        ]
        active_courses = {} # Речник за бърз достъп по име
        
        for name, priority in required_courses:
            course_obj, _ = CourseOrRank.objects.get_or_create(name=name, defaults={'priority': priority})
            # Запазваме ги, за да ги ползваме конкретно по-долу
            key = name.split("-")[0] # "1", "2", "3"...
            active_courses[key] = course_obj

        first_names = ["Иван", "Петър", "Георги", "Димитър", "Николай", "Тодор", "Александър", "Виктор", "Мартин", "Даниел", "Борис", "Калоян", "Стефан", "Христо", "Ангел"]
        last_names = ["Иванов", "Петров", "Георгиев", "Димитров", "Стоянов", "Андреев", "Михайлов", "Попов", "Колев", "Николов", "Василев", "Тодоров", "Христов", "Ангелов"]
        specialties_normal = ['101', '102', '103', '110', '181'] 

        self.stdout.write("🌱 Започвам генериране на 150 бойци със строга дисциплина...")
        created_count = 0
        
        while created_count < 150:
            # Избираме случайно число от 1 до 5, за да определим курса
            year = random.choice(["1", "2", "3", "4", "5"])
            course_obj = active_courses[year]
            
            # Нулираме променливите
            rank = ""
            platoon = ""
            company = random.choice(['1', '2'])
            fac_prefix = ""
            fac_suffix = ""

            # --- ЛОГИКА ПО ГОДИНИ (Твърди правила) ---
            
            if year == "1":
                # 1-ВИ КУРС: Млади курсанти, 4 цифри (1014-251..)
                rank = "Курсант"
                platoon = "Млади"
                base_spec = random.choice(specialties_normal + ['106']) # И доктори може да има
                fac_prefix = base_spec + "4"
                fac_suffix = "251"

            elif year == "2":
                # 2-РИ КУРС: Старшини II степен (-241..)
                rank = "Ст. II ст."
                platoon = random.choice(['1', '2', '3', '4'])
                fac_prefix = random.choice(specialties_normal + ['106'])
                fac_suffix = "241"

            elif year == "3":
                # 3-ТИ КУРС: Старшини I степен (-231..)
                rank = "Ст. I ст."
                platoon = random.choice(['1', '2', '3', '4'])
                fac_suffix = "231"
                
                # ТУК Е МЯСТОТО НА СПЕЦИАЛНАТА ГРУПА 109
                if random.random() < 0.15: # 15% от 3-ти курс са специалните
                    fac_prefix = "109"
                else:
                    fac_prefix = random.choice(specialties_normal + ['106'])

            elif year == "4":
                # 4-ТИ КУРС: Главни старшини (-221..)
                rank = "Гл. старшина"
                platoon = random.choice(['1', '2', '3', '4'])
                fac_suffix = "221"
                fac_prefix = random.choice(specialties_normal + ['106']) # 106 са докторите

            elif year == "5":
                # 5-ТИ КУРС: Мичмани (-211..)
                rank = "Мичман"
                platoon = random.choice(['1', '2', '3', '4'])
                fac_suffix = "211"
                fac_prefix = random.choice(specialties_normal + ['106'])
                
                # В 5-ти курс НЯМА 109-231, НЯМА Курсанти!

            # Генериране на номера
            student_num = f"{random.randint(1, 35):02d}"
            full_fac_number = f"{fac_prefix}-{fac_suffix}{student_num}"

            # Проверка за дублаж
            if Soldier.objects.filter(faculty_number=full_fac_number).exists():
                continue

            crew_name = f"Екипаж {random.randint(1, 10)}" if random.random() > 0.3 else ""

            Soldier.objects.create(
                first_name=random.choice(first_names),
                last_name=random.choice(last_names),
                faculty_number=full_fac_number,
                rank_title=rank,
                rank_group=course_obj,
                company=company,
                platoon=platoon,
                crew=crew_name,
                score=random.randint(0, 5)
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Готово! Армията е пренаредена без грешки в йерархията.'))