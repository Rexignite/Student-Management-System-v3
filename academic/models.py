# academic/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings  # ✅ Added this import
from datetime import date
import re


def validate_subject_code(value):
    if not re.match(r'^[A-Za-z]{2,4}\d{3}$', value):
        raise ValidationError('Subject code must be like: MATH101, CS201')


class Subject(models.Model):
    subject_code = models.CharField(max_length=20, unique=True, validators=[validate_subject_code])
    subject_name = models.CharField(max_length=100)
    # ✅ Changed: Use string reference instead of direct import
    teacher = models.ForeignKey('users.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='subjects')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name}"

    class Meta:
        db_table = 'academic_subject'
        ordering = ['subject_code']


class Attendance(models.Model):
    SESSION_CHOICES = (
        ('AM', 'Morning Session (9:00 AM - 12:00 PM)'),
        ('PM', 'Afternoon Session (1:00 PM - 4:00 PM)'),
    )
    
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('leave', 'Leave'),
    )
    
    # ✅ Changed: Use string references
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='attendances')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=date.today)
    session = models.CharField(max_length=2, choices=SESSION_CHOICES, default='AM')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    remarks = models.CharField(max_length=200, blank=True)
    # ✅ Changed: Use string reference
    marked_by = models.ForeignKey('users.Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='marked_attendances')
    marked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.subject_name} - {self.date} ({self.get_session_display()}) - {self.get_status_display()}"

    def get_status_badge(self):
        badges = {
            'present': 'success',
            'absent': 'danger',
            'late': 'warning',
            'leave': 'info',
        }
        return badges.get(self.status, 'secondary')
    
    def get_status_short(self):
        codes = {
            'present': 'P',
            'absent': 'A',
            'late': 'L',
            'leave': 'LV',
        }
        return codes.get(self.status, '-')

    class Meta:
        db_table = 'academic_attendance'
        unique_together = ['student', 'subject', 'date', 'session']
        ordering = ['-date', '-session']


class Marks(models.Model):
    EXAM_TYPES = (
        ('mid_term', 'Mid Term Exam'),
        ('final_term', 'Final Term Exam'),
        ('assignment', 'Assignment'),
        ('quiz', 'Quiz'),
        ('practical', 'Practical'),
        ('class_test', 'Class Test'),
    )
    
    # ✅ Changed: Use string reference
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='marks')
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    marks_obtained = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    total_marks = models.FloatField(default=100, validators=[MinValueValidator(0)])
    exam_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def percentage(self):
        return (self.marks_obtained / self.total_marks * 100) if self.total_marks > 0 else 0
    
    @property
    def grade(self):
        percentage = self.percentage
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C'
        elif percentage >= 40:
            return 'D'
        else:
            return 'F'
    
    @property
    def grade_points(self):
        percentage = self.percentage
        if percentage >= 90:
            return 10
        elif percentage >= 80:
            return 9
        elif percentage >= 70:
            return 8
        elif percentage >= 60:
            return 7
        elif percentage >= 50:
            return 6
        elif percentage >= 40:
            return 5
        else:
            return 0

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.subject_name} - {self.get_exam_type_display()}: {self.marks_obtained}/{self.total_marks}"

    class Meta:
        db_table = 'academic_marks'
        unique_together = ['student', 'subject', 'exam_type']
        ordering = ['subject__subject_name', '-created_at']


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('marks', 'Marks Updated'),
        ('attendance', 'Attendance Alert'),
        ('notice', 'General Notice'),
        ('fee', 'Fee Reminder'),
        ('exam', 'Exam Schedule'),
        ('event', 'Event'),
    )
    
    TARGET_ROLES = (
        ('all', 'All Users'),
        ('director', 'Director Only'),
        ('teacher', 'Teachers Only'),
        ('student', 'Students Only'),
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='notice')
    target_role = models.CharField(max_length=20, choices=TARGET_ROLES, default='all')
    # ✅ Changed: Use string references
    target_student = models.ForeignKey('users.Student', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    target_teacher = models.ForeignKey('users.Teacher', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    # ✅ Changed: Use settings.AUTH_USER_MODEL
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def mark_as_read(self):
        self.is_read = True
        self.save()

    class Meta:
        db_table = 'academic_notification'
        ordering = ['-created_at']