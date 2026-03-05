import random
from django.core.management.base import BaseCommand
from roster.models import Soldier, CourseOrRank, DutyShift

class Command(BaseCommand):
    help = 'Генерира армия с абсолютно точни квоти за длъжностите'

    def handle(self, *args, **kwargs):
        self.stdout.write("🧹 Изтривам старата армия...")
        DutyShift.objects.all().delete()
        Soldier.objects.all().delete()
        
        required_courses = [("1-ви курс", 1), ("2-ри курс", 2), ("3-ти курс", 3), ("4-ти курс", 4), ("5-ти курс", 5)]
        active_courses = {}
        for name, priority in required_courses:
            course_obj, _ = CourseOrRank.objects.get_or_create(name=name, defaults={'priority': priority})
            active_courses[name.split("-")[0]] = course_obj

        first_names = ["Иван", "Петър", "Георги", "Димитър", "Николай", "Тодор", "Александър", "Виктор", "Мартин", "Даниел", "Борис", "Калоян", "Стефан", "Валери", "Христо", "Пламен", "Йордан", "Атанас", "Валентин", "Васил", "Стоян", "Кирил", "Методи", "Андрей", "Антон", "Филип", "Симеон", "Владимир", "Емил", "Богомил"]
        last_names = ["Иванов", "Петров", "Георгиев", "Димитров", "Стоянов", "Андреев", "Михайлов", "Николов", "Василев", "Тодоров", "Маринов", "Христов", "Ангелов", "Илиев", "Йорданов", "Колев", "Петков", "Симеонов", "Златев", "Радев", "Павлов", "Атанасов", "Стефанов", "Попов", "Григоров", "Минев", "Желев", "Вълков", "Добрев", "Ковачев", "Узунов", "Миланов", "Костов", "Игнатов", "Дончев", "Хаджиев", "Владев", "Манолов", "Стайков", "Ганев", "Танев", "Русев", "Димов", "Кръстев", "Цветков", "Янков"]

        # --- ТОЧНИ КВОТИ ---
        # Генерираме точно по 30 човека на курс
        years_to_generate = ['1']*30 + ['2']*30 + ['3']*30 + ['4']*30 + ['5']*30
        random.shuffle(years_to_generate)
        
        # Разпределяме старшите длъжности (за 4-ти и 5-ти курс)
        senior_roles = ['ДК']*1 + ['ЗДК']*4 + ['ОК']*4 + ['ЗОК']*8 + ['ЕК']*16 + ['ЗЕК']*16 + ['КВД']*1 + ['ЗКВ']*1 + ['КВ']*3
        random.shuffle(senior_roles)
        
        # Разпределяме младшите длъжности (за 3-ти курс)
        junior_roles = ['КО']*5
        random.shuffle(junior_roles)
        
        # Подготвяме екипажите, за да има точно по 1 ЕК и ЗЕК за всеки номер (1-10 ВМС, 11-16 Медици)
        nav_crews_ek = list(range(1, 11)); random.shuffle(nav_crews_ek)
        med_crews_ek = list(range(11, 17)); random.shuffle(med_crews_ek)
        nav_crews_zek = list(range(1, 11)); random.shuffle(nav_crews_zek)
        med_crews_zek = list(range(11, 17)); random.shuffle(med_crews_zek)

        self.stdout.write("🌱 Генериране на 150 бойци по новия щат...")
        
        for _ in range(150):
            year = years_to_generate.pop()
            
            # 1. Присвояване на длъжност
            position = "Редови"
            if year in ["4", "5"] and senior_roles:
                position = senior_roles.pop()
            elif year == "3" and junior_roles:
                position = junior_roles.pop()

            # 2. Определяне Медик или ВМС
            is_medic = random.random() < 0.20
            # Ако сме изчерпали екипажите за медици, форсираме ВМС и обратно (само за ЕК и ЗЕК)
            if position == 'ЕК':
                if is_medic and not med_crews_ek: is_medic = False
                if not is_medic and not nav_crews_ek: is_medic = True
            elif position == 'ЗЕК':
                if is_medic and not med_crews_zek: is_medic = False
                if not is_medic and not nav_crews_zek: is_medic = True

            if is_medic:
                base_spec = '106'; company = '2'; possible_platoons = ['3', '4']
            else:
                base_spec = random.choice(['101', '102', '103', '110', '181']); company = '1'; possible_platoons = ['1', '2']

            # 3. Звания
            if position == 'КВ': rank = "Оф. кандидат"
            elif year == "5": rank = "Мичман"
            elif year == "4": rank = "Гл. старшина"
            elif year == "3": rank = "Ст. I ст."
            elif year == "2": rank = "Ст. II ст."
            else: rank = "Курсант"

            platoon = random.choice(possible_platoons)
            crew_name = ""
            fac_prefix = "109" if year == "3" and not is_medic and random.random() < 0.15 else base_spec
            if year == "1": fac_prefix = base_spec + "4"
            fac_suffix = f"2{6-int(year)}1"

            # 4. СПЕЦИФИЧНИ ПРАВИЛА ЗА ДЛЪЖНОСТИТЕ
            if position in ['КО', 'ЗКВ', 'КВД']:
                company = 'Млади'
                platoon = 'Млади'
                crew_name = "" # Без екипаж
            elif year == "1":
                company = 'Млади'
                platoon = 'Млади'
                crew_name = "" # Първокурсниците са без екипаж
            elif position in ['ДК', 'ЗДК', 'ОК', 'ЗОК', 'КВ']:
                crew_name = "" # Щабът няма конкретен екипаж
            elif position == 'ЕК':
                c_num = med_crews_ek.pop() if is_medic else nav_crews_ek.pop()
                crew_name = f"Екипаж {c_num}"
            elif position == 'ЗЕК':
                c_num = med_crews_zek.pop() if is_medic else nav_crews_zek.pop()
                crew_name = f"Екипаж {c_num}"
            else:
                # Редови от 2 до 5 курс
                c_num = random.randint(11, 16) if is_medic else random.randint(1, 10)
                crew_name = f"Екипаж {c_num}"

            # 5. Генериране на уникален Фак. Номер
            while True:
                student_num = f"{random.randint(1, 99):02d}"
                full_fac_number = f"{fac_prefix}-{fac_suffix}{student_num}"
                if not Soldier.objects.filter(faculty_number=full_fac_number).exists():
                    break

            phone_num = f"08{random.choice(['7', '8', '9'])}{random.randint(1000000, 9999999)}"

            Soldier.objects.create(
                first_name=random.choice(first_names), last_name=random.choice(last_names),
                faculty_number=full_fac_number, rank_title=rank, rank_group=active_courses[year],
                company=company, platoon=platoon, position=position, crew=crew_name, phone=phone_num,
                score=random.randint(0, 5)
            )

        self.stdout.write(self.style.SUCCESS(f'✅ Армията е обновена с АБСОЛЮТНО ТОЧНИ квоти!'))
        
        
        
        # --- НОВО: ГЕНЕРИРАНЕ НА ПОТРЕБИТЕЛСКИ АКАУНТИ ---
        from django.contrib.auth.models import User
        self.stdout.write("🔑 Генериране на потребителски акаунти за влизане в системата...")
        
        # Изтриваме старите обикновени потребители (без админите)
        User.objects.filter(is_superuser=False).delete()
        
        for s in Soldier.objects.all():
            # Потребителско име = Фак. номер, Парола = 123
            user = User.objects.create_user(username=s.faculty_number, password='123')
            user.first_name = s.first_name
            user.last_name = s.last_name
            user.save()
            
            # Връзваме войника към този акаунт
            s.user = user
            s.save()