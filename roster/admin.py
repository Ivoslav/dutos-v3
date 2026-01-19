from django.contrib import admin  # <--- ТОВА ЛИПСВАШЕ
from .models import CourseOrRank, Soldier, DutyType

# 1. Настройка за Военнослужещи
@admin.register(Soldier)
class SoldierAdmin(admin.ModelAdmin):
    # Какво се вижда в списъка (колоните)
    list_display = ('faculty_number', 'rank_title', 'last_name', 'first_name', 'company', 'platoon', 'score')
    
    # По какво можеш да търсиш (Търсачката горе)
    search_fields = ('last_name', 'first_name', 'faculty_number', 'rank_title')
    
    # Филтрите отдясно
    list_filter = ('rank_group', 'company', 'platoon', 'is_active')
    
    # Подредба на полетата при редакция (Групиране)
    fieldsets = (
        ('Лични данни', {
            'fields': ('first_name', 'last_name', 'faculty_number', 'birth_date')
        }),
        ('Служебна информация', {
            'fields': ('rank_title', 'rank_group', 'company', 'platoon', 'class_section', 'crew')
        }),
        ('Статус', {
            'fields': ('score', 'is_active')
        }),
    )

# 2. Регистриране на останалите модели (по-просто)
admin.site.register(CourseOrRank)
admin.site.register(DutyType)