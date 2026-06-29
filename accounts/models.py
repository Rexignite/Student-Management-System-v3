# accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

def validate_indian_mobile(value):
    import re
    if value:
        if not re.match(r'^[6-9]\d{9}$', value):
            raise ValidationError('Enter a valid 10-digit Indian mobile number starting with 6,7,8,9')

class User(AbstractUser):
    ROLE_CHOICES = (
        ('director', 'Director'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    
    phone_regex = RegexValidator(regex=r'^[6-9]\d{9}$', message="Enter a valid 10-digit Indian mobile number")
    phone = models.CharField(validators=[phone_regex], max_length=10, blank=True)
    
    profile_pic = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_users'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # ==================== OTP FIELDS FOR PASSWORD RESET ====================
    reset_otp = models.CharField(max_length=6, blank=True, null=True)
    reset_otp_created_at = models.DateTimeField(blank=True, null=True)
    reset_otp_verified = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} - {self.role} - {self.get_status_display()}"

    class Meta:
        db_table = 'accounts_user'
        ordering = ['-created_at']