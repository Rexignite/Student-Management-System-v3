# ====================================================================
# accounts/views.py
# COMPLETE FILE - STUDENT MANAGEMENT SYSTEM
# WITH OTP BASED PASSWORD RESET SYSTEM - FULLY FIXED
# WITH DIRECTOR USER MANAGEMENT
# WITH DELETE & RE-ADD FUNCTIONALITY FIXED
# ====================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Count, Sum
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.conf import settings
from django.middleware.csrf import get_token
from django.utils import timezone
from datetime import datetime, date, timedelta
import csv
import json
import re
import io
import random

from .models import User
from users.models import Student, Teacher
from academic.models import Subject, Attendance, Marks, Notification
from .utils import (
    parse_csv_file, validate_indian_phone, validate_name,
    generate_student_csv, generate_teacher_csv,
    generate_attendance_csv, generate_marks_csv,
    generate_otp, send_otp_email, verify_otp_expiry
)


# ==================== EMAIL HELPER FUNCTIONS ====================

def send_welcome_email(user, password=None, role=None):
    """Send welcome email to new user"""
    try:
        role_name = role or user.role
        subject = f"Welcome to Student Management System - {role_name.title()}"
        
        if password:
            message = f"""
            Dear {user.username},
            
            Your account has been created successfully!
            
            📋 Login Details:
            Username: {user.username}
            Password: {password}
            
            🔗 Login URL: http://127.0.0.1:8000/login/
            
            Please change your password after first login.
            
            Thank you,
            Student Management System
            """
        else:
            message = f"""
            Dear {user.username},
            
            Your account has been approved successfully!
            
            📋 Login Details:
            Username: {user.username}
            
            🔗 Login URL: http://127.0.0.1:8000/login/
            
            Thank you,
            Student Management System
            """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_approval_email(user, approved_by):
    """Send approval email to user"""
    try:
        subject = f"Account Approved - Student Management System"
        message = f"""
        Dear {user.username},
        
        Congratulations! Your account has been approved by {approved_by.username}.
        
        📋 Login Details:
        Username: {user.username}
        
        🔗 Login URL: http://127.0.0.1:8000/login/
        
        You can now login and access your dashboard.
        
        Thank you,
        Student Management System
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        return True
    except Exception:
        return False


def send_rejection_email(user, reason):
    """Send rejection email to user"""
    try:
        subject = f"Account Update - Student Management System"
        message = f"""
        Dear {user.username},
        
        We regret to inform you that your account registration has been rejected.
        
        Reason: {reason}
        
        If you have any questions, please contact the administrator.
        
        Thank you,
        Student Management System
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        return True
    except Exception:
        return False


# ==================== PROFESSIONAL VALIDATION FUNCTIONS ====================

def capitalize_name(name):
    """Convert name to proper case"""
    if not name:
        return ''
    return ' '.join(word.capitalize() for word in name.strip().split())


def validate_full_name_professional(name, field_label="Name"):
    """Professional name validation - letters, spaces, dots, hyphens"""
    if not name or not name.strip():
        return False, f"❌ {field_label} is required!"
    
    name = name.strip()
    
    if len(name) < 3:
        return False, f"❌ {field_label} must be at least 3 characters!"
    
    if len(name) > 100:
        return False, f"❌ {field_label} is too long! Maximum 100 characters allowed."
    
    if not re.match(r'^[A-Za-z\s\.\-]+$', name):
        return False, f"❌ {field_label} can only contain letters, spaces, dots (.), and hyphens (-)!"
    
    formatted_name = ' '.join(word.capitalize() for word in name.split())
    return True, formatted_name


def validate_phone_professional(phone, field_label="Phone number"):
    """Professional Indian mobile number validation"""
    if not phone or not str(phone).strip():
        return False, f"❌ {field_label} is required!"
    
    phone = str(phone).strip()
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    if not phone.isdigit():
        return False, f"❌ {field_label} must contain only digits!"
    
    if len(phone) != 10:
        return False, f"❌ {field_label} must be exactly 10 digits!"
    
    if phone[0] not in ['6', '7', '8', '9']:
        return False, f"❌ {field_label} must start with 6, 7, 8, or 9!"
    
    if phone == phone[0] * 10:
        return False, f"❌ Invalid {field_label}! Please enter a valid mobile number."
    
    return True, phone


def validate_email_professional(email):
    """Professional email validation"""
    if not email or not email.strip():
        return True, ""
    
    email = email.strip().lower()
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "❌ Please enter a valid email address (e.g., name@example.com)!"
    
    return True, email


def validate_address_professional(address):
    """Professional address validation"""
    if not address or not address.strip():
        return False, "❌ Address is required!"
    
    address = address.strip()
    
    if len(address) < 10:
        return False, "❌ Address must be at least 10 characters!"
    
    if len(address) > 500:
        return False, "❌ Address is too long! Maximum 500 characters allowed."
    
    if not re.match(r'^[A-Za-z0-9\s\.,\-\/#]+$', address):
        return False, "❌ Address contains invalid characters!"
    
    return True, address


def validate_username_professional(username):
    """Professional username validation"""
    if not username or not username.strip():
        return False, "❌ Username is required!"
    
    username = username.strip().lower()
    
    if len(username) < 3:
        return False, "❌ Username must be at least 3 characters!"
    
    if len(username) > 150:
        return False, "❌ Username is too long! Maximum 150 characters."
    
    if not re.match(r'^[a-z0-9_.]+$', username):
        return False, "❌ Username can only contain letters, numbers, dots (.), and underscores (_)!"
    
    if User.objects.filter(username=username).exists():
        return False, "❌ Username already taken! Please choose another username."
    
    return True, username


def validate_password_professional(password, confirm_password):
    """Professional password validation with strength check"""
    if not password:
        return False, "❌ Password is required!"
    
    if len(password) < 6:
        return False, "❌ Password must be at least 6 characters long!"
    
    if len(password) > 128:
        return False, "❌ Password is too long! Maximum 128 characters."
    
    if not any(char.isdigit() for char in password):
        return False, "❌ Password must contain at least one number!"
    
    if not any(char.isupper() for char in password):
        return False, "❌ Password must contain at least one uppercase letter!"
    
    if not any(char.islower() for char in password):
        return False, "❌ Password must contain at least one lowercase letter!"
    
    if password != confirm_password:
        return False, "❌ Passwords do not match!"
    
    return True, password


def validate_subject_code_professional(code):
    """Professional subject code validation - flexible format"""
    if not code or not code.strip():
        return False, "❌ Subject code is required!"
    
    code = code.strip().upper()
    
    if len(code) < 2:
        return False, "❌ Subject code must be at least 2 characters!"
    
    if len(code) > 10:
        return False, "❌ Subject code is too long! Maximum 10 characters allowed."
    
    if not re.match(r'^[A-Z0-9\-_]+$', code):
        return False, "❌ Subject code can only contain letters, numbers, hyphens (-), and underscores (_)!"
    
    if Subject.objects.filter(subject_code=code).exists():
        return False, f"❌ Subject code '{code}' already exists!"
    
    return True, code


def validate_subject_name_professional(subject_name):
    """Professional subject name validation"""
    if not subject_name or not subject_name.strip():
        return False, "❌ Subject name is required!"
    
    subject_name = subject_name.strip().title()
    
    if len(subject_name) < 3:
        return False, "❌ Subject name must be at least 3 characters!"
    
    if len(subject_name) > 100:
        return False, "❌ Subject name is too long! Maximum 100 characters."
    
    return True, subject_name


def validate_student_id_professional(student_id):
    """Professional student ID validation"""
    if not student_id or not student_id.strip():
        return False, "❌ Student ID is required!"
    
    student_id = student_id.strip().upper()
    
    if len(student_id) < 3:
        return False, "❌ Student ID must be at least 3 characters!"
    
    if len(student_id) > 20:
        return False, "❌ Student ID is too long! Maximum 20 characters."
    
    if not re.match(r'^[A-Z0-9\-_]+$', student_id):
        return False, "❌ Student ID can only contain letters, numbers, hyphens (-), and underscores (_)!"
    
    if Student.objects.filter(student_id=student_id).exists():
        return False, f"❌ Student ID '{student_id}' already exists!"
    
    return True, student_id


def validate_teacher_id_professional(teacher_id):
    """Professional teacher ID validation"""
    if not teacher_id or not teacher_id.strip():
        return False, "❌ Teacher ID is required!"
    
    teacher_id = teacher_id.strip().upper()
    
    if len(teacher_id) < 3:
        return False, "❌ Teacher ID must be at least 3 characters!"
    
    if len(teacher_id) > 20:
        return False, "❌ Teacher ID is too long! Maximum 20 characters."
    
    if not re.match(r'^[A-Z0-9\-_]+$', teacher_id):
        return False, "❌ Teacher ID can only contain letters, numbers, hyphens (-), and underscores (_)!"
    
    if Teacher.objects.filter(teacher_id=teacher_id).exists():
        return False, f"❌ Teacher ID '{teacher_id}' already exists!"
    
    return True, teacher_id


def validate_roll_number_professional(roll_number):
    """Professional roll number validation"""
    if not roll_number or not roll_number.strip():
        return False, "❌ Roll number is required!"
    
    roll_number = roll_number.strip().upper()
    
    if len(roll_number) > 10:
        return False, "❌ Roll number is too long! Maximum 10 characters."
    
    if not re.match(r'^[A-Z0-9\-_]+$', roll_number):
        return False, "❌ Roll number can only contain letters, numbers, hyphens (-), and underscores (_)!"
    
    return True, roll_number


def validate_class_name_professional(class_name):
    """Professional class/course name validation"""
    if not class_name or not class_name.strip():
        return False, "❌ Class/Course name is required!"
    
    class_name = class_name.strip().title()
    
    if len(class_name) < 2:
        return False, "❌ Class/Course name must be at least 2 characters!"
    
    if len(class_name) > 50:
        return False, "❌ Class/Course name is too long! Maximum 50 characters."
    
    if not re.match(r'^[A-Za-z0-9\s\-]+$', class_name):
        return False, "❌ Class/Course name can only contain letters, numbers, spaces, and hyphens!"
    
    return True, class_name


def validate_qualification_professional(qualification):
    """Professional qualification validation"""
    if not qualification or not qualification.strip():
        return False, "❌ Qualification is required!"
    
    qualification = qualification.strip()
    
    if len(qualification) < 2:
        return False, "❌ Qualification must be at least 2 characters!"
    
    if len(qualification) > 200:
        return False, "❌ Qualification is too long! Maximum 200 characters."
    
    return True, qualification


def validate_experience_professional(years):
    """Professional experience years validation"""
    try:
        years = int(years) if years else 0
        if years < 0:
            return False, "❌ Experience years cannot be negative!"
        if years > 50:
            return False, "❌ Experience years cannot exceed 50 years!"
        return True, years
    except ValueError:
        return False, "❌ Please enter a valid number for experience years!"


def validate_notification_title_professional(title):
    """Professional notification title validation"""
    if not title or not title.strip():
        return False, "❌ Title is required!"
    
    title = title.strip()
    
    if len(title) < 3:
        return False, "❌ Title must be at least 3 characters!"
    
    if len(title) > 200:
        return False, "❌ Title is too long! Maximum 200 characters."
    
    return True, title


def validate_notification_message_professional(message):
    """Professional notification message validation"""
    if not message or not message.strip():
        return False, "❌ Message is required!"
    
    message = message.strip()
    
    if len(message) < 5:
        return False, "❌ Message must be at least 5 characters!"
    
    if len(message) > 1000:
        return False, "❌ Message is too long! Maximum 1000 characters."
    
    return True, message


# ====================================================================
# PART 1: AUTHENTICATION VIEWS
# ====================================================================

@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'director':
            return redirect('/director/')
        elif request.user.role == 'teacher':
            return redirect('/teacher/')
        elif request.user.role == 'student':
            return redirect('/student/')
        return redirect('/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.status == 'pending':
                messages.error(request, '❌ Your account is pending approval. Please wait for admin approval.')
                return redirect('/login/')
            elif user.status == 'rejected':
                messages.error(request, '❌ Your account has been rejected. Please contact admin for more information.')
                return redirect('/login/')
            
            login(request, user)
            messages.success(request, f'✨ Welcome back, {user.username}!')
            
            if user.role == 'director':
                return redirect('/director/')
            elif user.role == 'teacher':
                return redirect('/teacher/')
            elif user.role == 'student':
                return redirect('/student/')
            else:
                return redirect('/')
        else:
            messages.error(request, '❌ Invalid username or password! Please try again.')
    
    return render(request, 'accounts/login.html')


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role')
        email = request.POST.get('email', '')
        
        has_error = False
        
        valid, username_result = validate_username_professional(username)
        if not valid:
            messages.error(request, username_result)
            has_error = True
        
        valid, password_result = validate_password_professional(password, confirm_password)
        if not valid:
            messages.error(request, password_result)
            has_error = True
        
        if email:
            valid, email_result = validate_email_professional(email)
            if not valid:
                messages.error(request, email_result)
                has_error = True
        else:
            email_result = ''
        
        if has_error:
            return redirect('/signup/')
        
        user = User.objects.create(
            username=username_result,
            password=make_password(password),
            role=role,
            email=email_result,
            status='pending',
            is_active=True,
        )
        
        if role == 'student':
            full_name = request.POST.get('full_name', username)
            valid, full_name_result = validate_full_name_professional(full_name, "Full name")
            if not valid:
                messages.error(request, full_name_result)
                user.delete()
                return redirect('/signup/')
            
            parent_phone = request.POST.get('parent_phone', '')
            valid, phone_result = validate_phone_professional(parent_phone, "Parent phone number")
            if not valid:
                messages.error(request, phone_result)
                user.delete()
                return redirect('/signup/')
            
            address = request.POST.get('address', '')
            valid, address_result = validate_address_professional(address)
            if not valid:
                messages.error(request, address_result)
                user.delete()
                return redirect('/signup/')
            
            class_name = request.POST.get('class_name', 'Not Assigned')
            valid, class_result = validate_class_name_professional(class_name)
            if not valid:
                messages.error(request, class_result)
                user.delete()
                return redirect('/signup/')
            
            roll_number = request.POST.get('roll_number', '001')
            valid, roll_result = validate_roll_number_professional(roll_number)
            if not valid:
                messages.error(request, roll_result)
                user.delete()
                return redirect('/signup/')
            
            Student.objects.create(
                user=user,
                student_id=f"STU{User.objects.count():05d}",
                full_name=full_name_result,
                class_name=class_result,
                roll_number=roll_result,
                parent_name=capitalize_name(request.POST.get('parent_name', '')),
                parent_phone=phone_result,
                address=address_result
            )
            messages.success(request, '🎉 Registration submitted! Waiting for admin approval.')
            
        elif role == 'teacher':
            full_name = request.POST.get('full_name', username)
            valid, full_name_result = validate_full_name_professional(full_name, "Full name")
            if not valid:
                messages.error(request, full_name_result)
                user.delete()
                return redirect('/signup/')
            
            phone = request.POST.get('phone', '')
            valid, phone_result = validate_phone_professional(phone, "Phone number")
            if not valid:
                messages.error(request, phone_result)
                user.delete()
                return redirect('/signup/')
            
            subject = request.POST.get('subject', 'General')
            valid, subject_result = validate_class_name_professional(subject)
            if not valid:
                messages.error(request, subject_result)
                user.delete()
                return redirect('/signup/')
            
            qualification = request.POST.get('qualification', 'Graduate')
            valid, qual_result = validate_qualification_professional(qualification)
            if not valid:
                messages.error(request, qual_result)
                user.delete()
                return redirect('/signup/')
            
            experience_years = request.POST.get('experience_years', 0)
            valid, exp_result = validate_experience_professional(experience_years)
            if not valid:
                messages.error(request, exp_result)
                user.delete()
                return redirect('/signup/')
            
            Teacher.objects.create(
                user=user,
                teacher_id=f"TCH{User.objects.count():05d}",
                full_name=full_name_result,
                subject=subject_result,
                qualification=qual_result,
                experience_years=exp_result,
                phone=phone_result
            )
            messages.success(request, '👨‍🏫 Registration submitted! Waiting for admin approval.')
        
        return redirect('/login/')
    
    return render(request, 'accounts/signup.html')


def logout_view(request):
    logout(request)
    messages.success(request, '✅ You have been logged out successfully!')
    return redirect('/login/')


@login_required
def dashboard(request):
    role = request.user.role
    
    if role == 'director':
        return redirect('/director/')
    elif role == 'teacher':
        return redirect('/teacher/')
    elif role == 'student':
        return redirect('/student/')
    else:
        messages.error(request, '❌ Invalid user role!')
        return redirect('/login/')


# ====================================================================
# PART 2: OTP BASED PASSWORD RESET VIEWS - FULLY FIXED
# ====================================================================

def forgot_password(request):
    """Step 1: User enters email, OTP sent"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, '❌ Please enter your email address!')
            return redirect('/forgot-password/')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate OTP
            otp = generate_otp()
            user.reset_otp = otp
            user.reset_otp_created_at = timezone.now()
            user.reset_otp_verified = False
            user.save(update_fields=['reset_otp', 'reset_otp_created_at', 'reset_otp_verified'])
            
            # Send OTP email
            if send_otp_email(email, otp):
                # Store email in session
                request.session['reset_email'] = email
                request.session['reset_email_timestamp'] = timezone.now().isoformat()
                
                messages.success(request, f'✅ OTP sent to {email}. Valid for 10 minutes.')
                return redirect('/verify-otp/')
            else:
                messages.error(request, '❌ Failed to send OTP email. Please try again.')
                return redirect('/forgot-password/')
            
        except User.DoesNotExist:
            messages.error(request, '❌ No account found with this email address!')
            return redirect('/forgot-password/')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return redirect('/forgot-password/')
    
    return render(request, 'accounts/forgot_password.html')


def verify_otp(request):
    """Step 2: User enters OTP, verify"""
    # Get email from session
    email = request.session.get('reset_email', '')
    
    if not email:
        messages.error(request, '❌ Session expired! Please try again.')
        return redirect('/forgot-password/')
    
    if request.method == 'POST':
        otp = request.POST.get('otp', '').strip()
        
        if not otp or len(otp) != 6:
            messages.error(request, '❌ Please enter a valid 6-digit OTP!')
            return redirect('/verify-otp/')
        
        try:
            user = User.objects.get(email=email)
            
            # Check if OTP exists and matches
            if not user.reset_otp:
                messages.error(request, '❌ No OTP found. Please request a new one.')
                return redirect('/forgot-password/')
            
            if user.reset_otp == otp:
                # Check if OTP expired
                if verify_otp_expiry(user.reset_otp_created_at):
                    messages.error(request, '❌ OTP has expired! Please request a new one.')
                    return redirect('/forgot-password/')
                
                # OTP verified - mark as verified
                user.reset_otp_verified = True
                user.save(update_fields=['reset_otp_verified'])
                
                messages.success(request, '✅ OTP verified! Set your new password.')
                return redirect('/set-new-password/')
            else:
                messages.error(request, '❌ Invalid OTP! Please try again.')
                
        except User.DoesNotExist:
            messages.error(request, '❌ User not found!')
            return redirect('/forgot-password/')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return redirect('/verify-otp/')
    
    return render(request, 'accounts/verify_otp.html', {'email': email})


def set_new_password(request):
    """Step 3: User sets new password after OTP verification - FULLY FIXED"""
    # Get email from session
    email = request.session.get('reset_email', '')
    
    if not email:
        messages.error(request, '❌ Session expired! Please try again.')
        return redirect('/forgot-password/')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        try:
            user = User.objects.get(email=email)
            
            # Check if OTP verified
            if not user.reset_otp_verified:
                messages.error(request, '❌ Please verify OTP first!')
                return redirect('/forgot-password/')
            
            # Validate password
            if not new_password:
                messages.error(request, '❌ Please enter a new password!')
                return redirect('/set-new-password/')
            
            if not confirm_password:
                messages.error(request, '❌ Please confirm your password!')
                return redirect('/set-new-password/')
            
            if new_password != confirm_password:
                messages.error(request, '❌ Passwords do not match!')
                return redirect('/set-new-password/')
            
            if len(new_password) < 6:
                messages.error(request, '❌ Password must be at least 6 characters!')
                return redirect('/set-new-password/')
            
            # ============================================
            # ✅ FIX: Properly set new password
            # ============================================
            user.set_password(new_password)
            
            # Clear OTP fields
            user.reset_otp = None
            user.reset_otp_created_at = None
            user.reset_otp_verified = False
            
            # ✅ CRITICAL: Use save() NOT update_fields
            user.save()
            # ============================================
            
            # Clear session
            if 'reset_email' in request.session:
                del request.session['reset_email']
            if 'reset_email_timestamp' in request.session:
                del request.session['reset_email_timestamp']
            
            messages.success(request, '✅ Password changed successfully! Please login with your new password.')
            return redirect('/login/')
            
        except User.DoesNotExist:
            messages.error(request, '❌ User not found!')
            return redirect('/forgot-password/')
        except Exception as e:
            messages.error(request, f'❌ Error: {str(e)}')
            return redirect('/set-new-password/')
    
    return render(request, 'accounts/set_new_password.html', {'email': email})


def resend_otp(request):
    """Resend OTP to user email"""
    email = request.session.get('reset_email', '')
    
    if not email:
        messages.error(request, '❌ Session expired! Please try again.')
        return redirect('/forgot-password/')
    
    try:
        user = User.objects.get(email=email)
        
        # Generate new OTP
        otp = generate_otp()
        user.reset_otp = otp
        user.reset_otp_created_at = timezone.now()
        user.reset_otp_verified = False
        user.save(update_fields=['reset_otp', 'reset_otp_created_at', 'reset_otp_verified'])
        
        # Send OTP email
        if send_otp_email(email, otp):
            messages.success(request, f'✅ New OTP sent to {email}. Valid for 10 minutes.')
        else:
            messages.error(request, '❌ Failed to send OTP. Please try again.')
        
    except User.DoesNotExist:
        messages.error(request, '❌ User not found!')
        return redirect('/forgot-password/')
    except Exception as e:
        messages.error(request, f'❌ Error: {str(e)}')
    
    return redirect('/verify-otp/')


# ====================================================================
# PART 3: PROFILE VIEWS
# ====================================================================

@login_required
def view_profile(request):
    context = {}
    
    if request.user.role == 'teacher' and hasattr(request.user, 'teacher_profile'):
        context['profile'] = request.user.teacher_profile
        context['role'] = 'teacher'
    elif request.user.role == 'student' and hasattr(request.user, 'student_profile'):
        context['profile'] = request.user.student_profile
        context['role'] = 'student'
    else:
        context['profile'] = request.user
        context['role'] = 'director'
    
    return render(request, 'accounts/profile.html', context)


@login_required
def update_profile_pic(request):
    if request.method == 'POST' and request.FILES.get('profile_pic'):
        profile_pic = request.FILES['profile_pic']
        
        if profile_pic.size > 2 * 1024 * 1024:
            messages.error(request, '❌ File size too large! Maximum 2MB allowed.')
            return redirect('/profile/')
        
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/jpg']
        if profile_pic.content_type not in allowed_types:
            messages.error(request, '❌ Invalid file type! Only JPG, PNG, GIF allowed.')
            return redirect('/profile/')
        
        if request.user.role == 'teacher' and hasattr(request.user, 'teacher_profile'):
            if request.user.teacher_profile.profile_pic:
                request.user.teacher_profile.profile_pic.delete()
            request.user.teacher_profile.profile_pic = profile_pic
            request.user.teacher_profile.save()
            messages.success(request, '✅ Profile picture updated!')
        elif request.user.role == 'student' and hasattr(request.user, 'student_profile'):
            if request.user.student_profile.profile_pic:
                request.user.student_profile.profile_pic.delete()
            request.user.student_profile.profile_pic = profile_pic
            request.user.student_profile.save()
            messages.success(request, '✅ Profile picture updated!')
        elif request.user.role == 'director':
            if request.user.profile_pic:
                request.user.profile_pic.delete()
            request.user.profile_pic = profile_pic
            request.user.save()
            messages.success(request, '✅ Profile picture updated!')
        
        return redirect('/profile/')
    
    return redirect('/profile/')


@login_required
def edit_profile(request):
    user = request.user
    
    # Director ke liye handling
    if user.role == 'director':
        if request.method == 'POST':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            
            has_error = False
            
            if first_name:
                if len(first_name) < 2:
                    messages.error(request, '❌ First name must be at least 2 characters!')
                    has_error = True
                elif len(first_name) > 30:
                    messages.error(request, '❌ First name is too long (max 30 characters)!')
                    has_error = True
                elif not re.match(r'^[A-Za-z]+$', first_name):
                    messages.error(request, '❌ First name can only contain letters!')
                    has_error = True
                else:
                    user.first_name = first_name.capitalize()
            
            if last_name:
                if len(last_name) < 2:
                    messages.error(request, '❌ Last name must be at least 2 characters!')
                    has_error = True
                elif len(last_name) > 30:
                    messages.error(request, '❌ Last name is too long (max 30 characters)!')
                    has_error = True
                elif not re.match(r'^[A-Za-z]+$', last_name):
                    messages.error(request, '❌ Last name can only contain letters!')
                    has_error = True
                else:
                    user.last_name = last_name.capitalize()
            
            if email:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    messages.error(request, '❌ Enter a valid email address!')
                    has_error = True
                else:
                    if User.objects.filter(email=email).exclude(id=user.id).exists():
                        messages.error(request, '❌ This email is already registered!')
                        has_error = True
                    else:
                        user.email = email.lower()
            
            if phone:
                if not phone.isdigit():
                    messages.error(request, '❌ Phone number must contain only digits!')
                    has_error = True
                elif len(phone) != 10:
                    messages.error(request, '❌ Phone number must be exactly 10 digits!')
                    has_error = True
                elif phone[0] not in ['6', '7', '8', '9']:
                    messages.error(request, '❌ Phone number must start with 6,7,8,9!')
                    has_error = True
                else:
                    user.phone = phone
            
            if not has_error:
                user.save()
                messages.success(request, '✅ Profile updated successfully!')
                return redirect('/profile/')
        
        return render(request, 'accounts/edit_profile.html', {'user': user, 'role': 'director'})
    
    # For Teacher and Student
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        has_error = False
        
        if first_name:
            if len(first_name) < 2:
                messages.error(request, '❌ First name must be at least 2 characters!')
                has_error = True
            elif len(first_name) > 30:
                messages.error(request, '❌ First name is too long (max 30 characters)!')
                has_error = True
            elif not re.match(r'^[A-Za-z]+$', first_name):
                messages.error(request, '❌ First name can only contain letters!')
                has_error = True
            else:
                user.first_name = first_name.capitalize()
        
        if last_name:
            if len(last_name) < 2:
                messages.error(request, '❌ Last name must be at least 2 characters!')
                has_error = True
            elif len(last_name) > 30:
                messages.error(request, '❌ Last name is too long (max 30 characters)!')
                has_error = True
            elif not re.match(r'^[A-Za-z]+$', last_name):
                messages.error(request, '❌ Last name can only contain letters!')
                has_error = True
            else:
                user.last_name = last_name.capitalize()
        
        if email:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                messages.error(request, '❌ Enter a valid email address!')
                has_error = True
            else:
                if User.objects.filter(email=email).exclude(id=user.id).exists():
                    messages.error(request, '❌ This email is already registered!')
                    has_error = True
                else:
                    user.email = email.lower()
        
        if phone:
            if not phone.isdigit():
                messages.error(request, '❌ Phone number must contain only digits!')
                has_error = True
            elif len(phone) != 10:
                messages.error(request, '❌ Phone number must be exactly 10 digits!')
                has_error = True
            elif phone[0] not in ['6', '7', '8', '9']:
                messages.error(request, '❌ Phone number must start with 6,7,8,9!')
                has_error = True
            else:
                user.phone = phone
        
        if not has_error:
            user.save()
            messages.success(request, '✅ Profile updated successfully!')
            return redirect('/profile/')
    
    profile_data = {}
    if user.role == 'teacher' and hasattr(user, 'teacher_profile'):
        profile_data['full_name'] = user.teacher_profile.full_name
        profile_data['teacher_id'] = user.teacher_profile.teacher_id
        profile_data['subject'] = user.teacher_profile.subject
        profile_data['qualification'] = user.teacher_profile.qualification
        profile_data['experience_years'] = user.teacher_profile.experience_years
    elif user.role == 'student' and hasattr(user, 'student_profile'):
        profile_data['full_name'] = user.student_profile.full_name
        profile_data['student_id'] = user.student_profile.student_id
        profile_data['class_name'] = user.student_profile.class_name
        profile_data['roll_number'] = user.student_profile.roll_number
        profile_data['parent_name'] = user.student_profile.parent_name
        profile_data['parent_phone'] = user.student_profile.parent_phone
        profile_data['address'] = user.student_profile.address    
    context = {
        'user': user,
        'role': user.role,
        'profile_data': profile_data,
    }
    return render(request, 'accounts/edit_profile.html', context)


# ====================================================================
# PART 4: DIRECTOR DASHBOARD
# ====================================================================

@login_required
@user_passes_test(lambda u: u.role == 'director')
def director_dashboard(request):
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_subjects = Subject.objects.count()
    pending_approvals = User.objects.filter(status='pending').count()
    
    attendances = Attendance.objects.all()
    total_present = attendances.filter(status='present').count()
    total_absent = attendances.filter(status='absent').count()
    total_late = attendances.filter(status='late').count()
    total_leave = attendances.filter(status='leave').count()
    
    subjects_with_teachers = Subject.objects.select_related('teacher').all()
    recent_notifications = Notification.objects.all().order_by('-created_at')[:10]
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_subjects': total_subjects,
        'pending_approvals': pending_approvals,
        'total_present': total_present,
        'total_absent': total_absent,
        'total_late': total_late,
        'total_leave': total_leave,
        'subjects_with_teachers': subjects_with_teachers,
        'recent_notifications': recent_notifications,
        'director': request.user,
    }
    return render(request, 'director/dashboard.html', context)


# ====================================================================
# PART 5: DIRECTOR - NOTIFICATION SEND
# ====================================================================

@login_required
@user_passes_test(lambda u: u.role == 'director')
def send_notification(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        target_role = request.POST.get('target_role', 'all')
        notification_type = request.POST.get('notification_type', 'notice')
        
        valid, title_result = validate_notification_title_professional(title)
        if not valid:
            messages.error(request, title_result)
            return redirect('/director/')
        
        valid, message_result = validate_notification_message_professional(message)
        if not valid:
            messages.error(request, message_result)
            return redirect('/director/')
        
        Notification.objects.create(
            title=title_result,
            message=message_result,
            notification_type=notification_type,
            target_role=target_role,
            created_by=request.user,
        )
        
        target_text = {'all': 'ALL USERS', 'teacher': 'TEACHERS', 'student': 'STUDENTS'}.get(target_role, 'USERS')
        messages.success(request, f'✅ Notification "{title_result}" sent to {target_text} successfully!')
        return redirect('/director/')
    
    return redirect('/director/')


# ====================================================================
# PART 6: DIRECTOR - NOTIFICATION MANAGEMENT
# ====================================================================

@login_required
@user_passes_test(lambda u: u.role == 'director')
def manage_notifications(request):
    notifications = Notification.objects.all().order_by('-created_at')
    return render(request, 'director/manage_notifications.html', {'notifications': notifications})


@login_required
@user_passes_test(lambda u: u.role == 'director')
def add_notification(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        notification_type = request.POST.get('notification_type', 'notice')
        target_role = request.POST.get('target_role', 'all')
        
        valid, title_result = validate_notification_title_professional(title)
        if not valid:
            messages.error(request, title_result)
            return redirect('/director/notifications/add/')
        
        valid, message_result = validate_notification_message_professional(message)
        if not valid:
            messages.error(request, message_result)
            return redirect('/director/notifications/add/')
        
        Notification.objects.create(
            title=title_result,
            message=message_result,
            notification_type=notification_type,
            target_role=target_role,
            created_by=request.user,
        )
        messages.success(request, f'✅ Notification "{title_result}" added successfully!')
        return redirect('/director/notifications/')
    
    context = {
        'notification_types': Notification.NOTIFICATION_TYPES,
        'target_roles': Notification.TARGET_ROLES,
    }
    return render(request, 'director/add_notification.html', context)


@login_required
@user_passes_test(lambda u: u.role == 'director')
def edit_notification(request, notif_id):
    notification = get_object_or_404(Notification, id=notif_id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        notification_type = request.POST.get('notification_type', 'notice')
        target_role = request.POST.get('target_role', 'all')
        
        valid, title_result = validate_notification_title_professional(title)
        if not valid:
            messages.error(request, title_result)
            return redirect(f'/director/notifications/edit/{notif_id}/')
        
        valid, message_result = validate_notification_message_professional(message)
        if not valid:
            messages.error(request, message_result)
            return redirect(f'/director/notifications/edit/{notif_id}/')
        
        notification.title = title_result
        notification.message = message_result
        notification.notification_type = notification_type
        notification.target_role = target_role
        notification.save()
        messages.success(request, f'✅ Notification "{title_result}" updated successfully!')
        return redirect('/director/notifications/')
    
    context = {
        'notification': notification,
        'notification_types': Notification.NOTIFICATION_TYPES,
        'target_roles': Notification.TARGET_ROLES,
    }
    return render(request, 'director/edit_notification.html', context)


@login_required
@user_passes_test(lambda u: u.role == 'director')
def delete_notification(request, notif_id):
    notification = get_object_or_404(Notification, id=notif_id)
    
    if request.method == 'POST':
        notification_title = notification.title
        notification.delete()
        messages.success(request, f'✅ Notification "{notification_title}" deleted successfully!')
        return redirect('/director/notifications/')
    
    return render(request, 'director/delete_notification.html', {'notification': notification})


# ====================================================================
# PART 7: NOTIFICATIONS VIEW (For All Users - View Only)
# ====================================================================

@login_required
def view_notifications(request):
    user = request.user
    
    if user.role == 'director':
        notifications = Notification.objects.filter(
            Q(target_role='director') | Q(target_role='all')
        )
    elif user.role == 'teacher':
        teacher = user.teacher_profile if hasattr(user, 'teacher_profile') else None
        notifications = Notification.objects.filter(
            Q(target_role='teacher') | Q(target_role='all') | Q(target_teacher=teacher)
        )
    elif user.role == 'student':
        student = user.student_profile if hasattr(user, 'student_profile') else None
        notifications = Notification.objects.filter(
            Q(target_role='student') | Q(target_role='all') | Q(target_student=student)
        )
    else:
        notifications = Notification.objects.none()
    
    notifications = notifications.order_by('-created_at')
    
    context = {
        'notifications': notifications,
        'unread_count': notifications.filter(is_read=False).count()
    }
    return render(request, 'notifications/list.html', context)


@login_required
def mark_notification_read(request, notif_id):
    notification = get_object_or_404(Notification, id=notif_id)
    notification.is_read = True
    notification.save()
    messages.success(request, '✅ Notification marked as read!')
    return redirect('/notifications/')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read for current user"""
    user = request.user
    
    if user.role == 'teacher' and hasattr(user, 'teacher_profile'):
        Notification.objects.filter(target_teacher=user.teacher_profile, is_read=False).update(is_read=True)
    elif user.role == 'student' and hasattr(user, 'student_profile'):
        Notification.objects.filter(target_student=user.student_profile, is_read=False).update(is_read=True)
    else:
        Notification.objects.filter(target_role=user.role, is_read=False).update(is_read=True)
    
    messages.success(request, '✅ All notifications marked as read!')
    return redirect('/notifications/')


# ====================================================================
# PART 8: DIRECTOR - USER APPROVAL MANAGEMENT
# ====================================================================

@login_required
@user_passes_test(lambda u: u.role == 'director')
def pending_users(request):
    pending_users_list = User.objects.filter(status='pending').order_by('-created_at')
    
    paginator = Paginator(pending_users_list, 20)
    page_number = request.GET.get('page')
    pending_users = paginator.get_page(page_number)
    
    users_data = []
    for user in pending_users:
        user_data = {
            'user': user,
            'student_profile': None,
            'teacher_profile': None,
        }
        if user.role == 'student' and hasattr(user, 'student_profile'):
            user_data['student_profile'] = user.student_profile
        elif user.role == 'teacher' and hasattr(user, 'teacher_profile'):
            user_data['teacher_profile'] = user.teacher_profile
        users_data.append(user_data)
    
    context = {
        'pending_users': pending_users,
        'users_data': users_data,
    }
    return render(request, 'director/pending_users.html', context)


@login_required
@user_passes_test(lambda u: u.role == 'director')
def approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.status = 'approved'
        user.approved_by = request.user
        user.approved_at = datetime.now()
        user.is_active = True
        user.save()
        
        send_approval_email(user, request.user)
        
        Notification.objects.create(
            title='Account Approved ✅',
            message=f'Your account has been approved by Director {request.user.username}.',
            notification_type='notice',
            target_role=user.role,
            created_by=request.user,
        )
        
        if user.role == 'student' and hasattr(user, 'student_profile'):
            Notification.objects.create(
                title='Account Approved',
                message='Your student account has been approved. Welcome!',
                notification_type='notice',
                target_student=user.student_profile,
                created_by=request.user,
            )
        elif user.role == 'teacher' and hasattr(user, 'teacher_profile'):
            Notification.objects.create(
                title='Account Approved',
                message='Your teacher account has been approved.',
                notification_type='notice',
                target_teacher=user.teacher_profile,
                created_by=request.user,
            )
        
        messages.success(request, f'✅ User "{user.username}" has been approved! Email sent.')
        return redirect('/director/users/pending/')
    
    return render(request, 'director/approve_user.html', {'pending_user': user})


@login_required
@user_passes_test(lambda u: u.role == 'director')
def reject_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', '').strip()
        
        if not reason:
            messages.error(request, '❌ Please provide a reason for rejection!')
            return redirect(f'/director/users/reject/{user_id}/')
        
        if len(reason) < 5:
            messages.error(request, '❌ Rejection reason must be at least 5 characters!')
            return redirect(f'/director/users/reject/{user_id}/')
        
        user.status = 'rejected'
        user.rejection_reason = reason
        user.is_active = False
        user.save()
        
        send_rejection_email(user, reason)
        
        Notification.objects.create(
            title='Account Rejected ❌',
            message=f'Your account has been rejected. Reason: {reason}',
            notification_type='notice',
            target_role=user.role,
            created_by=request.user,
        )
        
        messages.success(request, f'✅ User "{user.username}" has been rejected! Email sent.')
        return redirect('/director/users/pending/')
    
    return render(request, 'director/reject_user.html', {'pending_user': user})


@login_required
@user_passes_test(lambda u: u.role == 'director')
def approved_users(request):
    approved_users_list = User.objects.filter(status='approved').order_by('-approved_at')
    
    paginator = Paginator(approved_users_list, 20)
    page_number = request.GET.get('page')
    approved_users = paginator.get_page(page_number)
    
    return render(request, 'director/approved_users.html', {'approved_users': approved_users})


@login_required
@user_passes_test(lambda u: u.role == 'director')
def rejected_users(request):
    rejected_users_list = User.objects.filter(status='rejected').order_by('-updated_at')
    
    paginator = Paginator(rejected_users_list, 20)
    page_number = request.GET.get('page')
    rejected_users = paginator.get_page(page_number)
    
    return render(request, 'director/rejected_users.html', {'rejected_users': rejected_users})


# ====================================================================
# PART 9: DIRECTOR - MANAGE ALL USERS (USER MANAGEMENT)
# ====================================================================

@login_required
@user_passes_test(lambda u: u.role == 'director')
def manage_all_users(request):
    """Director can view all users (students, teachers, directors)"""
    users = User.objects.all().order_by('-created_at')
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    context = {
        'users': users_page,
        'total_users': users.count(),
        'total_students': users.filter(role='student').count(),
        'total_teachers': users.filter(role='teacher').count(),
        'total_directors': users.filter(role='director').count(),
    }
    return render(request, 'director/manage_all_users.html', context)


@login_required
@user_passes_test(lambda u: u.role == 'director')
def admin_change_password(request, user_id):
    """Director can change password of any user"""
    target_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not new_password:
            messages.error(request, '❌ Password is required!')
            return redirect('admin_change_password', user_id=user_id)
        
        if len(new_password) < 6:
            messages.error(request, '❌ Password must be at least 6 characters!')
            return redirect('admin_change_password', user_id=user_id)
        
        if new_password != confirm_password:
            messages.error(request, '❌ Passwords do not match!')
            return redirect('admin_change_password', user_id=user_id)
        
        target_user.set_password(new_password)
        target_user.save()
        
        messages.success(request, f'✅ Password changed for {target_user.username}')
        
        if target_user.email:
            send_mail(
                subject='Password Changed by Administrator',
                message=f"""
                Dear {target_user.username},
                
Your password has been changed by the administrator ({request.user.username}).

New Password: {new_password}

Please login and change your password immediately.

Thank you,
Student Management System
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[target_user.email],
                fail_silently=True,
            )
        
        return redirect('/director/users/')
    
    context = {
        'target_user': target_user,
        'user_role': target_user.get_role_display(),
    }
    return render(request, 'director/admin_change_password.html', context)


@login_required
@user_passes_test(lambda u: u.role == 'director')
def admin_reset_password(request, user_id):
    """Quick reset password to default"""
    target_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        if target_user.role == 'student':
            default_password = 'student@123'
        elif target_user.role == 'teacher':
            default_password = 'teacher@123'
        else:
            default_password = 'director@123'
        
        target_user.set_password(default_password)
        target_user.save()
        
        messages.success(request, f'✅ Password reset to default for {target_user.username}')
        
        if target_user.email:
            send_mail(
                subject='Password Reset by Administrator',
                message=f"""
                Dear {target_user.username},
                
Your password has been reset by the administrator.

New Password: {default_password}

Please login and change your password.

Thank you,
Student Management System
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[target_user.email],
                fail_silently=True,
            )
        
        return redirect('/director/users/')
    
    context = {'target_user': target_user}
    return render(request, 'director/admin_reset_password.html', context)


# ====================================================================
# PART 10: DIRECTOR - STUDENT MANAGEMENT (WITH DELETE FIX)
# ====================================================================

@login_required
@user_passes_test(lambda u: u.role == 'director')
def manage_students(request):
    students_list = Student.objects.select_related('user').all().order_by('-id')
    
    paginator = Paginator(students_list, 20)
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)
    
    return render(request, 'director/manage_students.html', {'students': students})


@login_required
@user_passes_test(lambda u: u.role == 'director')
def add_student(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        student_id = request.POST.get('student_id')
        class_name = request.POST.get('class_name')
        roll_number = request.POST.get('roll_number')
        parent_name = request.POST.get('parent_name')
        parent_phone = request.POST.get('parent_phone')
        address = request.POST.get('address')
        email = request.POST.get('email', '')
        profile_pic = request.FILES.get('profile_pic')
        
        has_error = False
        
        if profile_pic:
            if profile_pic.size > 2 * 1024 * 1024:
                messages.error(request, '❌ Profile picture size must be less than 2MB!')
                has_error = True
            elif profile_pic.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/jpg']:
                messages.error(request, '❌ Only JPG, PNG, GIF images are allowed!')
                has_error = True
        
        valid, username_result = validate_username_professional(username)
        if not valid:
            messages.error(request, username_result)
            has_error = True
        
        valid, password_result = validate_password_professional(password, confirm_password)
        if not valid:
            messages.error(request, password_result)
            has_error = True
        
        full_name = f"{first_name} {last_name}" if first_name and last_name else first_name or last_name or username
        valid, name_result = validate_full_name_professional(full_name, "Full name")
        if not valid:
            messages.error(request, name_result)
            has_error = True
        else:
            name_parts = name_result.split(' ', 1)
            first_name_result = name_parts[0]
            last_name_result = name_parts[1] if len(name_parts) > 1 else ''
        
        valid, student_id_result = validate_student_id_professional(student_id)
        if not valid:
            messages.error(request, student_id_result)
            has_error = True
        
        valid, class_result = validate_class_name_professional(class_name)
        if not valid:
            messages.error(request, class_result)
            has_error = True
        
        valid, roll_result = validate_roll_number_professional(roll_number)
        if not valid:
            messages.error(request, roll_result)
            has_error = True
        
        parent_name_result = ''
        if parent_name:
            valid, parent_name_result = validate_full_name_professional(parent_name, "Parent name")
            if not valid:
                messages.error(request, parent_name_result)
                has_error = True
        
        valid, phone_result = validate_phone_professional(parent_phone, "Parent phone number")
        if not valid:
            messages.error(request, phone_result)
            has_error = True
        
        valid, address_result = validate_address_professional(address)
        if not valid:
            messages.error(request, address_result)
            has_error = True
        
        if email:
            valid, email_result = validate_email_professional(email)
            if not valid:
                messages.error(request, email_result)
                has_error = True
            elif User.objects.filter(email=email_result).exists():
                messages.error(request, '❌ This email is already registered!')
                has_error = True
        else:
            email_result = ''
        
        if not has_error:
            try:
                user = User.objects.create_user(
                    username=username_result,
                    password=password,
                    first_name=first_name_result,
                    last_name=last_name_result,
                    email=email_result,
                    role='student',
                    phone=phone_result,
                    status='approved',
                )
                
                Student.objects.create(
                    user=user,
                    student_id=student_id_result,
                    full_name=name_result,
                    class_name=class_result,
                    roll_number=roll_result,
                    parent_name=parent_name_result,
                    parent_phone=phone_result,
                    address=address_result,
                    profile_pic=profile_pic
                )
                
                send_welcome_email(user, password, 'student')
                
                messages.success(request, f'✅ Student {name_result} added successfully! Email sent.')
                return redirect('/director/students/')
                
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
    
    return render(request, 'director/add_student.html')


@login_required
@user_passes_test(lambda u: u.role == 'director')
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        class_name = request.POST.get('class_name')
        roll_number = request.POST.get('roll_number')
        parent_name = request.POST.get('parent_name')
        parent_phone = request.POST.get('parent_phone')
        address = request.POST.get('address')
        email = request.POST.get('email', '')
        
        has_error = False
        
        valid, full_name_result = validate_full_name_professional(full_name, "Full name")
        if not valid:
            messages.error(request, full_name_result)
            has_error = True
        
        valid, class_result = validate_class_name_professional(class_name)
        if not valid:
            messages.error(request, class_result)
            has_error = True
        
        valid, roll_result = validate_roll_number_professional(roll_number)
        if not valid:
            messages.error(request, roll_result)
            has_error = True
        
        parent_name_result = ''
        if parent_name:
            valid, parent_name_result = validate_full_name_professional(parent_name, "Parent name")
            if not valid:
                messages.error(request, parent_name_result)
                has_error = True
        
        valid, phone_result = validate_phone_professional(parent_phone, "Parent phone number")
        if not valid:
            messages.error(request, phone_result)
            has_error = True
        
        valid, address_result = validate_address_professional(address)
        if not valid:
            messages.error(request, address_result)
            has_error = True
        
        if email:
            valid, email_result = validate_email_professional(email)
            if not valid:
                messages.error(request, email_result)
                has_error = True
            elif User.objects.filter(email=email_result).exclude(id=student.user.id).exists():
                messages.error(request, '❌ This email is already registered!')
                has_error = True
            else:
                if student.user:
                    student.user.email = email_result
        
        if not has_error:
            student.full_name = full_name_result
            student.class_name = class_result
            student.roll_number = roll_result
            student.parent_name = parent_name_result
            student.parent_phone = phone_result
            student.address = address_result
            student.save()
            
            if student.user:
                name_parts = full_name_result.split(' ', 1)
                student.user.first_name = name_parts[0] if name_parts else ''
                student.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
                student.user.phone = phone_result
                if email:
                    student.user.email = email_result
                student.user.save()
            
            messages.success(request, f'✅ Student {full_name_result} updated successfully!')
            return redirect('/director/students/')
    
    return render(request, 'director/edit_student.html', {'student': student})


@login_required
@user_passes_test(lambda u: u.role == 'director')
def delete_student(request, student_id):
    """Delete student - FIXED: Properly handle deletion so user can be re-added"""
    student = get_object_or_404(Student, id=student_id)
    student_name = student.full_name
    student_id_value = student.student_id
    
    if request.method == 'POST':
        # Store user object before deletion
        user = student.user
        
        # First delete student profile
        student.delete()
        
        # Then delete user if exists
        if user:
            user.delete()
        
        messages.success(request, f'✅ Student "{student_name}" (ID: {student_id_value}) deleted successfully! You can now re-add them.')
        return redirect('/director/students/')
    
    return render(request, 'director/delete_student.html', {'student': student})


# ====================================================================
# PART 11: DIRECTOR - TEACHER MANAGEMENT (WITH DELETE FIX)
# ====================================================================

@login_required
@user_passes_test(lambda u: u.role == 'director')
def manage_teachers(request):
    teachers_list = Teacher.objects.select_related('user').all()
    
    paginator = Paginator(teachers_list, 20)
    page_number = request.GET.get('page')
    teachers = paginator.get_page(page_number)
    
    return render(request, 'director/manage_teachers.html', {'teachers': teachers})


@login_required
@user_passes_test(lambda u: u.role == 'director')
def add_teacher(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        teacher_id = request.POST.get('teacher_id')
        subject = request.POST.get('subject')
        qualification = request.POST.get('qualification')
        experience_years = request.POST.get('experience_years')
        phone = request.POST.get('phone')
        email = request.POST.get('email', '')
        profile_pic = request.FILES.get('profile_pic')
        
        has_error = False
        
        if profile_pic:
            if profile_pic.size > 2 * 1024 * 1024:
                messages.error(request, '❌ Profile picture size must be less than 2MB!')
                has_error = True
            elif profile_pic.content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/jpg']:
                messages.error(request, '❌ Only JPG, PNG, GIF images are allowed!')
                has_error = True
        
        valid, username_result = validate_username_professional(username)
        if not valid:
            messages.error(request, username_result)
            has_error = True
        
        valid, password_result = validate_password_professional(password, confirm_password)
        if not valid:
            messages.error(request, password_result)
            has_error = True
        
        full_name = f"{first_name} {last_name}" if first_name and last_name else first_name or last_name or username
        valid, name_result = validate_full_name_professional(full_name, "Full name")
        if not valid:
            messages.error(request, name_result)
            has_error = True
        else:
            name_parts = name_result.split(' ', 1)
            first_name_result = name_parts[0]
            last_name_result = name_parts[1] if len(name_parts) > 1 else ''
        
        valid, teacher_id_result = validate_teacher_id_professional(teacher_id)
        if not valid:
            messages.error(request, teacher_id_result)
            has_error = True
        
        valid, subject_result = validate_class_name_professional(subject)
        if not valid:
            messages.error(request, subject_result)
            has_error = True
        
        valid, qual_result = validate_qualification_professional(qualification)
        if not valid:
            messages.error(request, qual_result)
            has_error = True
        
        valid, exp_result = validate_experience_professional(experience_years)
        if not valid:
            messages.error(request, exp_result)
            has_error = True
        
        valid, phone_result = validate_phone_professional(phone, "Phone number")
        if not valid:
            messages.error(request, phone_result)
            has_error = True
        
        if email:
            valid, email_result = validate_email_professional(email)
            if not valid:
                messages.error(request, email_result)
                has_error = True
            elif User.objects.filter(email=email_result).exists():
                messages.error(request, '❌ This email is already registered!')
                has_error = True
        else:
            email_result = ''
        
        if not has_error:
            try:
                user = User.objects.create_user(
                    username=username_result,
                    password=password,
                    first_name=first_name_result,
                    last_name=last_name_result,
                    email=email_result,
                    role='teacher',
                    phone=phone_result,
                    status='approved',
                )
                
                Teacher.objects.create(
                    user=user,
                    teacher_id=teacher_id_result,
                    full_name=name_result,
                    subject=subject_result,
                    qualification=qual_result,
                    experience_years=exp_result,
                    phone=phone_result,
                    profile_pic=profile_pic
                )
                
                send_welcome_email(user, password, 'teacher')
                
                messages.success(request, f'✅ Teacher {name_result} added successfully! Email sent.')
                return redirect('/director/teachers/')
                
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
    
    return render(request, 'director/add_teacher.html')


@login_required
@user_passes_test(lambda u: u.role == 'director')
def edit_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        subject = request.POST.get('subject')
        qualification = request.POST.get('qualification')
        experience_years = request.POST.get('experience_years')
        phone = request.POST.get('phone')
        email = request.POST.get('email', '')
        
        has_error = False
        
        valid, full_name_result = validate_full_name_professional(full_name, "Full name")
        if not valid:
            messages.error(request, full_name_result)
            has_error = True
        
        valid, subject_result = validate_class_name_professional(subject)
        if not valid:
            messages.error(request, subject_result)
            has_error = True
        
        valid, qual_result = validate_qualification_professional(qualification)
        if not valid:
            messages.error(request, qual_result)
            has_error = True
        
        valid, exp_result = validate_experience_professional(experience_years)
        if not valid:
            messages.error(request, exp_result)
            has_error = True
        
        valid, phone_result = validate_phone_professional(phone, "Phone number")
        if not valid:
            messages.error(request, phone_result)
            has_error = True
        
        if email:
            valid, email_result = validate_email_professional(email)
            if not valid:
                messages.error(request, email_result)
                has_error = True
            elif User.objects.filter(email=email_result).exclude(id=teacher.user.id).exists():
                messages.error(request, '❌ This email is already registered!')
                has_error = True
            else:
                if teacher.user:
                    teacher.user.email = email_result
        
        if not has_error:
            teacher.full_name = full_name_result
            teacher.subject = subject_result
            teacher.qualification = qual_result
            teacher.experience_years = exp_result
            teacher.phone = phone_result
            teacher.save()
            
            if teacher.user:
                name_parts = full_name_result.split(' ', 1)
                teacher.user.first_name = name_parts[0] if name_parts else ''
                teacher.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
                teacher.user.phone = phone_result
                if email:
                    teacher.user.email = email_result
                teacher.user.save()
            
            messages.success(request, f'✅ Teacher {full_name_result} updated successfully!')
            return redirect('/director/teachers/')
    
    return render(request, 'director/edit_teacher.html', {'teacher': teacher})


@login_required
@user_passes_test(lambda u: u.role == 'director')
def delete_teacher(request, teacher_id):
    """Delete teacher - FIXED: Properly handle deletion so user can be re-added"""
    teacher = get_object_or_404(Teacher, id=teacher_id)
    teacher_name = teacher.full_name
    teacher_id_value = teacher.teacher_id
    user = teacher.user
    
    if request.method == 'POST':
        # Delete teacher profile first
        teacher.delete()
        
        # Delete user if exists
        if user:
            user.delete()
        
        messages.success(request, f'✅ Teacher "{teacher_name}" (ID: {teacher_id_value}) deleted successfully! You can now re-add them.')
        return redirect('/director/teachers/')
    
    return render(request, 'director/delete_teacher.html', {'teacher': teacher})


# ====================================================================
# PART 12: DIRECTOR - SUBJECT MANAGEMENT
# ====================================================================

@login_required
@user_passes_test(lambda u: u.role == 'director')
def manage_subjects(request):
    subjects_list = Subject.objects.select_related('teacher').all().order_by('subject_code')
    
    paginator = Paginator(subjects_list, 20)
    page_number = request.GET.get('page')
    subjects = paginator.get_page(page_number)
    
    teachers = Teacher.objects.all().order_by('full_name')
    
    teachers_with_subjects = []
    for teacher in teachers:
        teacher_subjects = teacher.subjects.all()
        teachers_with_subjects.append({
            'teacher': teacher,
            'subjects': teacher_subjects,
            'count': teacher_subjects.count()
        })
    
    context = {
        'subjects': subjects,
        'teachers': teachers,
        'teachers_with_subjects': teachers_with_subjects,
        'total_subjects': subjects_list.count(),
        'assigned_subjects': subjects_list.filter(teacher__isnull=False).count(),
        'unassigned_subjects': subjects_list.filter(teacher__isnull=True).count(),
    }
    return render(request, 'director/manage_subjects.html', context)


@login_required
@user_passes_test(lambda u: u.role == 'director')
def add_subject(request):
    if request.method == 'POST':
        subject_code = request.POST.get('subject_code')
        subject_name = request.POST.get('subject_name')
        teacher_id = request.POST.get('teacher')
        description = request.POST.get('description', '')
        
        has_error = False
        
        valid, code_result = validate_subject_code_professional(subject_code)
        if not valid:
            messages.error(request, code_result)
            has_error = True
        
        valid, name_result = validate_subject_name_professional(subject_name)
        if not valid:
            messages.error(request, name_result)
            has_error = True
        
        if not has_error:
            teacher = Teacher.objects.filter(id=teacher_id).first() if teacher_id and teacher_id != '' else None
            
            Subject.objects.create(
                subject_code=code_result,
                subject_name=name_result,
                teacher=teacher,
                description=description.strip() if description else ''
            )
            
            messages.success(request, f'✅ Subject "{name_result}" added successfully!')
            return redirect('/director/subjects/')
    
    teachers = Teacher.objects.all().order_by('full_name')
    return render(request, 'director/add_subject.html', {'teachers': teachers})


@login_required
@user_passes_test(lambda u: u.role == 'director')
def edit_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        subject_code = request.POST.get('subject_code')
        subject_name = request.POST.get('subject_name')
        description = request.POST.get('description', '')
        
        has_error = False
        
        if not subject_code or not subject_code.strip():
            messages.error(request, '❌ Subject code is required!')
            has_error = True
        else:
            subject_code = subject_code.strip().upper()
            if len(subject_code) < 2:
                messages.error(request, '❌ Subject code must be at least 2 characters!')
                has_error = True
            elif len(subject_code) > 10:
                messages.error(request, '❌ Subject code is too long! Maximum 10 characters.')
                has_error = True
            elif not re.match(r'^[A-Z0-9\-_]+$', subject_code):
                messages.error(request, '❌ Subject code can only contain letters, numbers, hyphens (-), and underscores (_)')
                has_error = True
            elif Subject.objects.filter(subject_code=subject_code).exclude(id=subject_id).exists():
                messages.error(request, f'❌ Subject code "{subject_code}" already exists!')
                has_error = True
        
        valid, name_result = validate_subject_name_professional(subject_name)
        if not valid:
            messages.error(request, name_result)
            has_error = True
        
        if not has_error:
            subject.subject_code = subject_code
            subject.subject_name = name_result
            subject.description = description.strip() if description else ''
            
            teacher_id = request.POST.get('teacher')
            subject.teacher = Teacher.objects.filter(id=teacher_id).first() if teacher_id and teacher_id != '' else None
            subject.save()
            
            messages.success(request, f'✅ Subject "{name_result}" updated successfully!')
            return redirect('/director/subjects/')
    
    teachers = Teacher.objects.all().order_by('full_name')
    return render(request, 'director/edit_subject.html', {'subject': subject, 'teachers': teachers})


@login_required
@user_passes_test(lambda u: u.role == 'director')
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject_name = subject.subject_name
    
    if request.method == 'POST':
        subject.delete()
        messages.success(request, f'✅ Subject "{subject_name}" deleted successfully!')
        return redirect('/director/subjects/')
    
    return render(request, 'director/delete_subject.html', {'subject': subject})


@login_required
@user_passes_test(lambda u: u.role == 'director')
def assign_teacher_to_subject(request, subject_id):
    if subject_id <= 0:
        messages.error(request, '❌ Invalid subject ID!')
        return redirect('/director/subjects/')
    
    try:
        subject = Subject.objects.get(id=subject_id)
    except Subject.DoesNotExist:
        messages.error(request, f'❌ Subject with ID {subject_id} does not exist!')
        return redirect('/director/subjects/')
    
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        if teacher_id and teacher_id != 'none':
            try:
                teacher = Teacher.objects.get(id=teacher_id)
                subject.teacher = teacher
                subject.save()
                messages.success(request, f'✅ Teacher "{teacher.full_name}" assigned to "{subject.subject_name}"')
            except Teacher.DoesNotExist:
                messages.error(request, '❌ Teacher not found!')
        elif teacher_id == 'none':
            subject.teacher = None
            subject.save()
            messages.info(request, f'ℹ️ Teacher removed from "{subject.subject_name}"')
        else:
            messages.warning(request, '⚠️ No teacher selected!')
        
        return redirect('/director/subjects/')
    
    teachers = Teacher.objects.all().order_by('full_name')
    return render(request, 'director/assign_teacher.html', {
        'subject': subject,
        'teachers': teachers
    })


# ====================================================================
# PART 13: DIRECTOR - ATTENDANCE OVERVIEW
# ====================================================================

@login_required
@user_passes_test(lambda u: u.role == 'director')
def attendance_overview(request):
    attendances_list = Attendance.objects.select_related('student', 'subject').all()
    
    paginator = Paginator(attendances_list, 50)
    page_number = request.GET.get('page')
    attendances = paginator.get_page(page_number)
    
    context = {
        'attendances': attendances,
        'total_present': attendances_list.filter(status='present').count(),
        'total_absent': attendances_list.filter(status='absent').count(),
        'total_late': attendances_list.filter(status='late').count(),
        'total_leave': attendances_list.filter(status='leave').count(),
    }
    return render(request, 'director/attendance_overview.html', context)


@login_required
@user_passes_test(lambda u: u.role == 'director')
def download_attendance_report(request):
    class_name = request.GET.get('class')
    subject_id = request.GET.get('subject')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    attendances = Attendance.objects.select_related('student', 'subject').all()
    
    if class_name:
        attendances = attendances.filter(student__class_name=class_name)
    if subject_id:
        attendances = attendances.filter(subject_id=subject_id)
    if start_date:
        attendances = attendances.filter(date__gte=start_date)
    if end_date:
        attendances = attendances.filter(date__lte=end_date)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student Name', 'Student ID', 'Class', 'Subject', 'Date', 'Session', 'Status', 'Remarks'])
    
    for att in attendances:
        writer.writerow([
            att.student.full_name,
            att.student.student_id,
            att.student.class_name,
            att.subject.subject_name,
            att.date,
            att.session,
            att.status.upper(),
            att.remarks or ''
        ])
    
    return response


# ====================================================================
# PART 14: DIRECTOR - CSV UPLOAD
# ====================================================================

@login_required
@user_passes_test(lambda u: u.role == 'director')
def upload_students_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, '❌ Please upload a CSV file!')
            return redirect('/director/students/')
        
        data = parse_csv_file(csv_file)
        if not data:
            messages.error(request, '❌ Error reading CSV file!')
            return redirect('/director/students/')
        
        success_count = 0
        error_count = 0
        
        for row in data:
            try:
                username = row.get('username', '').strip()
                student_id = row.get('student_id', '').strip()
                full_name = row.get('full_name', '').strip()
                class_name = row.get('class_name', '').strip()
                roll_number = row.get('roll_number', '').strip()
                parent_name = row.get('parent_name', '').strip()
                parent_phone = row.get('parent_phone', '').strip()
                address = row.get('address', '').strip()
                
                if not username or User.objects.filter(username=username).exists():
                    error_count += 1
                    continue
                
                valid, phone_result = validate_phone_professional(parent_phone, "Phone")
                if not valid:
                    error_count += 1
                    continue
                
                valid, name_result = validate_full_name_professional(full_name, "Full name")
                if not valid:
                    error_count += 1
                    continue
                
                if not student_id or Student.objects.filter(student_id=student_id).exists():
                    error_count += 1
                    continue
                
                user = User.objects.create_user(
                    username=username,
                    password='student@123',
                    first_name=full_name.split()[0] if full_name else username,
                    last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
                    role='student',
                    phone=phone_result,
                    status='approved',
                )
                
                Student.objects.create(
                    user=user,
                    student_id=student_id.upper(),
                    full_name=name_result,
                    class_name=class_name.title(),
                    roll_number=roll_number.upper(),
                    parent_name=capitalize_name(parent_name),
                    parent_phone=phone_result,
                    address=address
                )
                
                success_count += 1
                
            except Exception:
                error_count += 1
        
        messages.success(request, f'✅ {success_count} students uploaded successfully!')
        if error_count > 0:
            messages.warning(request, f'⚠️ {error_count} students failed to upload!')
        return redirect('/director/students/')
    
    return render(request, 'director/upload_students.html')


@login_required
@user_passes_test(lambda u: u.role == 'director')
def upload_teachers_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, '❌ Please upload a CSV file!')
            return redirect('/director/teachers/')
        
        data = parse_csv_file(csv_file)
        if not data:
            messages.error(request, '❌ Error reading CSV file!')
            return redirect('/director/teachers/')
        
        success_count = 0
        error_count = 0
        
        for row in data:
            try:
                username = row.get('username', '').strip()
                teacher_id = row.get('teacher_id', '').strip()
                full_name = row.get('full_name', '').strip()
                subject = row.get('subject', '').strip()
                qualification = row.get('qualification', '').strip()
                phone = row.get('phone', '').strip()
                
                if not username or User.objects.filter(username=username).exists():
                    error_count += 1
                    continue
                
                valid, phone_result = validate_phone_professional(phone, "Phone")
                if not valid:
                    error_count += 1
                    continue
                
                valid, name_result = validate_full_name_professional(full_name, "Full name")
                if not valid:
                    error_count += 1
                    continue
                
                if not teacher_id or Teacher.objects.filter(teacher_id=teacher_id).exists():
                    error_count += 1
                    continue
                
                user = User.objects.create_user(
                    username=username,
                    password='teacher@123',
                    first_name=full_name.split()[0] if full_name else username,
                    last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
                    role='teacher',
                    phone=phone_result,
                    status='approved',
                )
                
                Teacher.objects.create(
                    user=user,
                    teacher_id=teacher_id.upper(),
                    full_name=name_result,
                    subject=subject.title(),
                    qualification=qualification,
                    experience_years=0,
                    phone=phone_result
                )
                
                success_count += 1
                
            except Exception:
                error_count += 1
        
        messages.success(request, f'✅ {success_count} teachers uploaded successfully!')
        if error_count > 0:
            messages.warning(request, f'⚠️ {error_count} teachers failed to upload!')
        return redirect('/director/teachers/')
    
    return render(request, 'director/upload_teachers.html')


@login_required
@user_passes_test(lambda u: u.role == 'director')
def upload_subjects_csv(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, '❌ Please upload a CSV file!')
            return redirect('/director/subjects/')
        
        data = parse_csv_file(csv_file)
        if not data:
            messages.error(request, '❌ Error reading CSV file!')
            return redirect('/director/subjects/')
        
        success_count = 0
        error_count = 0
        
        for row in data:
            try:
                subject_code = row.get('subject_code', '').strip().upper()
                subject_name = row.get('subject_name', '').strip()
                teacher_id = row.get('teacher_id', '').strip()
                description = row.get('description', '').strip()
                
                if len(subject_code) < 2:
                    error_count += 1
                    continue
                if len(subject_code) > 10:
                    error_count += 1
                    continue
                if not re.match(r'^[A-Z0-9\-_]+$', subject_code):
                    error_count += 1
                    continue
                
                if Subject.objects.filter(subject_code=subject_code).exists():
                    error_count += 1
                    continue
                
                if not subject_name or len(subject_name) < 3:
                    error_count += 1
                    continue
                
                teacher = Teacher.objects.filter(teacher_id=teacher_id).first() if teacher_id else None
                
                Subject.objects.create(
                    subject_code=subject_code,
                    subject_name=subject_name.title(),
                    teacher=teacher,
                    description=description
                )
                
                success_count += 1
                
            except Exception:
                error_count += 1
        
        messages.success(request, f'✅ {success_count} subjects uploaded successfully!')
        if error_count > 0:
            messages.warning(request, f'⚠️ {error_count} subjects failed to upload!')
        return redirect('/director/subjects/')
    
    return render(request, 'director/upload_subjects.html')


# ====================================================================
# PART 15: DIRECTOR - CSV DOWNLOAD
# ====================================================================

@login_required
@user_passes_test(lambda u: u.role == 'director')
def download_students_csv(request):
    students = Student.objects.all().select_related('user')
    csv_data = generate_student_csv(students)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="all_students.csv"'
    return response


@login_required
@user_passes_test(lambda u: u.role == 'director')
def download_teachers_csv(request):
    teachers = Teacher.objects.all().select_related('user')
    csv_data = generate_teacher_csv(teachers)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="all_teachers.csv"'
    return response


@login_required
@user_passes_test(lambda u: u.role == 'director')
def download_full_attendance_csv(request):
    class_name = request.GET.get('class')
    subject_id = request.GET.get('subject')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    attendances = Attendance.objects.all().select_related('student', 'subject')
    
    if class_name:
        attendances = attendances.filter(student__class_name=class_name)
    if subject_id:
        attendances = attendances.filter(subject_id=subject_id)
    if start_date:
        attendances = attendances.filter(date__gte=start_date)
    if end_date:
        attendances = attendances.filter(date__lte=end_date)
    
    csv_data = generate_attendance_csv(attendances)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="full_attendance_report.csv"'
    return response


@login_required
@user_passes_test(lambda u: u.role == 'director')
def download_full_marks_csv(request):
    class_name = request.GET.get('class')
    subject_id = request.GET.get('subject')
    exam_type = request.GET.get('exam_type')
    
    marks = Marks.objects.all().select_related('student', 'subject')
    
    if class_name:
        marks = marks.filter(student__class_name=class_name)
    if subject_id:
        marks = marks.filter(subject_id=subject_id)
    if exam_type:
        marks = marks.filter(exam_type=exam_type)
    
    csv_data = generate_marks_csv(marks)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="full_marks_report.csv"'
    return response


# ====================================================================
# PART 16: TEACHER DASHBOARD
# ====================================================================

@login_required
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    if not hasattr(request.user, 'teacher_profile'):
        messages.error(request, '❌ Teacher profile not found!')
        return redirect('/logout/')
    
    teacher = request.user.teacher_profile
    my_subjects = Subject.objects.filter(teacher=teacher)
    all_students = Student.objects.all().order_by('class_name', 'roll_number')
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    notifications = Notification.objects.filter(
        Q(target_role='teacher') | Q(target_role='all')
    ).order_by('-created_at')[:10]
    
    context = {
        'teacher': teacher,
        'subjects': my_subjects,
        'students': all_students,
        'notifications': notifications,
        'my_subjects': my_subjects,
        'current_year': current_year,
        'current_month': current_month,
        'total_subjects': my_subjects.count(),
        'total_students': all_students.count(),
    }
    return render(request, 'teacher/dashboard.html', context)


# ====================================================================
# PART 17: TEACHER - STUDENT MANAGEMENT
# ====================================================================

@login_required
def teacher_manage_students(request):
    if request.user.role != 'teacher':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    students_list = Student.objects.select_related('user').all().order_by('roll_number')
    
    paginator = Paginator(students_list, 20)
    page_number = request.GET.get('page')
    students = paginator.get_page(page_number)
    
    return render(request, 'teacher/manage_students.html', {'students': students})


@login_required
def teacher_edit_student(request, student_id):
    if request.user.role != 'teacher':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        class_name = request.POST.get('class_name')
        roll_number = request.POST.get('roll_number')
        parent_name = request.POST.get('parent_name')
        parent_phone = request.POST.get('parent_phone')
        address = request.POST.get('address')
        
        has_error = False
        
        valid, full_name_result = validate_full_name_professional(full_name, "Full name")
        if not valid:
            messages.error(request, full_name_result)
            has_error = True
        
        if parent_name:
            valid, parent_name_result = validate_full_name_professional(parent_name, "Parent name")
            if not valid:
                messages.error(request, parent_name_result)
                has_error = True
        else:
            parent_name_result = ''
        
        valid, phone_result = validate_phone_professional(parent_phone, "Parent phone number")
        if not valid:
            messages.error(request, phone_result)
            has_error = True
        
        valid, address_result = validate_address_professional(address)
        if not valid:
            messages.error(request, address_result)
            has_error = True
        
        if not class_name:
            messages.error(request, '❌ Class/Course is required!')
            has_error = True
        if not roll_number:
            messages.error(request, '❌ Roll number is required!')
            has_error = True
        
        if not has_error:
            student.full_name = full_name_result
            student.class_name = class_name.title()
            student.roll_number = roll_number.upper()
            student.parent_name = parent_name_result
            student.parent_phone = phone_result
            student.address = address_result
            student.save()
            
            messages.success(request, f'✅ Student {student.full_name} updated successfully!')
            return redirect('/teacher/students/')
    
    return render(request, 'teacher/edit_student.html', {'student': student})


# ====================================================================
# PART 18: TEACHER - MONTHLY ATTENDANCE CALENDAR
# ====================================================================

@login_required
def monthly_attendance_calendar(request):
    """Monthly attendance calendar view with AJAX support"""
    if request.user.role != 'teacher':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    from django.template.loader import render_to_string
    
    teacher = request.user.teacher_profile
    my_subjects = Subject.objects.filter(teacher=teacher)
    
    selected_subject_id = request.GET.get('subject_id')
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    
    calendar_data = []
    subject_name = ""
    
    if selected_subject_id:
        try:
            subject = Subject.objects.get(id=selected_subject_id, teacher=teacher)
            subject_name = subject.subject_name
            
            first_day = date(year, month, 1)
            if month == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month + 1, 1)
            last_day = next_month - timedelta(days=1)
            
            students = Student.objects.all().order_by('roll_number')
            
            current_date = first_day
            while current_date <= last_day:
                day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                
                day_data = {
                    'date': current_date,
                    'day': current_date.day,
                    'month': current_date.month,
                    'year': current_date.year,
                    'day_name': day_names[current_date.weekday()],
                    'students': []
                }
                
                for student in students:
                    att_am = Attendance.objects.filter(
                        student=student, subject=subject, date=current_date, session='AM'
                    ).first()
                    
                    att_pm = Attendance.objects.filter(
                        student=student, subject=subject, date=current_date, session='PM'
                    ).first()
                    
                    day_data['students'].append({
                        'student': student,
                        'am_status': att_am.status if att_am else None,
                        'pm_status': att_pm.status if att_pm else None
                    })
                
                calendar_data.append(day_data)
                current_date += timedelta(days=1)
                
        except Subject.DoesNotExist:
            subject_name = ""
            messages.warning(request, '⚠️ Selected subject not found.')
    
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    context = {
        'teacher': teacher,
        'my_subjects': my_subjects,
        'calendar_data': calendar_data,
        'selected_subject_id': selected_subject_id,
        'current_year': year,
        'current_month': month,
        'subject_name': subject_name,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'month_name': date(year, month, 1).strftime('%B %Y'),
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('teacher/monthly_calendar_partial.html', context, request=request)
        return JsonResponse({'success': True, 'calendar_html': html})
    
    return render(request, 'teacher/monthly_attendance.html', context)


@login_required
@csrf_exempt
def update_monthly_attendance(request):
    """Update monthly attendance via AJAX"""
    if request.user.role != 'teacher':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    
    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        subject_id = data.get('subject_id')
        date_str = data.get('date')
        session_period = data.get('session')
        
        teacher = request.user.teacher_profile
        
        try:
            subject = Subject.objects.get(id=subject_id, teacher=teacher)
        except Subject.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Subject not found'}, status=404)
        
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)
        
        attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        attendance, created = Attendance.objects.get_or_create(
            student=student,
            subject=subject,
            date=attendance_date,
            session=session_period,
            defaults={'status': 'present', 'marked_by': teacher, 'remarks': ''}
        )
        
        current_status = attendance.status
        
        if current_status == 'present':
            new_status = 'absent'
        elif current_status == 'absent':
            new_status = 'late'
        elif current_status == 'late':
            new_status = 'leave'
        else:
            new_status = 'present'
        
        attendance.status = new_status
        attendance.marked_by = teacher
        attendance.save()
        
        status_display = {'present': 'P', 'absent': 'A', 'late': 'L', 'leave': 'LV'}
        status_color = {'present': 'present', 'absent': 'absent', 'late': 'late', 'leave': 'leave'}
        
        return JsonResponse({
            'success': True,
            'new_status': new_status,
            'new_status_display': status_display.get(new_status, '—'),
            'status_color': status_color.get(new_status, 'default')
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ====================================================================
# PART 19: TEACHER - MARKS MANAGEMENT
# ====================================================================

@login_required
def teacher_manage_marks(request):
    if request.user.role != 'teacher':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    teacher = request.user.teacher_profile
    my_subjects = Subject.objects.filter(teacher=teacher)
    students = Student.objects.all().order_by('full_name')
    marks_list = Marks.objects.filter(subject__teacher=teacher).select_related('student', 'subject')
    
    paginator = Paginator(marks_list, 20)
    page_number = request.GET.get('page')
    marks = paginator.get_page(page_number)
    
    context = {
        'marks': marks,
        'my_subjects': my_subjects,
        'students': students,
        'exam_types': Marks.EXAM_TYPES,
    }
    return render(request, 'teacher/manage_marks.html', context)


@login_required
def add_marks(request):
    if request.user.role != 'teacher':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        subject_id = request.POST.get('subject_id')
        exam_type = request.POST.get('exam_type')
        marks_obtained = request.POST.get('marks_obtained')
        total_marks = request.POST.get('total_marks', 100)
        teacher = request.user.teacher_profile
        
        try:
            marks_obtained = float(marks_obtained)
            total_marks = float(total_marks)
            if marks_obtained < 0:
                messages.error(request, '❌ Marks cannot be negative!')
                return redirect('/teacher/manage-marks/')
            if marks_obtained > total_marks:
                messages.error(request, f'❌ Marks cannot exceed {total_marks}!')
                return redirect('/teacher/manage-marks/')
            if total_marks <= 0:
                messages.error(request, '❌ Total marks must be greater than 0!')
                return redirect('/teacher/manage-marks/')
        except ValueError:
            messages.error(request, '❌ Please enter valid numbers for marks!')
            return redirect('/teacher/manage-marks/')
        
        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id, teacher=teacher)
        
        marks, created = Marks.objects.get_or_create(
            student=student, subject=subject, exam_type=exam_type,
            defaults={'marks_obtained': marks_obtained, 'total_marks': total_marks}
        )
        
        if not created:
            marks.marks_obtained = marks_obtained
            marks.total_marks = total_marks
            marks.save()
            messages.success(request, f'✅ Marks updated for {student.full_name}!')
        else:
            messages.success(request, f'✅ Marks added for {student.full_name}!')
        
        return redirect('/teacher/manage-marks/')
    
    return redirect('/teacher/manage-marks/')


@login_required
def edit_marks(request, marks_id):
    if request.user.role != 'teacher':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    marks = get_object_or_404(Marks, id=marks_id)
    
    if marks.subject.teacher != request.user.teacher_profile:
        messages.error(request, '❌ You are not authorized!')
        return redirect('/teacher/manage-marks/')
    
    if request.method == 'POST':
        marks_obtained = request.POST.get('marks_obtained')
        total_marks = request.POST.get('total_marks')
        
        try:
            marks_obtained = float(marks_obtained)
            total_marks = float(total_marks)
            if marks_obtained < 0:
                messages.error(request, '❌ Marks cannot be negative!')
                return redirect(f'/teacher/edit-marks/{marks_id}/')
            if marks_obtained > total_marks:
                messages.error(request, f'❌ Marks cannot exceed {total_marks}!')
                return redirect(f'/teacher/edit-marks/{marks_id}/')
        except ValueError:
            messages.error(request, '❌ Please enter valid numbers!')
            return redirect(f'/teacher/edit-marks/{marks_id}/')
        
        marks.marks_obtained = marks_obtained
        marks.total_marks = total_marks
        marks.save()
        messages.success(request, '✅ Marks updated successfully!')
        return redirect('/teacher/manage-marks/')
    
    return render(request, 'teacher/edit_marks.html', {'marks': marks})


@login_required
def delete_marks(request, marks_id):
    if request.user.role != 'teacher':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    marks = get_object_or_404(Marks, id=marks_id)
    
    if marks.subject.teacher != request.user.teacher_profile:
        messages.error(request, '❌ You are not authorized!')
        return redirect('/teacher/manage-marks/')
    
    if request.method == 'POST':
        marks.delete()
        messages.success(request, '✅ Marks deleted successfully!')
        return redirect('/teacher/manage-marks/')
    
    return render(request, 'teacher/delete_marks.html', {'marks': marks})


@login_required
def student_marks_detail(request, student_id):
    if request.user.role not in ['teacher', 'director']:
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    student = get_object_or_404(Student, id=student_id)
    marks = Marks.objects.filter(student=student).select_related('subject')
    
    marks_by_subject = {}
    subject_percentages = {}
    
    for mark in marks:
        if mark.subject not in marks_by_subject:
            marks_by_subject[mark.subject] = []
            subject_percentages[mark.subject] = {
                'total_obtained': 0, 'total_max': 0, 'percentage': 0,
                'count': 0, 'grade': 'F'
            }
        
        marks_by_subject[mark.subject].append(mark)
        subject_percentages[mark.subject]['total_obtained'] += mark.marks_obtained
        subject_percentages[mark.subject]['total_max'] += mark.total_marks
        subject_percentages[mark.subject]['count'] += 1
    
    for subject, data in subject_percentages.items():
        if data['total_max'] > 0:
            data['percentage'] = (data['total_obtained'] / data['total_max'] * 100)
            if data['percentage'] >= 90:
                data['grade'] = 'A+'
            elif data['percentage'] >= 80:
                data['grade'] = 'A'
            elif data['percentage'] >= 70:
                data['grade'] = 'B+'
            elif data['percentage'] >= 60:
                data['grade'] = 'B'
            elif data['percentage'] >= 50:
                data['grade'] = 'C'
            elif data['percentage'] >= 40:
                data['grade'] = 'D'
            else:
                data['grade'] = 'F'
    
    total_obtained = sum(data['total_obtained'] for data in subject_percentages.values())
    total_max = sum(data['total_max'] for data in subject_percentages.values())
    overall_percentage = (total_obtained / total_max * 100) if total_max > 0 else 0
    
    if overall_percentage >= 90:
        overall_grade = 'A+ 🌟'
    elif overall_percentage >= 80:
        overall_grade = 'A'
    elif overall_percentage >= 70:
        overall_grade = 'B+'
    elif overall_percentage >= 60:
        overall_grade = 'B'
    elif overall_percentage >= 50:
        overall_grade = 'C'
    elif overall_percentage >= 40:
        overall_grade = 'D'
    else:
        overall_grade = 'F ❌'
    
    context = {
        'student': student,
        'marks_by_subject': marks_by_subject,
        'subject_percentages': subject_percentages,
        'total_marks_obtained': total_obtained,
        'total_max_marks': total_max,
        'overall_percentage': overall_percentage,
        'overall_marks_grade': overall_grade,
    }
    return render(request, 'teacher/student_marks_detail.html', context)


# ====================================================================
# PART 20: TEACHER - AJAX AND CSV HELPER FUNCTIONS
# ====================================================================

@login_required
def get_students_by_subject(request):
    if request.user.role != 'teacher':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    subject_id = request.GET.get('subject_id')
    
    try:
        teacher = request.user.teacher_profile
        subject = get_object_or_404(Subject, id=subject_id, teacher=teacher)
        students = Student.objects.all().order_by('full_name')
        
        students_data = []
        for student in students:
            students_data.append({
                'id': student.id,
                'student_id': student.student_id,
                'full_name': student.full_name,
                'class_name': student.class_name,
                'roll_number': student.roll_number,
            })
        
        return JsonResponse({'success': True, 'students': students_data})
        
    except Subject.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Subject not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def get_student_attendance(request, student_id):
    """Get attendance for a specific student (AJAX)"""
    if request.user.role != 'teacher':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    try:
        student = get_object_or_404(Student, id=student_id)
        attendances = Attendance.objects.filter(student=student).select_related('subject')
        
        attendance_data = []
        for att in attendances:
            attendance_data.append({
                'date': att.date.strftime('%Y-%m-%d'),
                'subject': att.subject.subject_name,
                'session': att.session,
                'status': att.status,
                'remarks': att.remarks or ''
            })
        
        return JsonResponse({'success': True, 'attendance': attendance_data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def download_marks_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="marks_sample.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['student_id', 'exam_type', 'marks_obtained', 'total_marks'])
    writer.writerow(['STU00001', 'mid_term', '85', '100'])
    writer.writerow(['STU00001', 'assignment', '45', '50'])
    writer.writerow(['STU00002', 'final_term', '78', '100'])
    writer.writerow(['STU00003', 'quiz', '18', '25'])
    writer.writerow(['STU00004', 'practical', '42', '50'])
    
    return response


# ====================================================================
# PART 21: TEACHER - CSV UPLOAD/DOWNLOAD
# ====================================================================

@login_required
def teacher_upload_marks_csv(request):
    if request.user.role != 'teacher':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    teacher = request.user.teacher_profile
    my_subjects = Subject.objects.filter(teacher=teacher)
    
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        subject_id = request.POST.get('subject_id')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, '❌ Please upload a CSV file!')
            return redirect('/teacher/manage-marks/')
        
        subject = get_object_or_404(Subject, id=subject_id, teacher=teacher)
        data = parse_csv_file(csv_file)
        
        if not data:
            messages.error(request, '❌ Error reading CSV file!')
            return redirect('/teacher/manage-marks/')
        
        success_count = 0
        error_count = 0
        
        for row in data:
            try:
                student_id = row.get('student_id', '').strip()
                exam_type = row.get('exam_type', '').strip()
                marks_obtained = float(row.get('marks_obtained', 0))
                total_marks = float(row.get('total_marks', 100))
                
                student = Student.objects.filter(student_id=student_id).first()
                if not student:
                    error_count += 1
                    continue
                
                if exam_type not in dict(Marks.EXAM_TYPES):
                    error_count += 1
                    continue
                
                if marks_obtained < 0 or marks_obtained > total_marks:
                    error_count += 1
                    continue
                
                marks, created = Marks.objects.get_or_create(
                    student=student, subject=subject, exam_type=exam_type,
                    defaults={'marks_obtained': marks_obtained, 'total_marks': total_marks}
                )
                
                if not created:
                    marks.marks_obtained = marks_obtained
                    marks.total_marks = total_marks
                    marks.save()
                
                success_count += 1
                
            except Exception:
                error_count += 1
        
        messages.success(request, f'✅ {success_count} marks uploaded successfully!')
        if error_count > 0:
            messages.warning(request, f'⚠️ {error_count} records failed to upload!')
        return redirect('/teacher/manage-marks/')
    
    context = {
        'subjects': my_subjects,
        'exam_types': Marks.EXAM_TYPES,
    }
    return render(request, 'teacher/upload_marks.html', context)


@login_required
def teacher_upload_attendance_csv(request):
    if request.user.role != 'teacher':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    try:
        teacher = request.user.teacher_profile
    except Teacher.DoesNotExist:
        messages.error(request, '❌ Teacher profile not found!')
        return redirect('/dashboard/')
    
    my_subjects = Subject.objects.filter(teacher=teacher)
    
    recent_attendances = []
    recent_attendances_qs = Attendance.objects.filter(
        subject__in=my_subjects
    ).select_related('student', 'subject').order_by('-date', '-id')[:50]
    
    attendance_summary = {}
    for att in recent_attendances_qs:
        key = f"{att.date}_{att.subject.id}"
        if key not in attendance_summary:
            attendance_summary[key] = {
                'id': att.id,
                'date': att.date,
                'subject': att.subject,
                'present_count': 0,
                'absent_count': 0,
                'late_count': 0,
                'leave_count': 0,
                'total_students': 0
            }
        if att.status == 'present':
            attendance_summary[key]['present_count'] += 1
        elif att.status == 'absent':
            attendance_summary[key]['absent_count'] += 1
        elif att.status == 'late':
            attendance_summary[key]['late_count'] += 1
        elif att.status == 'leave':
            attendance_summary[key]['leave_count'] += 1
        attendance_summary[key]['total_students'] += 1
    
    for key, summary in attendance_summary.items():
        total = summary['total_students']
        if total > 0:
            present = summary['present_count']
            summary['percentage'] = round((present / total) * 100, 1)
        else:
            summary['percentage'] = 0
        recent_attendances.append(summary)
    
    recent_attendances.sort(key=lambda x: x['date'], reverse=True)
    
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        subject_id = request.POST.get('subject')
        default_session = request.POST.get('session', 'AM')
        default_date_str = request.POST.get('attendance_date', '')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, '❌ Please upload a valid CSV file!')
            return redirect('/teacher/upload-attendance-csv/')
        
        if not subject_id:
            messages.error(request, '❌ Please select a subject!')
            return redirect('/teacher/upload-attendance-csv/')
        
        try:
            subject = Subject.objects.get(id=subject_id, teacher=teacher)
        except Subject.DoesNotExist:
            messages.error(request, '❌ Invalid subject selected!')
            return redirect('/teacher/upload-attendance-csv/')
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            csv_reader = csv.DictReader(io_string)
            
            headers = csv_reader.fieldnames
            if not headers:
                messages.error(request, '❌ CSV file is empty or has no headers!')
                return redirect('/teacher/upload-attendance-csv/')
            
            required_columns = ['roll_number', 'status']
            missing_columns = [col for col in required_columns if col not in headers]
            if missing_columns:
                messages.error(request, f'❌ Missing required columns: {", ".join(missing_columns)}')
                return redirect('/teacher/upload-attendance-csv/')
            
            success_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_reader, start=2):
                try:
                    roll_number = row.get('roll_number', '').strip()
                    status = row.get('status', '').strip().lower()
                    date_str = row.get('date', '').strip()
                    session = row.get('session', default_session).strip().upper()
                    remarks = row.get('remarks', '').strip()
                    
                    if not roll_number:
                        errors.append(f"Row {row_num}: Roll number is empty")
                        error_count += 1
                        continue
                    
                    try:
                        student = Student.objects.get(roll_number=roll_number)
                    except Student.DoesNotExist:
                        errors.append(f"Row {row_num}: Student with roll number '{roll_number}' not found")
                        error_count += 1
                        continue
                    
                    status_map = {
                        'present': 'present', 'absent': 'absent', 'late': 'late', 'leave': 'leave',
                        'p': 'present', 'a': 'absent', 'l': 'late', 'lv': 'leave'
                    }
                    
                    if status not in status_map:
                        errors.append(f"Row {row_num}: Invalid status '{status}'. Use: present, absent, late, leave")
                        error_count += 1
                        continue
                    
                    final_status = status_map[status]
                    
                    if date_str:
                        try:
                            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid date format '{date_str}'. Use YYYY-MM-DD")
                            error_count += 1
                            continue
                    elif default_date_str:
                        try:
                            attendance_date = datetime.strptime(default_date_str, '%Y-%m-%d').date()
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid default date format")
                            error_count += 1
                            continue
                    else:
                        attendance_date = date.today()
                    
                    if session not in ['AM', 'PM']:
                        session = 'AM'
                    
                    attendance, created = Attendance.objects.get_or_create(
                        student=student,
                        subject=subject,
                        date=attendance_date,
                        session=session,
                        defaults={
                            'status': final_status,
                            'remarks': remarks,
                            'marked_by': teacher
                        }
                    )
                    
                    if not created:
                        attendance.status = final_status
                        attendance.remarks = remarks
                        attendance.marked_by = teacher
                        attendance.save()
                    
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    error_count += 1
            
            if success_count > 0:
                messages.success(request, f'✅ {success_count} attendance records uploaded successfully for "{subject.subject_name}"!')
            
            if error_count > 0:
                messages.warning(request, f'⚠️ {error_count} records failed to upload.')
                for err in errors[:5]:
                    messages.warning(request, f'  • {err}')
            
            return redirect('/teacher/upload-attendance-csv/')
            
        except Exception as e:
            messages.error(request, f'❌ Error reading CSV file: {str(e)}')
            return redirect('/teacher/upload-attendance-csv/')
    
    context = {
        'teacher': teacher,
        'subjects': my_subjects,
        'recent_attendances': recent_attendances,
        'total_subjects': my_subjects.count(),
    }
    return render(request, 'teacher/upload_attendance.html', context)


@login_required
def download_attendance_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_sample.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['roll_number', 'status', 'date', 'session', 'remarks'])
    writer.writerow(['2024001', 'present', '2025-05-06', 'AM', ''])
    writer.writerow(['2024002', 'absent', '2025-05-06', 'AM', 'Sick leave'])
    writer.writerow(['2024003', 'late', '2025-05-06', 'PM', 'Traffic jam'])
    writer.writerow(['2024004', 'present', '2025-05-06', 'AM', ''])
    writer.writerow(['2024005', 'leave', '2025-05-06', 'PM', 'Family function'])
    
    return response


@login_required
def download_class_students_csv(request):
    if request.user.role != 'teacher':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    students = Student.objects.all().order_by('roll_number')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="class_students_list.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['roll_number', 'student_id', 'full_name', 'class_name', 'parent_phone'])
    
    for student in students:
        writer.writerow([
            student.roll_number,
            student.student_id,
            student.full_name,
            student.class_name,
            student.parent_phone or ''
        ])
    
    return response


@login_required
def teacher_attendance_details(request, attendance_id):
    if request.user.role != 'teacher':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    try:
        teacher = request.user.teacher_profile
        attendance = get_object_or_404(Attendance, id=attendance_id)
        
        if attendance.subject.teacher != teacher:
            messages.error(request, '❌ You are not authorized to view this attendance!')
            return redirect('/teacher/')
        
        context = {
            'attendance': attendance,
            'student': attendance.student,
            'subject': attendance.subject,
            'teacher': teacher,
        }
        return render(request, 'teacher/attendance_details.html', context)
        
    except Attendance.DoesNotExist:
        messages.error(request, '❌ Attendance record not found!')
        return redirect('/teacher/')
    except Exception as e:
        messages.error(request, f'❌ Error: {str(e)}')
        return redirect('/teacher/')


# ====================================================================
# PART 22: STUDENT DASHBOARD
# ====================================================================

@login_required
def student_dashboard(request):
    if request.user.role != 'student':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, '❌ Student profile not found!')
        return redirect('/logout/')
    
    student = request.user.student_profile
    
    attendances = Attendance.objects.filter(student=student)
    total_classes = attendances.count()
    total_present = attendances.filter(status='present').count()
    total_absent = attendances.filter(status='absent').count()
    total_late = attendances.filter(status='late').count()
    total_leave = attendances.filter(status='leave').count()
    
    attendance_percentage = (total_present / total_classes * 100) if total_classes > 0 else 0
    
    marks = Marks.objects.filter(student=student).select_related('subject')
    total_obtained = sum(m.marks_obtained for m in marks)
    total_max = sum(m.total_marks for m in marks)
    overall_percentage = (total_obtained / total_max * 100) if total_max > 0 else 0
    
    marks_by_subject = {}
    subject_percentages = {}
    
    for mark in marks:
        if mark.subject not in marks_by_subject:
            marks_by_subject[mark.subject] = []
            subject_percentages[mark.subject] = {'total_obtained': 0, 'total_max': 0, 'percentage': 0}
        
        marks_by_subject[mark.subject].append(mark)
        subject_percentages[mark.subject]['total_obtained'] += mark.marks_obtained
        subject_percentages[mark.subject]['total_max'] += mark.total_marks
    
    for subject, data in subject_percentages.items():
        if data['total_max'] > 0:
            data['percentage'] = (data['total_obtained'] / data['total_max'] * 100)
    
    subjects_enrolled = len(marks_by_subject.keys())
    
    notifications = Notification.objects.filter(
        Q(target_role='student') | Q(target_role='all')
    ).order_by('-created_at')[:10]
    
    def get_grade(percentage):
        if percentage >= 90: return 'A+'
        elif percentage >= 80: return 'A'
        elif percentage >= 70: return 'B+'
        elif percentage >= 60: return 'B'
        elif percentage >= 50: return 'C'
        elif percentage >= 40: return 'D'
        else: return 'F'
    
    context = {
        'student': student,
        'attendance_percentage': round(attendance_percentage, 1),
        'total_present': total_present,
        'total_absent': total_absent,
        'total_late': total_late,
        'total_leave': total_leave,
        'total_classes': total_classes,
        'total_marks_obtained': round(total_obtained, 1),
        'total_max_marks': total_max,
        'overall_percentage': round(overall_percentage, 1),
        'overall_grade': get_grade(overall_percentage),
        'marks': marks,
        'marks_by_subject': marks_by_subject,
        'subject_percentages': subject_percentages,
        'subjects_enrolled': subjects_enrolled,
        'notifications': notifications,
    }
    return render(request, 'student/dashboard.html', context)


@login_required
def student_attendance(request):
    if request.user.role != 'student':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    student = request.user.student_profile
    attendances = Attendance.objects.filter(student=student).select_related('subject', 'marked_by').order_by('-date')
    
    total_classes = attendances.count()
    total_present = attendances.filter(status='present').count()
    total_absent = attendances.filter(status='absent').count()
    total_late = attendances.filter(status='late').count()
    total_leave = attendances.filter(status='leave').count()
    attendance_percentage = (total_present / total_classes * 100) if total_classes > 0 else 0
    
    context = {
        'student': student,
        'attendances': attendances,
        'total_classes': total_classes,
        'total_present': total_present,
        'total_absent': total_absent,
        'total_late': total_late,
        'total_leave': total_leave,
        'attendance_percentage': attendance_percentage,
    }
    return render(request, 'student/attendance.html', context)


@login_required
def student_marks(request):
    if request.user.role != 'student':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    student = request.user.student_profile
    marks = Marks.objects.filter(student=student).select_related('subject')
    
    total_obtained = sum(m.marks_obtained for m in marks)
    total_max = sum(m.total_marks for m in marks)
    overall_percentage = (total_obtained / total_max * 100) if total_max > 0 else 0
    
    def get_grade(percentage):
        if percentage >= 90: return 'A+'
        elif percentage >= 80: return 'A'
        elif percentage >= 70: return 'B+'
        elif percentage >= 60: return 'B'
        elif percentage >= 50: return 'C'
        elif percentage >= 40: return 'D'
        else: return 'F'
    
    context = {
        'student': student,
        'marks': marks,
        'total_marks_obtained': total_obtained,
        'total_max_marks': total_max,
        'overall_percentage': round(overall_percentage, 1),
        'overall_grade': get_grade(overall_percentage),
    }
    return render(request, 'student/marks.html', context)


# ====================================================================
# PART 23: STUDENT - MONTHLY ATTENDANCE
# ====================================================================

@login_required
def student_monthly_attendance(request):
    """Student monthly attendance calendar view"""
    if request.user.role != 'student':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, '❌ Student profile not found!')
        return redirect('/logout/')
    
    student = request.user.student_profile
    
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    
    first_day = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    last_day = next_month - timedelta(days=1)
    
    attendances = Attendance.objects.filter(student=student)
    
    calendar_data = []
    current_date = first_day
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    while current_date <= last_day:
        attendance_am = attendances.filter(date=current_date, session='AM').first()
        attendance_pm = attendances.filter(date=current_date, session='PM').first()
        
        am_status = attendance_am.status if attendance_am else None
        pm_status = attendance_pm.status if attendance_pm else None
        
        status_class = 'absent'
        if am_status == 'present' or pm_status == 'present':
            status_class = 'present'
        elif am_status == 'late' or pm_status == 'late':
            status_class = 'late'
        elif am_status == 'leave' or pm_status == 'leave':
            status_class = 'leave'
        
        status_display = {
            'present': 'P', 'absent': 'A', 'late': 'L', 'leave': 'LV'
        }
        
        calendar_data.append({
            'date': current_date,
            'day': current_date.day,
            'month': current_date.month,
            'year': current_date.year,
            'day_name': day_names[current_date.weekday()],
            'am_status': status_display.get(am_status, '—') if am_status else '—',
            'pm_status': status_display.get(pm_status, '—') if pm_status else '—',
            'am_status_raw': am_status,
            'pm_status_raw': pm_status,
            'status_class': status_class,
            'is_weekend': current_date.weekday() >= 5,
        })
        current_date += timedelta(days=1)
    
    total_days = len(calendar_data)
    present_count = sum(1 for d in calendar_data if d['status_class'] == 'present')
    absent_count = sum(1 for d in calendar_data if d['status_class'] == 'absent')
    late_count = sum(1 for d in calendar_data if d['status_class'] == 'late')
    leave_count = sum(1 for d in calendar_data if d['status_class'] == 'leave')
    
    attendance_percentage = (present_count / total_days * 100) if total_days > 0 else 0
    
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    context = {
        'student': student,
        'calendar_data': calendar_data,
        'current_year': year,
        'current_month': month,
        'month_name': date(year, month, 1).strftime('%B %Y'),
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'total_days': total_days,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'leave_count': leave_count,
        'attendance_percentage': round(attendance_percentage, 1),
    }
    
    return render(request, 'student/monthly_attendance.html', context)


@login_required
def student_monthly_attendance_data(request):
    """AJAX endpoint for student monthly attendance data"""
    if request.user.role != 'student':
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'success': False, 'error': 'Student profile not found'}, status=404)
    
    student = request.user.student_profile
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    
    first_day = date(year, month, 1)
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    last_day = next_month - timedelta(days=1)
    
    attendances = Attendance.objects.filter(student=student)
    
    calendar_data = []
    current_date = first_day
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    while current_date <= last_day:
        attendance_am = attendances.filter(date=current_date, session='AM').first()
        attendance_pm = attendances.filter(date=current_date, session='PM').first()
        
        am_status = attendance_am.status if attendance_am else None
        pm_status = attendance_pm.status if attendance_pm else None
        
        status_display = {
            'present': 'P', 'absent': 'A', 'late': 'L', 'leave': 'LV'
        }
        
        calendar_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'day': current_date.day,
            'day_name': day_names[current_date.weekday()],
            'am_status': status_display.get(am_status, '—') if am_status else '—',
            'pm_status': status_display.get(pm_status, '—') if pm_status else '—',
        })
        current_date += timedelta(days=1)
    
    return JsonResponse({
        'success': True,
        'calendar_data': calendar_data,
        'month_name': date(year, month, 1).strftime('%B %Y'),
    })


# ====================================================================
# PART 24: STUDENT - CSV DOWNLOAD
# ====================================================================

@login_required
def student_download_attendance_csv(request):
    if request.user.role != 'student':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    student = request.user.student_profile
    attendances = Attendance.objects.filter(student=student).select_related('subject')
    csv_data = generate_attendance_csv(attendances)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="my_attendance_{student.student_id}.csv"'
    return response


@login_required
def student_download_marks_csv(request):
    if request.user.role != 'student':
        messages.error(request, '❌ Access denied.')
        return redirect('/dashboard/')
    
    student = request.user.student_profile
    marks = Marks.objects.filter(student=student).select_related('subject')
    csv_data = generate_marks_csv(marks)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="my_marks_{student.student_id}.csv"'
    return response


# ====================================================================
# PART 25: ADDITIONAL FUNCTIONS
# ====================================================================

@login_required
def delete_account(request):
    """Delete user account permanently"""
    if request.method == 'POST':
        password = request.POST.get('password')
        user = request.user
        
        if not user.check_password(password):
            messages.error(request, '❌ Incorrect password!')
            return redirect('/profile/delete/')
        
        username = user.username
        user.delete()
        
        messages.success(request, f'✅ Account "{username}" has been deleted permanently.')
        return redirect('/login/')
    
    return render(request, 'accounts/delete_account.html')


@login_required
def change_password(request):
    """Change password for logged in user"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, '❌ Current password is incorrect!')
            return redirect('/password-change/')
        
        valid, msg = validate_password_professional(new_password, confirm_password)
        if not valid:
            messages.error(request, msg)
            return redirect('/password-change/')
        
        request.user.set_password(new_password)
        request.user.save()
        
        update_session_auth_hash(request, request.user)
        
        messages.success(request, '✅ Password changed successfully!')
        return redirect('/profile/')
    
    return render(request, 'accounts/change_password.html')


def get_csrf_token(request):
    """Return CSRF token for AJAX requests"""
    return JsonResponse({'csrfToken': get_token(request)})


def check_username_availability(request):
    """Check if username is available (for AJAX)"""
    username = request.GET.get('username', '').strip().lower()
    
    if not username:
        return JsonResponse({'available': False, 'error': 'Username required'})
    
    if len(username) < 3:
        return JsonResponse({'available': False, 'error': 'Username must be at least 3 characters'})
    
    if User.objects.filter(username=username).exists():
        return JsonResponse({'available': False, 'error': 'Username already taken'})
    
    return JsonResponse({'available': True, 'message': 'Username available'})


@login_required
def resend_verification_email(request):
    """Resend verification email for pending users"""
    user = request.user
    
    if user.status != 'pending':
        messages.error(request, '❌ Your account is not pending verification!')
        return redirect('/dashboard/')
    
    subject = "Complete Your Registration - Student Management System"
    message = f"""
    Dear {user.username},
    
    Your account registration is pending approval.
    
    📋 Details:
    Username: {user.username}
    Role: {user.role}
    
    Please contact the administrator for approval.
    
    Thank you,
    Student Management System
    """
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email] if user.email else [],
        fail_silently=True,
    )
    
    messages.success(request, '✅ Verification request resent! Admin will review your account.')
    return redirect('/dashboard/')


def health_check(request):
    """Health check endpoint for monitoring"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected',
        'users_count': User.objects.count(),
    })


def custom_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def custom_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)


# Error handlers
handler403 = custom_403
handler404 = custom_404
handler500 = custom_500