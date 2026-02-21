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

        # --- РАЗШИРЕН СПИСЪК С ИМЕНА ---
        first_names = [
            "Иван", "Петър", "Георги", "Димитър", "Николай", "Тодор", "Александър", "Виктор", 
            "Мартин", "Даниел", "Борис", "Калоян", "Стефан", "Валери", "Христо", "Красимир",
            "Пламен", "Йордан", "Атанас", "Валентин", "Васил", "Стоян", "Борислав", "Кирил",
            "Методи", "Андрей", "Антон", "Филип", "Симеон", "Владимир", "Емил", "Богомил"
        ]
        
        last_names = [
            "Иванов", "Петров", "Георгиев", "Димитров", "Стоянов", "Андреев", "Михайлов", 
            "Николов", "Василев", "Тодоров", "Маринов", "Христов", "Ангелов", "Илиев", 
            "Йорданов", "Колев", "Петков", "Симеонов", "Златев", "Радев", "Павлов", 
            "Атанасов", "Стефанов", "Попов", "Григоров", "Минев", "Желев", "Вълков",
            "Караиванов", "Добрев", "Ковачев", "Узунов", "Миланов", "Костов", "Игнатов",
            "Богомилов", "Дончев", "Хаджиев", "Владев", "Манолов", "Стайков", "Ганев",
            "Танев", "Русев", "Ненов", "Димов", "Кръстев", "Захариев", "Цветков", "Янков"
        ]
        
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
            rank = ""; platoon = ""; fac_prefix = ""; fac_suffix = ""; position = "Редови"

            if year == "1": 
                company = "Млади"
                platoon = "Млади" 
                rank = "Курсант"
                fac_prefix = base_spec + "4"
                fac_suffix = "251"
                
            elif year == "2": 
                rank = "Ст. II ст."; platoon = random.choice(possible_platoons); fac_prefix = base_spec; fac_suffix = "241"
                if random.random() < 0.10: position = "ЗЕК" # 10% шанс да е Зам. екипажен

            elif year == "3": 
                rank = "Ст. I ст."; platoon = random.choice(possible_platoons); fac_suffix = "231"; 
                fac_prefix = "109" if not is_medic and random.random() < 0.15 else base_spec
                
                # КО-та са от 3-ти курс
                rnd = random.random()
                if rnd < 0.15: position = "КО"
                elif rnd < 0.20: position = "ЗОК"

            elif year == "4": 
                rank = "Гл. старшина"; platoon = random.choice(possible_platoons); fac_suffix = "221"; fac_prefix = base_spec
                
                # ЗКВ и КВД са от 4-ти курс
                rnd = random.random()
                if rnd < 0.10: position = "ЗКВ"
                elif rnd < 0.20: position = "КВД"
                elif rnd < 0.25: position = "ОК"

            elif year == "5": 
                platoon = random.choice(possible_platoons); fac_suffix = "211"; fac_prefix = base_spec
                
                # Тук слагаме Офицерските кандидати (КВ) и старшите командири
                rnd = random.random()
                if rnd < 0.10:
                    rank = "Оф. кандидат"
                    position = "КВ"
                else:
                    rank = "Мичман"
                    if rnd < 0.20: position = "КВД"
                    elif rnd < 0.30: position = "ЕК"
                    elif rnd < 0.35: position = "ДК"

            student_num = f"{random.randint(1, 35):02d}"
            full_fac_number = f"{fac_prefix}-{fac_suffix}{student_num}"

            if Soldier.objects.filter(faculty_number=full_fac_number).exists():
                continue

            has_crew = True if year != "1" else (random.random() > 0.5)
            crew_name = f"Екипаж {crew_num}" if has_crew else ""

            # Създаване на телефон (произволен)
            phone_num = f"08{random.choice(['7', '8', '9'])}{random.randint(1000000, 9999999)}"

            Soldier.objects.create(
                first_name=random.choice(first_names),
                last_name=random.choice(last_names),
                faculty_number=full_fac_number,
                rank_title=rank,
                rank_group=course_obj,
                company=company,
                platoon=platoon,
                position=position,
                crew=crew_name,
                phone=phone_num,
                score=random.randint(0, 5)
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Готово! Армията е обновена с по-разнообразни имена.'))