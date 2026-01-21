from django.contrib import admin
from django.db.models import Q
from django.utils.html import format_html
from .models import Soldier, DutyType, DutyShift, Leave

# === 1. СПЕЦИАЛЕН ФИЛТЪР ЗА РОТИТЕ ===
class SoldierTypeFilter(admin.SimpleListFilter):
    title = 'Разпределение' # Заглавието на филтъра
    parameter_name = 'soldier_type'

    def lookups(self, request, model_admin):
        # Какви опции да се показват в менюто
        return (
            ('young', '👶 Млади (1-ви курс)'),
            ('c1_old', '🟦 1-ва Рота (Стари)'),
            ('c2_old', '🟥 2-ра Рота (Стари)'),
            ('hq', '🏢 Щаб / Други'),
        )

    def queryset(self, request, queryset):
        # Логиката: Какво да показва при всеки избор
        
        # Ако избереш "Млади" -> търси взвод "Млади"
        if self.value() == 'young':
            return queryset.filter(platoon='Млади')
        
        # Ако избереш "1-ва Рота (Стари)" -> 1-ва рота, НО ИЗКЛЮЧИ младите
        if self.value() == 'c1_old':
            return queryset.filter(company='1').exclude(platoon='Млади')
            
        # Ако избереш "2-ра Рота (Стари)" -> 2-ра рота, НО ИЗКЛЮЧИ младите
        if self.value() == 'c2_old':
            return queryset.filter(company='2').exclude(platoon='Млади')

        if self.value() == 'hq':
            return queryset.exclude(company__in=['1', '2']).exclude(platoon='Млади')

# === 2. ВОЙНИЦИ ===
@admin.register(Soldier)
class SoldierAdmin(admin.ModelAdmin):
    list_display = ('rank_title', 'last_name', 'get_platoon_display', 'score', 'is_active')
    
    # ТУК ВКЛЮЧВАМЕ НОВИЯ ФИЛТЪР ВМЕСТО ОБИКНОВЕНИЯ 'company'
    list_filter = (SoldierTypeFilter, 'rank_group', 'is_active')
    
    search_fields = ('last_name', 'faculty_number')
    ordering = ('rank_group__priority', 'last_name')
    list_editable = ('score', 'is_active')
    list_per_page = 50
    actions = ['reset_points']

    # Красиво показване на взвода
    def get_platoon_display(self, obj):
        if obj.platoon == 'Млади':
            return '👶 Млади'
        return f"{obj.company}-ва Рота / {obj.platoon} взвод"
    get_platoon_display.short_description = 'Подразделение'

    @admin.action(description='🔄 Нулирай точките на избраните')
    def reset_points(self, request, queryset):
        rows_updated = queryset.update(score=0)
        self.message_user(request, f"Успешно нулирани точките на {rows_updated} души.")

# === 3. НАРЯДИ ===
@admin.register(DutyShift)
class DutyShiftAdmin(admin.ModelAdmin):
    list_display = ('date', 'duty_name_colored', 'soldier_info')
    list_filter = ('date', 'duty_type')
    date_hierarchy = 'date'

    def duty_name_colored(self, obj):
        return obj.duty_type.name
    duty_name_colored.short_description = 'Наряд'

    def soldier_info(self, obj):
        return f"{obj.soldier.rank_title} {obj.soldier.last_name}"
    soldier_info.short_description = 'Военнослужещ'

# === 4. ОТПУСКИ ===
@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('soldier_link', 'colored_type', 'start_date', 'end_date', 'days_count', 'status_bar')
    list_filter = ('leave_type', 'start_date')
    search_fields = ('soldier__last_name', 'soldier__faculty_number')
    list_per_page = 20

    # 1. Цветен етикет за вида отпуск
    def colored_type(self, obj):
        colors = {
            'sick': ('red', 'Болничен'),
            'home': ('orange', 'Домашен'),
            'mission': ('blue', 'Командировка'),
            'arrest': ('black', 'Арест'),
            'other': ('gray', 'Друго'),
        }
        color, label = colors.get(obj.leave_type, ('gray', obj.leave_type))
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 10px; font-weight: bold;">{}</span>',
            color, label
        )
    colored_type.short_description = 'Вид'

    # 2. Линк към войника (вместо просто име)
    def soldier_link(self, obj):
        return obj.soldier
    soldier_link.short_description = 'Военнослужещ'
    soldier_link.admin_order_field = 'soldier__last_name'

    # 3. Визуална лента за продължителността
    def status_bar(self, obj):
        delta = (obj.end_date - obj.start_date).days
        # Макс черта = 30 дни
        width = min(delta * 3, 100) 
        color = 'red' if obj.leave_type == 'sick' else 'green'
        
        return format_html(
            '<div style="width: 100px; background-color: #ddd; height: 5px; border-radius: 2px;">'
            '<div style="width: {}px; background-color: {}; height: 100%;"></div>'
            '</div>',
            width, color
        )
    status_bar.short_description = 'Дължина'

    def days_count(self, obj):
        delta = obj.end_date - obj.start_date
        return f"{delta.days} дни"
    days_count.short_description = 'Дни'