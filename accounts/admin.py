# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'status', 'phone', 'created_at')
    list_filter = ('role', 'status', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    list_per_page = 25
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'status', 'phone', 'profile_pic', 'rejection_reason', 'approved_by', 'approved_at')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


admin.site.register(User, CustomUserAdmin)