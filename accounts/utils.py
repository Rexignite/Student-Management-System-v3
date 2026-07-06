# ====================================================================
# accounts/utils.py
# COMPLETE FILE - STUDENT MANAGEMENT SYSTEM
# WITH OTP FUNCTIONS - FULLY FIXED
# ====================================================================

import csv
import io
import re
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def validate_indian_phone(phone):
    """Validate Indian phone number"""
    if not phone:
        return False
    phone = str(phone).strip()
    return re.match(r'^[6-9]\d{9}$', phone) is not None


def validate_name(name):
    """Validate name - letters and spaces only"""
    if not name:
        return False
    return re.match(r'^[A-Za-z\s]{3,100}$', name) is not None


def parse_csv_file(file):
    """Parse CSV file and return list of dictionaries"""
    try:
        decoded_file = file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        return list(reader)
    except Exception:
        return None


def generate_student_csv(students):
    """Generate CSV for students list"""
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
    """Generate CSV for teachers list"""
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
    """Generate CSV for attendance records"""
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
    """Generate CSV for marks records"""
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


# ====================================================================
# OTP FUNCTIONS FOR PASSWORD RESET - FULLY FIXED
# ====================================================================

def generate_otp():
    """
    Generate 6-digit OTP for password reset
    Example: 483729
    """
    return ''.join(random.choices(string.digits, k=6))


def send_otp_email(user_email, otp):
    """
    Send OTP to user's email for password reset
    Returns True if email sent successfully, False otherwise
    """
    try:
        subject = "Password Reset OTP - Student Management System"
        
        message = f"""
Dear User,

You have requested to reset your password for the Student Management System.

Your One-Time Password (OTP) is: {otp}

This OTP is valid for 10 minutes.

If you did not request this, please ignore this email.

For security, never share this OTP with anyone.

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
        print(f"OTP Email Error: {e}")
        return False


def send_otp_sms(user_phone, otp):
    """
    Send OTP to user's phone (SMS)
    You can integrate SMS API like Twilio, MSG91, etc. here
    Currently returns True as placeholder
    """
    print(f"SMS would be sent to {user_phone} with OTP: {otp}")
    return True


def verify_otp_expiry(created_at):
    """
    Check if OTP is expired (10 minutes validity)
    Returns True if expired, False if valid
    """
    if not created_at:
        return True
    
    expiry_time = created_at + timedelta(minutes=10)
    return timezone.now() > expiry_time


def get_otp_remaining_time(created_at):
    """
    Get remaining time in seconds for OTP validity
    Returns remaining seconds, or 0 if expired
    """
    if not created_at:
        return 0
    
    expiry_time = created_at + timedelta(minutes=10)
    remaining = (expiry_time - timezone.now()).total_seconds()
    return max(0, int(remaining))


def validate_otp(otp):
    """
    Validate OTP format - must be 6 digits
    Returns True if valid, False otherwise
    """
    if not otp:
        return False
    otp = str(otp).strip()
    return re.match(r'^[0-9]{6}$', otp) is not None


# ====================================================================
# ADDITIONAL UTILITY FUNCTIONS
# ====================================================================

def generate_username(first_name, last_name=""):
    """
    Generate a username from first and last name
    Example: John Doe -> john_doe
    """
    first = first_name.lower().strip()
    last = last_name.lower().strip() if last_name else ""
    
    if last:
        username = f"{first}_{last}"
    else:
        username = first
    
    username = re.sub(r'[^a-z0-9_]', '', username)
    
    if len(username) < 3:
        username = f"user_{random.randint(100, 999)}"
    
    return username


def generate_password(length=10):
    """
    Generate a random password
    """
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(characters, k=length))


def generate_student_id():
    """
    Generate a unique student ID
    Format: STU2024XXXXX
    """
    year = timezone.now().year
    count = random.randint(1000, 99999)
    return f"STU{year}{count:05d}"


def generate_teacher_id():
    """
    Generate a unique teacher ID
    Format: TCH2024XXXXX
    """
    year = timezone.now().year
    count = random.randint(1000, 99999)
    return f"TCH{year}{count:05d}"


def get_role_display(role):
    """
    Get display name for user role
    """
    role_map = {
        'director': 'Director',
        'teacher': 'Teacher',
        'student': 'Student',
    }
    return role_map.get(role, role)


def get_status_display(status):
    """
    Get display name for user status
    """
    status_map = {
        'pending': 'Pending Approval',
        'approved': 'Active',
        'rejected': 'Rejected',
    }
    return status_map.get(status, status)


def get_attendance_status_display(status):
    """
    Get display name for attendance status
    """
    status_map = {
        'present': 'Present',
        'absent': 'Absent',
        'late': 'Late',
        'leave': 'Leave',
    }
    return status_map.get(status, status)


def get_exam_type_display(exam_type):
    """
    Get display name for exam type
    """
    exam_map = {
        'mid_term': 'Mid Term',
        'final_term': 'Final Term',
        'assignment': 'Assignment',
        'quiz': 'Quiz',
        'practical': 'Practical',
        'test': 'Test',
    }
    return exam_map.get(exam_type, exam_type)


def calculate_percentage(obtained, total):
    """
    Calculate percentage
    """
    if total <= 0:
        return 0
    return (obtained / total) * 100


def get_grade(percentage):
    """
    Get grade based on percentage
    """
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


def get_grade_description(grade):
    """
    Get description for grade
    """
    grade_map = {
        'A+': 'Outstanding',
        'A': 'Excellent',
        'B+': 'Very Good',
        'B': 'Good',
        'C': 'Satisfactory',
        'D': 'Below Average',
        'F': 'Fail',
    }
    return grade_map.get(grade, 'Unknown')


def sanitize_input(text):
    """
    Sanitize user input to prevent XSS
    """
    if not text:
        return ''
    
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
    return text.strip()


def truncate_text(text, max_length=100, suffix='...'):
    """
    Truncate text to max_length
    """
    if not text:
        return ''
    if len(text) <= max_length:
        return text
    return text[:max_length] + suffix


def get_current_datetime():
    """
    Get current datetime in string format
    """
    return timezone.now().strftime('%Y-%m-%d %H:%M:%S')


def get_current_date():
    """
    Get current date in string format
    """
    return timezone.now().date().strftime('%Y-%m-%d')


def get_month_name(month):
    """
    Get month name from month number
    """
    months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    if 1 <= month <= 12:
        return months[month - 1]
    return 'Unknown'


def get_day_name(day):
    """
    Get day name from day number (0=Monday, 6=Sunday)
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    if 0 <= day <= 6:
        return days[day]
    return 'Unknown'


def is_valid_email(email):
    """
    Validate email format
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_username(username):
    """
    Validate username format
    """
    if not username:
        return False
    if len(username) < 3 or len(username) > 150:
        return False
    return re.match(r'^[a-zA-Z0-9_.]+$', username) is not None


def is_valid_password(password):
    """
    Validate password strength
    """
    if not password:
        return False
    if len(password) < 6:
        return False
    if not any(c.isdigit() for c in password):
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    return True


def generate_random_color():
    """
    Generate a random hex color
    """
    return '#{:06x}'.format(random.randint(0, 0xFFFFFF))


def get_file_extension(filename):
    """
    Get file extension from filename
    """
    if not filename:
        return ''
    return filename.split('.')[-1].lower()


def is_image_file(filename):
    """
    Check if file is an image
    """
    valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    ext = get_file_extension(filename)
    return ext in valid_extensions


def format_phone_number(phone):
    """
    Format phone number to Indian format
    Example: 9876543210 -> +91 98765 43210
    """
    if not phone:
        return ''
    phone = str(phone).strip()
    if len(phone) == 10:
        return f"+91 {phone[:5]} {phone[5:]}"
    return phone


def format_date(date_obj, format_str='%d-%m-%Y'):
    """
    Format date object to string
    """
    if not date_obj:
        return ''
    return date_obj.strftime(format_str)


def format_datetime(dt_obj, format_str='%d-%m-%Y %H:%M'):
    """
    Format datetime object to string
    """
    if not dt_obj:
        return ''
    return dt_obj.strftime(format_str)


def get_week_number(date_obj):
    """
    Get week number of the year
    """
    if not date_obj:
        return 0
    return date_obj.isocalendar()[1]


def get_quarter(month):
    """
    Get quarter of the year for a given month
    """
    if 1 <= month <= 3:
        return 1
    elif 4 <= month <= 6:
        return 2
    elif 7 <= month <= 9:
        return 3
    elif 10 <= month <= 12:
        return 4
    return 0


def get_academic_year(date_obj):
    """
    Get academic year for a given date
    Example: June 2024 to May 2025 -> 2024-25
    """
    if not date_obj:
        return ''
    year = date_obj.year
    if date_obj.month >= 6:
        return f"{year}-{str(year+1)[-2:]}"
    else:
        return f"{year-1}-{str(year)[-2:]}"