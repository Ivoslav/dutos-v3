from django.db import models

# --- СПИСЪЦИ ЗА ИЗБОР (DROPDOWNS) ---

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
    ('Щаб', 'Щаб'),
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
    # ЛИЧНИ ДАННИ
    first_name = models.CharField(max_length=50, verbose_name="Име")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    # Добавихме help_text, за да знаеш формата
    faculty_number = models.CharField(max_length=20, unique=True, verbose_name="Фак. номер", null=True, blank=True, help_text="Пример: 111-24112")
    birth_date = models.DateField(verbose_name="Дата на раждане (ДД.ММ.ГГГГ)", null=True, blank=True)
    
    # СЛУЖЕБНИ ДАННИ (Вече са с Dropdown)
    rank_title = models.CharField(max_length=50, choices=RANK_CHOICES, default='Курсант', verbose_name="Звание")
    rank_group = models.ForeignKey(CourseOrRank, on_delete=models.CASCADE, verbose_name="Курс (Басейн за наряди)")
    
    # ОРГАНИЗАЦИЯ
    company = models.CharField(max_length=10, choices=COMPANY_CHOICES, default='1', verbose_name="Рота")
    platoon = models.CharField(max_length=20, choices=PLATOON_CHOICES, default='1', verbose_name="Взвод/Отряд")
    
    # Това ще се попълва автоматично!
    class_section = models.CharField(max_length=20, verbose_name="Класно отделение", blank=True, help_text="Попълва се автоматично от Фак. номер")
    crew = models.CharField(max_length=50, verbose_name="Екипаж", blank=True)

    # СИСТЕМНИ
    score = models.IntegerField(default=0, verbose_name="Натрупани точки")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    # --- ТУК Е МАГИЯТА ЗА ФАКУЛТЕТНИЯ НОМЕР ---
    def save(self, *args, **kwargs):
        # Ако има въведен факултетен номер (напр. 111-24112)
        if self.faculty_number and len(self.faculty_number) > 2:
            # Взимаме всичко без последните 2 цифри
            # Логика: sliced string [:-2]
            self.class_section = self.faculty_number[:-2]
            
            # Ако има тирета или точки в края, може да искаш да ги махнеш, 
            # но за сега го оставяме както го искаш (всичко преди последните 2).
            
        super(Soldier, self).save(*args, **kwargs)

    def __str__(self):
        # Връща: "Курсант Иванов (111-24055)"
        return f"{self.rank_title} {self.last_name} ({self.faculty_number})"

    class Meta:
        verbose_name = "Военнослужещ"
        verbose_name_plural = "Военнослужещи"

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
    date = models.DateField(verbose_name="Дата на наряда")
    duty_type = models.ForeignKey(DutyType, on_delete=models.CASCADE, verbose_name="Вид наряд")
    soldier = models.ForeignKey(Soldier, on_delete=models.CASCADE, verbose_name="Назначен")
    
    # Допълнително инфо (ако се наложи смяна)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Създаден на")

    def __str__(self):
        # Тук ползваме self.soldier.last_name, защото името е вътре във войника!
        return f"{self.date} - {self.duty_type}: {self.soldier}"

    class Meta:
        verbose_name = "Назначен наряд"
        verbose_name_plural = "График на нарядите"
        # Уникалност: Един войник не може да има 2 наряда в един ден!
        unique_together = ('date', 'soldier')