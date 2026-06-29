# academic/admin.py

from django.contrib import admin
from .models import Subject, Attendance, Marks, Notification


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_code', 'subject_name', 'teacher', 'created_at')
    list_filter = ('teacher', 'created_at')
    search_fields = ('subject_code', 'subject_name', 'description')
    list_per_page = 25


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    # ✅ Added session in list_display
    list_display = ('student', 'subject', 'date', 'session', 'status', 'marked_by', 'marked_at')
    # ✅ Added session in list_filter
    list_filter = ('status', 'session', 'date', 'subject')
    search_fields = ('student__full_name', 'student__roll_number', 'subject__subject_name', 'remarks')
    list_per_page = 25
    date_hierarchy = 'date'
    
    # ✅ Added fieldsets for better organization
    fieldsets = (
        ('Student & Subject', {
            'fields': ('student', 'subject')
        }),
        ('Attendance Details', {
            'fields': ('date', 'session', 'status', 'remarks')
        }),
        ('Record Information', {
            'fields': ('marked_by', 'marked_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('marked_at',)


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    # ✅ Removed 'exam_date' from list_display (optional, can keep but it's read-only)
    list_display = ('student', 'subject', 'exam_type', 'marks_obtained', 'total_marks', 'percentage')
    # ✅ Removed 'exam_date' from list_filter
    list_filter = ('exam_type', 'subject')
    search_fields = ('student__full_name', 'student__roll_number', 'subject__subject_name')
    list_per_page = 25
    
    def percentage(self, obj):
        return f"{obj.percentage:.1f}%"
    percentage.short_description = 'Percentage'
    percentage.admin_order_field = 'marks_obtained'
    
    fieldsets = (
        ('Student & Subject', {
            'fields': ('student', 'subject')
        }),
        ('Marks Details', {
            # ✅ Removed 'exam_date' from fields (it's auto-generated)
            'fields': ('exam_type', 'marks_obtained', 'total_marks')
        }),
    )
    
    # ✅ Add exam_date as read-only to show but not edit
    readonly_fields = ('exam_date',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'target_role', 'created_by', 'created_at', 'is_read')
    list_filter = ('notification_type', 'target_role', 'is_read', 'created_at')
    search_fields = ('title', 'message')
    list_per_page = 25
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('title', 'message', 'notification_type')
        }),
        ('Target Audience', {
            'fields': ('target_role', 'target_teacher', 'target_student')
        }),
        ('Status', {
            'fields': ('is_read', 'created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)