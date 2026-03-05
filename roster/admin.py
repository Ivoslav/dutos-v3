from django.contrib import admin
from .models import AuthorizedDevice, Soldier, DutyType, DutyShift, Leave, ShiftPreference

@admin.register(ShiftPreference)
class ShiftPreferenceAdmin(admin.ModelAdmin):
    list_display = ('soldier', 'date', 'preference', 'created_at')
    list_filter = ('preference', 'date', 'soldier__company')
    search_fields = ('soldier__last_name',)

# 1. Тунинг на Войниците
@admin.register(Soldier)
class SoldierAdmin(admin.ModelAdmin):
    # Какво се вижда в списъка (Колони)
    list_display = ('rank_title', 'last_name', 'faculty_number', 'company', 'platoon', 'position', 'score', 'is_active')    
    # Филтри отдясно (Много полезно!)
    list_filter = ('company', 'platoon', 'rank_group', 'position', 'is_active')
    
    search_fields = ('last_name', 'faculty_number')
    ordering = ('rank_group__priority', 'last_name')
    list_editable = ('score', 'is_active')
    list_per_page = 50
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
admin.site.register(AuthorizedDevice)