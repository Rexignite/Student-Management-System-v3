# accounts/utils.py

import csv
import io
import re
import random
import string
from django.core.mail import send_mail
from django.conf import settings

def validate_indian_phone(phone):
    if not phone:
        return False
    phone = str(phone).strip()
    return re.match(r'^[6-9]\d{9}$', phone) is not None

def validate_name(name):
    if not name:
        return False
    return re.match(r'^[A-Za-z\s]{3,100}$', name) is not None

def parse_csv_file(file):
    try:
        decoded_file = file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        return list(reader)
    except Exception:
        return None

def generate_student_csv(students):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student ID', 'Full Name', 'Class', 'Roll Number', 'Parent Name', 'Parent Phone', 'Address', 'Username'])
    
    for student in students:
        writer.writerow([
            student.student_id,
            student.full_name,
            student.class_name,
            student.roll_number,
            student.parent_name,
            student.parent_phone,
            student.address,
            student.user.username if student.user else ''
        ])
    
    return output.getvalue()

def generate_teacher_csv(teachers):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Teacher ID', 'Full Name', 'Subject', 'Qualification', 'Experience Years', 'Phone', 'Username'])
    
    for teacher in teachers:
        writer.writerow([
            teacher.teacher_id,
            teacher.full_name,
            teacher.subject,
            teacher.qualification,
            teacher.experience_years,
            teacher.phone,
            teacher.user.username if teacher.user else ''
        ])
    
    return output.getvalue()

def generate_attendance_csv(attendances):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Student Name', 'Student ID', 'Subject', 'Status', 'Remarks'])
    
    for att in attendances:
        writer.writerow([
            att.date,
            att.student.full_name,
            att.student.student_id,
            att.subject.subject_name,
            att.status.upper(),
            att.remarks or ''
        ])
    
    return output.getvalue()

def generate_marks_csv(marks):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student Name', 'Student ID', 'Subject', 'Exam Type', 'Marks Obtained', 'Total Marks', 'Percentage'])
    
    for mark in marks:
        percentage = (mark.marks_obtained / mark.total_marks * 100) if mark.total_marks > 0 else 0
        writer.writerow([
            mark.student.full_name,
            mark.student.student_id,
            mark.subject.subject_name,
            mark.exam_type,
            mark.marks_obtained,
            mark.total_marks,
            f"{percentage:.2f}%"
        ])
    
    return output.getvalue()


# ==================== OTP FUNCTIONS FOR PASSWORD RESET ====================

def generate_otp():
    """Generate 6-digit OTP for password reset"""
    return ''.join(random.choices(string.digits, k=6))


def send_otp_email(user_email, otp):
    """Send OTP to user's email for password reset"""
    try:
        subject = "Password Reset OTP - Student Management System"
        message = f"""
        Dear User,
        
        You requested to reset your password for Student Management System.
        
        Your OTP for password reset is: {otp}
        
        This OTP is valid for 10 minutes.
        
        If you didn't request this, please ignore this email.
        
        Thank you,
        Student Management System
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_otp_sms(user_phone, otp):
    """Send OTP to user's phone (SMS) - Optional, for future use"""
    # You can integrate SMS API like Twilio, MSG91, etc. here
    # For now, just return True
    return True


def verify_otp_expiry(created_at):
    """Check if OTP is expired (10 minutes validity)"""
    from django.utils import timezone
    from datetime import timedelta
    
    if not created_at:
        return True  # Expired if no creation time
    
    expiry_time = created_at + timedelta(minutes=10)
    return timezone.now() > expiry_time