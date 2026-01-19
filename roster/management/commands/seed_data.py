import random
from django.core.management.base import BaseCommand
from roster.models import Soldier, CourseOrRank, DutyShift

class Command(BaseCommand):
    help = 'Генерира армия: ВМС (1-ва рота, 1-2 отряд, 1-10 екипаж) и Медици (2-ра рота, 3-4 отряд, 11-16 екипаж)'

    def handle(self, *args, **kwargs):
        self.stdout.write("🧹 Изтривам старата армия...")
        DutyShift.objects.all().delete()
        Soldier.objects.all().delete()
        
        # 1. СТРУКТУРА НА КУРСОВЕТЕ
        required_courses = [
            ("1-ви курс", 1), ("2-ри курс", 2), ("3-ти курс", 3),
            ("4-ти курс", 4), ("5-ти курс", 5)
        ]
        active_courses = {}
        for name, priority in required_courses:
            course_obj, _ = CourseOrRank.objects.get_or_create(name=name, defaults={'priority': priority})
            key = name.split("-")[0] 
            active_courses[key] = course_obj

        first_names = ["Иван", "Петър", "Георги", "Димитър", "Николай", "Тодор", "Александър", "Виктор", "Мартин", "Даниел", "Борис", "Калоян", "Стефан", "Валери"]
        last_names = ["Иванов", "Петров", "Георгиев", "Димитров", "Стоянов", "Андреев", "Михайлов", "Попов", "Колев", "Николов", "Василев", "Тодоров", "Маринов"]
        
        # СПИСЪЦИ
        specs_vms = ['101', '102', '103', '110', '181'] # ВМС
        spec_medic = '106'                              # Медици

        self.stdout.write("🌱 Започвам генериране на 150 бойци по новия щат...")
        created_count = 0
        
        while created_count < 150:
            year = random.choice(["1", "2", "3", "4", "5"])
            course_obj = active_courses[year]
            
            # --- 1. ОПРЕДЕЛЯМЕ ВИДА (ВМС или МЕДИК) ---
            # 20% шанс за Медик, 80% за ВМС
            is_medic = random.random() < 0.20
            
            if is_medic:
                # === МЕДИЦИ (Доктори) ===
                base_spec = spec_medic
                company = '2'                        # Само 2-ра рота
                possible_platoons = ['3', '4']       # Само 3-ти и 4-ти отряд
                crew_num = random.randint(11, 16)    # Екипажи 11-16
            else:
                # === ВМС (Всички останали) ===
                base_spec = random.choice(specs_vms)
                company = '1'                        # Само 1-ва рота
                possible_platoons = ['1', '2']       # Само 1-ви и 2-ри отряд
                crew_num = random.randint(1, 10)     # Екипажи 1-10

            # --- 2. НАСТРОЙКИ СПОРЕД КУРСА ---
            rank = ""
            platoon = "" # Избираме крайното тук
            fac_prefix = ""
            fac_suffix = ""

            if year == "1":
                # 1-ВИ КУРС: Винаги са "Млади", независимо дали са медици или ВМС
                rank = "Курсант"
                platoon = "Млади" # Специален статус
                fac_prefix = base_spec + "4" # 1064 или 1014
                fac_suffix = "251"

            elif year == "2":
                rank = "Ст. II ст."
                platoon = random.choice(possible_platoons) # 3/4 за медици, 1/2 за ВМС
                fac_prefix = base_spec
                fac_suffix = "241"

            elif year == "3":
                rank = "Ст. I ст."
                platoon = random.choice(possible_platoons)
                fac_suffix = "231"
                
                # Специалният отряд 109 (Само за ВМС в 1-ва рота)
                if not is_medic and random.random() < 0.15: 
                    fac_prefix = "109"
                    # Те са си ВМС, така че рота 1, отряд 1/2, екипаж 1-10 си остават
                else:
                    fac_prefix = base_spec

            elif year == "4":
                rank = "Гл. старшина"
                platoon = random.choice(possible_platoons)
                fac_suffix = "221"
                fac_prefix = base_spec

            elif year == "5":
                rank = "Мичман"
                platoon = random.choice(possible_platoons)
                fac_suffix = "211"
                fac_prefix = base_spec

            # Сглобяване на номера
            student_num = f"{random.randint(1, 35):02d}"
            full_fac_number = f"{fac_prefix}-{fac_suffix}{student_num}"

            if Soldier.objects.filter(faculty_number=full_fac_number).exists():
                continue

            # Екипаж: Създаваме стринг "Екипаж X"
            # Даваме екипаж на всички от горните курсове, а на 1-ви курс - 50% шанс
            has_crew = True if year != "1" else (random.random() > 0.5)
            crew_name = f"Екипаж {crew_num}" if has_crew else ""

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

        self.stdout.write(self.style.SUCCESS(f'✅ Готово! Армията е разделена: ВМС (1-ва рота/1-10 ек.), Медици (2-ра рота/11-16 ек.).'))