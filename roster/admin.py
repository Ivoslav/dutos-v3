from django.contrib import admin
from .models import CourseOrRank, DutyShift, Soldier, DutyType, DutyShift, Leave

@admin.register(Soldier)
class SoldierAdmin(admin.ModelAdmin):
    list_display = ('faculty_number', 'rank_title', 'last_name', 'first_name', 'company', 'platoon', 'score')
    
    search_fields = ('last_name', 'first_name', 'faculty_number', 'rank_title')
    
    list_filter = ('rank_group', 'company', 'platoon', 'is_active')
    
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

admin.site.register(CourseOrRank)
admin.site.register(DutyType)

@admin.register(DutyShift)
class DutyShiftAdmin(admin.ModelAdmin):
    list_display = ('date', 'duty_type', 'soldier')
    list_filter = ('date', 'duty_type')
    date_hierarchy = 'date'

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('soldier', 'leave_type', 'start_date', 'end_date', 'duration')
    list_filter = ('leave_type', 'start_date')
    search_fields = ('soldier__last_name', 'soldier__faculty_number')
    
    def duration(self, obj):
        delta = obj.end_date - obj.start_date
        return f"{delta.days + 1} дни"
    duration.short_description = "Продължителност"