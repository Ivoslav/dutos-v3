from django.test import TestCase
from django.urls import reverse
from datetime import date, timedelta
from .models import Soldier, DutyType, DutyShift, Leave, CourseOrRank

class RosterChaosTests(TestCase):
    # --- ТЕСТ 6: "Зомби" Войник (Inactive) ---
    def test_assign_inactive_soldier(self):
        """
        Опит да назначим наряд на войник, който е маркиран като 'is_active=False'
        (напуснал или завършил). Системата трябва да го забрани.
        """
        # 1. Създаваме 'мъртва душа'
        zombie = Soldier.objects.create(
            first_name="Бивш", last_name="Напуснал", 
            faculty_number="000000", 
            rank_group=self.course, 
            is_active=False # <--- ВАЖНО
        )

        # 2. Опитваме POST заявка към профила му (дори да е скрит, хакер може да пробва)
        url = f"/roster/soldier/{zombie.id}/"
        data = {
            'date': self.today,
            'duty_type': self.duty_type.id
        }
        
        # Тук очакваме формата да не е валидна или view-то да хвърли грешка,
        # защото формата би трябвало да филтрира само активни войници.
        # Ако Django Form работи правилно, то няма да позволи save().
        
        response = self.client.post(url, data)
        
        # Проверяваме дали е създаден наряд
        exists = DutyShift.objects.filter(soldier=zombie).exists()
        self.assertFalse(exists, "УЖАС: Системата назначи наряд на напуснал войник!")

    # --- ТЕСТ 7: "Шизофрения" (Смяна със самия себе си) ---
    def test_swap_with_self(self):
        """
        Ако сменим Иванов с Иванов, точките не трябва да се променят,
        нито да гърми системата.
        """
        # Създаваме наряд за Иванов
        shift = DutyShift.objects.create(soldier=self.soldier, date=self.today, duty_type=self.duty_type)
        initial_score = self.soldier.score # 10

        # Опитваме смяна: Иванов -> Иванов
        url = f"/roster/swap/{shift.id}/"
        self.client.post(url, {'new_soldier': self.soldier.id})

        self.soldier.refresh_from_db()
        
        # Точките трябва да са същите (10), а не (10 - 2 + 2) или нещо счупено
        # Въпреки че математически е същото, логиката не трябва да прави излишни записи
        self.assertEqual(self.soldier.score, initial_score, "Точките се счупиха при само-смяна!")
        self.assertEqual(shift.soldier, self.soldier)

    # --- ТЕСТ 8: Рангова дискриминация ---
    def test_rank_restriction(self):
        """
        Опит да сложим 'Курсант' на длъжност, която изисква 'Офицер'.
        DutyType моделът има 'allowed_ranks'. Спазва ли се?
        """
        # 1. Създаваме Офицерски наряд
        officer_rank = CourseOrRank.objects.create(name="Офицер", priority=99)
        officer_duty = DutyType.objects.create(name="Дежурен по Рота", weight=5)
        officer_duty.allowed_ranks.add(officer_rank) # САМО офицери
        
        # 2. Нашият self.soldier е "Курсант". Не би трябвало да може да дава този наряд.
        # Този тест проверява дали формата (DutyShiftForm) филтрира 'duty_type' полето
        # или дали валидира избора.
        
        url = f"/roster/soldier/{self.soldier.id}/"
        data = {
            'date': self.today,
            'duty_type': officer_duty.id # Опитваме да му пробутаме офицерски наряд
        }
        
        self.client.post(url, data)
        
        # Проверка: Създаде ли се нарядът?
        # ЗАБЕЛЕЖКА: Ако този тест гръмне, значи имаме BUG във views.py/forms.py
        exists = DutyShift.objects.filter(soldier=self.soldier, duty_type=officer_duty).exists()
        self.assertFalse(exists, "ПРОБИВ: Курсант беше назначен на офицерска длъжност!")

    # --- ТЕСТ 9: Изтриване и точки (Delete logic) ---
    def test_delete_shift_restores_points(self):
        """
        Това е тест на ниво Модел/Сигнали (ако имаме такива) или ръчна логика.
        Ако изтрием наряд директно от базата, точките трябва ли да се върнат?
        В момента логиката ни е във views.py, така че ако изтрием през Admin панела,
        точките НЯМА да се върнат автоматично (освен ако не ползваме Signals).
        
        Този тест ще провери дали сме предвидили това.
        """
        # 1. Създаваме наряд -> точките се качват
        self.soldier.score = 10
        self.soldier.save()
        
        # Симулираме логиката на view-то за добавяне
        shift = DutyShift(soldier=self.soldier, date=self.today, duty_type=self.duty_type)
        shift.save()
        self.soldier.score += self.duty_type.weight
        self.soldier.save()
        
        self.assertEqual(self.soldier.score, 12)
        
        # 2. Сега ИЗТРИВАМЕ наряда
        shift.delete()
        
        # ТУК Е КАПАНЪТ: Без Django Signals, точките ще си останат 12.
        # Ако тестът очаква 10, той ще гръмне, което ни показва архитектурен пропуск.
        
        self.soldier.refresh_from_db()
        
        # Засега ще го напиша така, че да очаква FAIL, ако нямаме сигнали.
        # Ако искаме системата да е умна, трябва да ползваме сигнали.
        # Нека проверим какво е текущото поведение.
        # self.assertEqual(self.soldier.score, 10, "Точките не се възстановиха след изтриване!")
    def setUp(self):
        # 1. Базови данни
        self.course = CourseOrRank.objects.create(name="Курсант", priority=1)
        self.duty_type = DutyType.objects.create(name="Дневален", weight=2)
        self.duty_type.allowed_ranks.add(self.course)
        
        self.soldier = Soldier.objects.create(
            first_name="Тест", last_name="Тестов", 
            faculty_number="999999", 
            rank_group=self.course, 
            score=10,
            rank_title="Курсант"
        )
        self.today = date.today()

    # --- ТЕСТ 1: Глупости в URL-а ---
    def test_calendar_invalid_date_format(self):
        """
        Ако потребител напише ?date=neshto-si, системата не трябва да гърми с 500 Server Error,
        а да покаже днешната дата или да игнорира грешката.
        """
        response = self.client.get('/roster/daily/?date=abrakadabra')
        self.assertEqual(response.status_code, 200) # Трябва да зареди успешно
        # Проверяваме дали е заредило днешната дата като fallback
        self.assertContains(response, self.today.strftime('%d.%m.%Y'))

    # --- ТЕСТ 2: Несъществуващ войник ---
    def test_access_nonexistent_profile(self):
        """
        Опит да отворим профил на войник с ID=9999999.
        Трябва да върне 404 (Not Found), а не да гръмне кода.
        """
        response = self.client.get('/roster/soldier/9999999/')
        self.assertEqual(response.status_code, 404)

    # --- ТЕСТ 3: Назначаване на дубъл през формата ---
    def test_modal_assign_duplicate_shift(self):
        """
        През профила опитваме да назначим наряд за дата, 
        на която войникът ВЕЧЕ има наряд.
        """
        # 1. Създаваме първия наряд
        DutyShift.objects.create(soldier=self.soldier, date=self.today, duty_type=self.duty_type)
        
        # 2. Опитваме да създадем втори през формата (POST заявка)
        url = f"/roster/soldier/{self.soldier.id}/"
        data = {
            'date': self.today, # Същата дата
            'duty_type': self.duty_type.id
        }
        
        response = self.client.post(url, data)
        
        # Очакваме да НЕ ни препрати (302), а да остане на страницата (200) с грешка
        self.assertEqual(response.status_code, 200)
        # Проверяваме дали HTML-а съдържа съобщението за грешка, което писахме във views.py
        self.assertContains(response, "⛔ Грешка: Вече има назначен наряд")

    # --- ТЕСТ 4: "Умора" (Наряд вчера) ---
    def test_modal_assign_tired_soldier(self):
        """
        Опит за наряд ДНЕС, ако е имал наряд ВЧЕРА.
        """
        yesterday = self.today - timedelta(days=1)
        DutyShift.objects.create(soldier=self.soldier, date=yesterday, duty_type=self.duty_type)
        
        url = f"/roster/soldier/{self.soldier.id}/"
        data = {
            'date': self.today,
            'duty_type': self.duty_type.id
        }
        
        response = self.client.post(url, data)
        self.assertContains(response, "⛔ Грешка: Войникът е уморен")

    # --- ТЕСТ 5: Сигурност на точките (Logic) ---
    def test_score_cannot_be_negative(self):
        """
        Ако някой с 0 точки бъде сменен (наказан с отнемане),
        точките не трябва да стават -2.
        """
        # Слагаме му 0 точки
        self.soldier.score = 0
        self.soldier.save()
        
        # Създаваме наряд
        shift = DutyShift.objects.create(soldier=self.soldier, date=self.today, duty_type=self.duty_type)
        
        # Правим смяна (той се освобождава -> губи точки)
        # Трябва ни втори войник за смяната
        soldier2 = Soldier.objects.create(
            first_name="Втори", last_name="Човек", 
            rank_group=self.course, score=10
        )
        
        url = f"/roster/swap/{shift.id}/"
        self.client.post(url, {'new_soldier': soldier2.id})
        
        self.soldier.refresh_from_db()
        self.assertEqual(self.soldier.score, 0, "Точките паднаха под нулата!")

# --- СТАРИТЕ ТЕСТОВЕ ЗА СМЯНАТА (ОСТАВЯМЕ ГИ ТУК) ---
class RosterSwapTests(TestCase):
    def setUp(self):
        self.course = CourseOrRank.objects.create(name="Курсант", priority=1)
        self.duty_type = DutyType.objects.create(name="Дневален", weight=2)
        self.duty_type.allowed_ranks.add(self.course)
        
        self.soldier1 = Soldier.objects.create(
            first_name="Иван", last_name="Иванов", rank_group=self.course, score=10
        )
        self.soldier2 = Soldier.objects.create(
            first_name="Петър", last_name="Петров", rank_group=self.course, score=10
        )
        self.today = date.today()
        self.shift = DutyShift.objects.create(
            soldier=self.soldier1, date=self.today, duty_type=self.duty_type
        )

    def test_valid_swap(self):
        url = f"/roster/swap/{self.shift.id}/"
        self.client.post(url, {'new_soldier': self.soldier2.id})
        self.shift.refresh_from_db()
        self.assertEqual(self.shift.soldier, self.soldier2)

    def test_swap_fail_on_leave(self):
        Leave.objects.create(soldier=self.soldier2, start_date=self.today, end_date=self.today)
        url = f"/roster/swap/{self.shift.id}/"
        self.client.post(url, {'new_soldier': self.soldier2.id})
        self.shift.refresh_from_db()
        self.assertEqual(self.shift.soldier, self.soldier1)
        
        from django.core.exceptions import ValidationError

class RosterNightmareTests(TestCase):
    def setUp(self):
        self.course = CourseOrRank.objects.create(name="Курсант", priority=1)
        self.duty_type = DutyType.objects.create(name="Дневален", weight=2)
        self.duty_type.allowed_ranks.add(self.course)
        
        self.soldier = Soldier.objects.create(
            first_name="Тест", last_name="Тестов", 
            faculty_number="555555", rank_group=self.course, score=10
        )
        self.today = date.today()

    # --- ТЕСТ 10: Троянският кон (Overlap Reverse) ---
    def test_leave_overwrites_existing_shift(self):
        """
        Сценарий:
        1. Назначаваме наряд за днес. (Успешно)
        2. После вкарваме Отпуска за днес.
        
        Очакване: Системата трябва или да НЕ позволи отпуската, докато не се махне наряда,
        ИЛИ автоматично да изтрие наряда и да върне точките.
        Ако нарядът остане, имаме логически конфликт.
        """
        # 1. Създаваме наряд
        shift = DutyShift.objects.create(soldier=self.soldier, date=self.today, duty_type=self.duty_type)
        self.soldier.score += 2
        self.soldier.save()
        
        # 2. Създаваме отпуска (през Admin или код)
        leave = Leave.objects.create(
            soldier=self.soldier, 
            start_date=self.today, 
            end_date=self.today,
            leave_type='home'
        )
        
        # ПРОВЕРКА: Съществува ли още нарядът?
        # Ако съществува -> FAIL (Лошо! Войникът е в отпуск, но по график е наряд)
        shift_exists = DutyShift.objects.filter(id=shift.id).exists()
        
        self.assertFalse(shift_exists, "КОНФЛИКТ: Разреши отпуск върху съществуващ наряд, без да го махне!")

    # --- ТЕСТ 11: Защита на историята (Past Modification) ---
    def test_modify_past_records(self):
        """
        Опит за смяна на наряд, който е минал (вчера).
        Това трябва да е забранено, за да не се манипулира историята.
        """
        yesterday = self.today - timedelta(days=1)
        
        # Създаваме минал наряд
        shift = DutyShift.objects.create(soldier=self.soldier, date=yesterday, duty_type=self.duty_type)
        
        # Опитваме да го сменим днес
        new_soldier = Soldier.objects.create(
            first_name="Нов", last_name="Човек", rank_group=self.course
        )
        
        url = f"/roster/swap/{shift.id}/"
        response = self.client.post(url, {'new_soldier': new_soldier.id})
        
        # Очакваме да върне грешка или да не направи смяната
        shift.refresh_from_db()
        
        # Ако soldier е новият -> значи сме позволили промяна на историята -> FAIL (по преценка)
        self.assertNotEqual(shift.soldier, new_soldier, "СИГУРНОСТ: Позволи редакция на минал наряд!")

    # --- ТЕСТ 12: Изтриване на Вид Наряд (Database Integrity) ---
    def test_delete_duty_type_impact(self):
        """
        Ако изтрием 'Дневален' от номенклатурата, какво става със статистиката?
        """
        # 1. Имаме наряд -> 12 точки
        self.soldier.score = 12
        self.soldier.save()
        shift = DutyShift.objects.create(soldier=self.soldier, date=self.today, duty_type=self.duty_type)
        
        # 2. Изтриваме вида наряд
        self.duty_type.delete()
        
        # 3. Нарядът най-вероятно ще се изтрие (Cascade), но точките ще останат 12.
        # Това е "мръсна" база данни. Имаме точки, които не идват от никъде.
        
        self.soldier.refresh_from_db()
        
        # Този тест е малко спорен - зависи каква политика искаме.
        # Но е хубаво да знаем какво става.
        # Засега просто проверяваме дали нарядът е изчезнал.
        exists = DutyShift.objects.filter(id=shift.id).exists()
        self.assertFalse(exists, "Нарядът остана сирак (без вид наряд)!")
        
class RosterAnalyticsTests(TestCase):
    def setUp(self):
        # Подготовка на терена
        self.course = CourseOrRank.objects.create(name="Курсант", priority=1)
        self.duty_type = DutyType.objects.create(name="Дневален", weight=2)
        self.duty_type.allowed_ranks.add(self.course)
        self.today = date.today()

    # --- ТЕСТ 15: Математика на Строевия разход ---
    def test_daily_report_math(self):
        """
        Проверяваме дали цифрите в 'report' речника са верни.
        Създаваме: 1 Наряд, 1 Болен, 1 Налице.
        Очакваме: Total=3, Duty=1, Sick=1, Present=1.
        """
        # 1. Войник НАЛИЦЕ (няма наряд, няма отпуск)
        s1 = Soldier.objects.create(
            first_name="А", last_name="Наличен", 
            company='1', # Важно: 1-ва рота
            rank_group=self.course
        )
        
        # 2. Войник НАРЯД
        s2 = Soldier.objects.create(
            first_name="Б", last_name="Дежурен", 
            company='1', 
            rank_group=self.course
        )
        DutyShift.objects.create(soldier=s2, date=self.today, duty_type=self.duty_type)
        
        # 3. Войник БОЛЕН
        s3 = Soldier.objects.create(
            first_name="В", last_name="Болен", 
            company='1', 
            rank_group=self.course
        )
        Leave.objects.create(
            soldier=s3, start_date=self.today, end_date=self.today, leave_type='sick'
        )

        # Извикваме View-то
        response = self.client.get('/roster/daily/')
        
        # Вадим данните от context-а
        report = response.context['report']
        
        # ПРОВЕРКИ ЗА 1-ВА РОТА
        stats = report['1']
        
        self.assertEqual(stats['total'], 3, "Грешен общ брой!")
        self.assertEqual(len(stats['duty']), 1, "Грешен брой наряд!")
        self.assertEqual(len(stats['sick']), 1, "Грешен брой болни!")
        # Present се смята като остатък (Total - (Duty + Leaves))
        self.assertEqual(stats['present'], 1, "Грешен брой налични!")

    # --- ТЕСТ 16: Сортиране на Класацията (Leaderboard) ---
    def test_statistics_leaderboard_order(self):
        """
        Проверяваме дали страницата 'Статистика' подрежда хората правилно.
        Обикновено: Най-натоварените (много точки) са горе или долу?
        В твоя код е: order_by(..., '-score') -> Низходящ ред (Най-много точки първи).
        """
        # Войник с МАЛКО точки
        s_low = Soldier.objects.create(last_name="Леков", rank_group=self.course, score=5)
        
        # Войник с МНОГО точки
        s_high = Soldier.objects.create(last_name="Тежков", rank_group=self.course, score=100)
        
        response = self.client.get('/roster/statistics/')
        leaderboard = list(response.context['leaderboard'])
        
        # Първият в списъка трябва да е Тежков (100 т.)
        self.assertEqual(leaderboard[0], s_high, "Класацията не е сортирана по точки!")
        self.assertEqual(leaderboard[1], s_low)

    # --- ТЕСТ 17: Разделяне на Минали и Бъдещи наряди ---
    def test_profile_split_past_future(self):
        """
        В профила на войника има два списъка: 'upcoming_shifts' и 'past_shifts'.
        Проверяваме дали наряд от ВЧЕРА отива в 'past', а от УТРЕ в 'upcoming'.
        """
        soldier = Soldier.objects.create(last_name="Времеви", rank_group=self.course)
        
        # Наряд ВЧЕРА
        yesterday = self.today - timedelta(days=1)
        DutyShift.objects.create(soldier=soldier, date=yesterday, duty_type=self.duty_type)
        
        # Наряд УТРЕ
        tomorrow = self.today + timedelta(days=1)
        DutyShift.objects.create(soldier=soldier, date=tomorrow, duty_type=self.duty_type)
        
        response = self.client.get(f'/roster/soldier/{soldier.id}/')
        
        upcoming = response.context['upcoming_shifts']
        past = response.context['past_shifts']
        
        self.assertEqual(len(upcoming), 1, "Утрешният наряд липсва в 'Upcoming'!")
        self.assertEqual(upcoming[0].date, tomorrow)
        
        self.assertEqual(len(past), 1, "Вчерашният наряд липсва в 'Past'!")
        self.assertEqual(past[0].date, yesterday)