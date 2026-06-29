# users/models.py

from django.db import models
from django.core.validators import MinLengthValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings  # ✅ Changed: import from settings
import re


def validate_only_letters(value):
    if not all(char.isalpha() or char.isspace() for char in value):
        raise ValidationError('Name can only contain letters and spaces.')


def validate_indian_mobile(value):
    if not re.match(r'^[6-9]\d{9}$', value):
        raise ValidationError('Enter valid 10-digit mobile number starting with 6-9')


def validate_roll_number(value):
    if not re.match(r'^[A-Za-z0-9\-_]+$', value):
        raise ValidationError('Roll number can only contain letters, numbers, hyphens (-), and underscores (_)')


class Student(models.Model):
    # ✅ Changed: Use settings.AUTH_USER_MODEL instead of direct User import
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='student_profile'
    )
    student_id = models.CharField(max_length=20, unique=True)
    
    full_name = models.CharField(max_length=100, validators=[validate_only_letters, MinLengthValidator(3)])
    class_name = models.CharField(max_length=50)  # ✅ Increased from 20 to 50
    roll_number = models.CharField(max_length=20, validators=[validate_roll_number])  # ✅ Added validator
    
    parent_name = models.CharField(max_length=100, validators=[validate_only_letters], blank=True, null=True)  # ✅ Made optional
    parent_phone = models.CharField(max_length=10, validators=[validate_indian_mobile], blank=True, null=True)  # ✅ Made optional
    
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True, null=True)  # ✅ Made optional
    enrollment_date = models.DateField(auto_now_add=True)
    profile_pic = models.ImageField(upload_to='student_profiles/', null=True, blank=True)
    phone = models.CharField(max_length=10, blank=True, validators=[validate_indian_mobile])  # ✅ Added validator
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"

    class Meta:
        db_table = 'users_student'
        ordering = ['class_name', 'roll_number']  # ✅ Changed ordering


class Teacher(models.Model):
    # ✅ Changed: Use settings.AUTH_USER_MODEL instead of direct User import
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='teacher_profile'
    )
    teacher_id = models.CharField(max_length=20, unique=True)
    
    full_name = models.CharField(max_length=100, validators=[validate_only_letters, MinLengthValidator(3)])
    subject = models.CharField(max_length=100)
    qualification = models.CharField(max_length=200)
    experience_years = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(50)])  # ✅ Added validators
    phone = models.CharField(max_length=10, validators=[validate_indian_mobile])
    joining_date = models.DateField(auto_now_add=True)
    profile_pic = models.ImageField(upload_to='teacher_profiles/', null=True, blank=True)
    bio = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.teacher_id} - {self.full_name} ({self.subject})"

    class Meta:
        db_table = 'users_teacher'
        ordering = ['full_name']  # ✅ Changed ordering