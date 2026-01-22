from django.contrib import admin
from .models import Soldier, DutyType, DutyShift, Leave

# 1. Тунинг на Войниците
@admin.register(Soldier)
class SoldierAdmin(admin.ModelAdmin):
    # Какво се вижда в списъка (Колони)
    list_display = ('rank_title', 'last_name', 'faculty_number', 'company', 'platoon', 'score', 'is_active')
    
    # Филтри отдясно (Много полезно!)
    list_filter = ('company', 'platoon', 'rank_group', 'is_active')
    
    # Търсачка (Търси по име и факултетен номер)
    search_fields = ('last_name', 'faculty_number')
    
    # Подреждане по подразбиране
    ordering = ('rank_group__priority', 'last_name')
    
    # Възможност да редактираш точките директно от списъка (без да отваряш профила)
    list_editable = ('score', 'is_active')
    
    # Колко реда да показва на страница
    list_per_page = 50

    # Екстра: Масово действие "Нулирай точките" (за начало на месец/година)
    actions = ['reset_points']

    @admin.action(description='🔄 Нулирай точките на избраните')
    def reset_points(self, request, queryset):
        rows_updated = queryset.update(score=0)
        self.message_user(request, f"Успешно нулирани точките на {rows_updated} души.")


# 2. Тунинг на Нарядите
@admin.register(DutyShift)
class DutyShiftAdmin(admin.ModelAdmin):
    list_display = ('date', 'duty_name_colored', 'soldier_info')
    list_filter = ('date', 'duty_type')
    date_hierarchy = 'date' # Добавя навигация по дати най-горе

    # Показваме името на наряда
    def duty_name_colored(self, obj):
        return obj.duty_type.name
    duty_name_colored.short_description = 'Наряд'

    # Показваме кой го дава
    def soldier_info(self, obj):
        return f"{obj.soldier.rank_title} {obj.soldier.last_name}"
    soldier_info.short_description = 'Военнослужещ'


# 3. Тунинг на Отпуските/Болничните
@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('soldier', 'leave_type', 'start_date', 'end_date', 'days_count')
    list_filter = ('leave_type', 'start_date')
    search_fields = ('soldier__last_name',)
    
    def days_count(self, obj):
        delta = obj.end_date - obj.start_date
        return f"{delta.days} дни"
    days_count.short_description = 'Продължителност'


# 4. Другите модели
admin.site.register(DutyType)