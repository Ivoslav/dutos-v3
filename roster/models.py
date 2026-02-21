from django.db import models

# Звания (спрямо твоята йерархия)
RANK_CHOICES = [
    ('Курсант', 'Курсант (1-ви курс)'),
    ('Ст. II ст.', 'Старшина II степен'),
    ('Ст. I ст.', 'Старшина I степен'),
    ('Гл. старшина', 'Главен старшина'),
    ('Мичман', 'Мичман'),
    ('Оф. кандидат', 'Офицерски кандидат'),
    ('Лейтенант', 'Лейтенант'),
    ('Капитан', 'Капитан'),
    ('Майор', 'Майор'),
    ('Граждански', 'Гражданско лице'),
]

# Взводове/Отряди
PLATOON_CHOICES = [
    ('1', '1-ви взвод'),
    ('2', '2-ри взвод'),
    ('3', '3-ти взвод'),
    ('4', '4-ти взвод'),
    ('Млади', 'Взвод млади курсанти'),
]

# Роти
COMPANY_CHOICES = [
    ('1', '1-ва Рота'),
    ('2', '2-ра Рота'),
    ('Млади', 'Млади курсанти'),
    ('Щаб', 'Щаб'),
]

POSITION_CHOICES = [
    # --- БАЗОВ СЪСТАВ ---
    ('Редови', 'Редови състав'),

    # --- 1-ВИ КУРС (Взводна организация) ---
    ('КО', 'Командир на отделение'),
    ('ЗКВ', 'Заместник командир на взвод'),
    ('КВД', 'Командир на взвод дубльор'),

    # --- 2-5 КУРС (Корабна/Екипажна организация) ---
    ('ЕК', 'Екипажен командир'),
    ('ЗЕК', 'Зам. екипажен командир'),
    ('ОК', 'Отряден командир'),
    ('ЗОК', 'Зам. отряден командир'),
    ('ДК', 'Дивизионен командир'),
    ('ЗДК', 'Зам. дивизионен командир'),

    # --- ОФИЦЕРИ / ПОСТОЯНЕН СЪСТАВ ---
    ('КВ', 'Командир на взвод (Офицер)'),
    ('КР', 'Командир на рота (Офицер)'),
    ('КомБат', 'Командир на батальон (Офицер)'),
]


class CourseOrRank(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Име на група/Курс")
    priority = models.IntegerField(default=0, verbose_name="Приоритет")

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Курс/Група"
        verbose_name_plural = "Курсове и Групи"

class Soldier(models.Model):
    first_name = models.CharField(max_length=50, verbose_name="Име")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    faculty_number = models.CharField(max_length=20, unique=True, verbose_name="Фак. номер", null=True, blank=True, help_text="Пример: 111-24112")
    birth_date = models.DateField(verbose_name="Дата на раждане (ДД.ММ.ГГГГ)", null=True, blank=True)
    
    rank_title = models.CharField(max_length=50, choices=RANK_CHOICES, default='Курсант', verbose_name="Звание")
    position = models.CharField(max_length=15, choices=POSITION_CHOICES, default='Редови', verbose_name="Длъжност")
    rank_group = models.ForeignKey(CourseOrRank, on_delete=models.CASCADE, verbose_name="Курс (Басейн за наряди)")
    
    company = models.CharField(max_length=10, choices=COMPANY_CHOICES, default='1', verbose_name="Рота")
    platoon = models.CharField(max_length=20, choices=PLATOON_CHOICES, default='1', verbose_name="Взвод/Отряд")
    
    class_section = models.CharField(max_length=20, verbose_name="Класно отделение", blank=True, help_text="Попълва се автоматично от Фак. номер")
    crew = models.CharField(max_length=50, verbose_name="Екипаж", blank=True)
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон", help_text="За оповестяване")

    score = models.IntegerField(default=0, verbose_name="Натрупани точки")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    def save(self, *args, **kwargs):
        if self.faculty_number and len(self.faculty_number) > 2:
            self.class_section = self.faculty_number[:-2]
                        
        super(Soldier, self).save(*args, **kwargs)

# В класа Soldier:
    @property
    def smart_name(self):
        clashes = Soldier.objects.filter(last_name=self.last_name, is_active=True).exclude(pk=self.pk)
        if not clashes.exists():
            return self.last_name

        my_first = self.first_name
        for i in range(1, len(my_first) + 1):
            prefix = my_first[:i]
            is_unique = True
            for other in clashes:
                if other.first_name.startswith(prefix):
                    is_unique = False
                    break
            if is_unique:
                return f"{self.last_name} {prefix}."
        return f"{self.last_name} {self.first_name}"

    def __str__(self):
        # Промени този ред да ползва smart_name
        return f"{self.rank_title} {self.smart_name} ({self.faculty_number})"

# Най-долу във файла, замени Announcement с това:
class Announcement(models.Model):
    TARGET_CHOICES = [
        ('all', '📢 ВСИЧКИ'),
        ('1', '⚓ 1-ва Рота'),
        ('2', '⚕️ 2-ра Рота'),
        ('young', '👶 Млади Курсанти'),
        ('staff', '⭐ Щаб / Офицери'),
    ]

    title = models.CharField(max_length=100, verbose_name="Заглавие")
    message = models.TextField(verbose_name="Съобщение")
    # ТОВА ПОЛЕ Е ВИНОВНИКА ЗА ГРЕШКАТА - ТРЯБВА ДА ГО ИМА:
    target = models.CharField(max_length=10, choices=TARGET_CHOICES, default='all', verbose_name="Получател")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    def __str__(self):
        return f"[{self.get_target_display()}] {self.title}"
    
    class Meta:
        verbose_name = "Извънредно съобщение"
        verbose_name_plural = "Извънредни съобщения"

class DutyType(models.Model):
    name = models.CharField(max_length=100)
    allowed_ranks = models.ManyToManyField(CourseOrRank)
    people_required = models.IntegerField(default=1)
    weight = models.IntegerField(default=1)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Вид Наряд"
        verbose_name_plural = "Видове Наряди"

class DutyShift(models.Model):
    STATUS_CHOICES = [
        ('admin_draft', '🔒 Скрита чернова'),
        ('public_draft', '👀 Проекто-наряд'),
        ('official', '✅ Утвърден'),
    ]

    date = models.DateField(verbose_name="Дата на наряда")
    duty_type = models.ForeignKey(DutyType, on_delete=models.CASCADE, verbose_name="Вид наряд")
    soldier = models.ForeignKey(Soldier, on_delete=models.CASCADE, verbose_name="Назначен")
    
    # --- НОВОТО ПОЛЕ С 3-ТЕ ФАЗИ ---
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='admin_draft', verbose_name="Статус")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Създаден на")

    def __str__(self):
        return f"[{self.get_status_display()}] {self.date} - {self.duty_type.name}: {self.soldier.last_name}"

    class Meta:
        verbose_name = "Назначен наряд"
        verbose_name_plural = "График на нарядите"
        unique_together = ('date', 'soldier')


class Leave(models.Model):
    TYPE_CHOICES = [
        ('home', 'Домашен отпуск'),
        ('sick', 'Болничен / Лазарет'),
        ('mission', 'Командировка'),
        ('arrest', 'Арест'),
        ('other', 'Друго'),
    ]

    soldier = models.ForeignKey(Soldier, on_delete=models.CASCADE, verbose_name="Военнослужещ")
    start_date = models.DateField(verbose_name="Начална дата")
    end_date = models.DateField(verbose_name="Крайна дата")
    leave_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='home', verbose_name="Вид")
    reason = models.CharField(max_length=100, blank=True, verbose_name="Причина (опционално)")

    def save(self, *args, **kwargs):
        # 1. Преди да запишем отпуската, търсим конфликти в графика
        # Трябва да направим import-а тук вътре, за да избегнем Circular Import грешка,
        # ако DutyShift е дефиниран след Leave (макар че при теб е преди, застраховаме се).
        from .models import DutyShift 

        # Намираме всички наряди, които попадат в периода на отпуската
        conflicting_shifts = DutyShift.objects.filter(
            soldier=self.soldier,
            date__gte=self.start_date,
            date__lte=self.end_date
        )

        # 2. За всеки намерен конфликтен наряд:
        for shift in conflicting_shifts:
            # Връщаме точките на войника (тъй като нарядът пада)
            soldier = shift.soldier
            soldier.score -= shift.duty_type.weight
            if soldier.score < 0: soldier.score = 0
            soldier.save()
            
            # Изтриваме наряда
            shift.delete()

        # 3. Чак тогава записваме самата отпуска
        super(Leave, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.soldier.last_name} ({self.get_leave_type_display()})"
    
class Announcement(models.Model):
    TARGET_CHOICES = [
        ('all', '📢 ВСИЧКИ'),
        ('1', '⚓ 1-ва Рота'),
        ('2', '⚕️ 2-ра Рота'),
        ('young', '👶 Млади Курсанти'),
        ('staff', '⭐ Щаб / Офицери'),
    ]

    title = models.CharField(max_length=100, verbose_name="Заглавие")
    message = models.TextField(verbose_name="Съобщение")
    target = models.CharField(max_length=10, choices=TARGET_CHOICES, default='all', verbose_name="Получател")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Активно")

    def __str__(self):
        return f"[{self.get_target_display()}] {self.title}"

    class Meta:
        verbose_name = "Извънредно съобщение"
        verbose_name_plural = "Извънредни съобщения"
        
class ShiftPreference(models.Model):
    PREF_CHOICES = [
        ('want', '🟩 Желая наряд (Доброволец)'),
        ('cannot', '🟥 Не мога (Блокиран ден)'),
    ]

    soldier = models.ForeignKey(Soldier, on_delete=models.CASCADE, verbose_name="Военнослужещ")
    date = models.DateField(verbose_name="Дата")
    preference = models.CharField(max_length=10, choices=PREF_CHOICES, verbose_name="Тип желание")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.soldier.last_name} - {self.date} ({self.get_preference_display()})"

    class Meta:
        verbose_name = "Желание за наряд"
        verbose_name_plural = "Желания за наряди"
        # Един човек не може да има две различни желания за един и същи ден
        unique_together = ('soldier', 'date')