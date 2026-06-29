# users/admin.py

from django.contrib import admin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
import csv
import io
from .models import Student, Teacher


# ============================================================
# CSV EXPORT FUNCTIONS
# ============================================================

def export_students_csv(modeladmin, request, queryset):
    """Export selected students to CSV file"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="students_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student ID', 'Full Name', 'Class', 'Roll Number', 'Parent Name', 'Parent Phone', 'Address', 'Username', 'Created Date'])
    
    for student in queryset:
        writer.writerow([
            student.student_id,
            student.full_name,
            student.class_name,
            student.roll_number,
            student.parent_name,
            student.parent_phone,
            student.address,
            student.user.username if student.user else '',
            student.created_at.strftime('%Y-%m-%d') if student.created_at else ''
        ])
    
    return response
export_students_csv.short_description = "📥 Download Selected Students as CSV"


def export_teachers_csv(modeladmin, request, queryset):
    """Export selected teachers to CSV file"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="teachers_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Teacher ID', 'Full Name', 'Subject', 'Qualification', 'Experience Years', 'Phone', 'Username', 'Created Date'])
    
    for teacher in queryset:
        writer.writerow([
            teacher.teacher_id,
            teacher.full_name,
            teacher.subject,
            teacher.qualification,
            teacher.experience_years,
            teacher.phone,
            teacher.user.username if teacher.user else '',
            teacher.created_at.strftime('%Y-%m-%d') if teacher.created_at else ''
        ])
    
    return response
export_teachers_csv.short_description = "📥 Download Selected Teachers as CSV"


# ============================================================
# STUDENT ADMIN WITH CSV IMPORT
# ============================================================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'full_name', 'class_name', 'roll_number', 'parent_phone', 'created_at')
    list_filter = ('class_name', 'created_at')
    search_fields = ('student_id', 'full_name', 'parent_name', 'parent_phone', 'roll_number')
    list_per_page = 25
    readonly_fields = ('created_at', 'updated_at')
    actions = [export_students_csv]
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.import_csv, name='import_students_csv'),
        ]
        return custom_urls + urls
    
    def import_csv(self, request):
        """Import students from CSV file"""
        from accounts.models import User  # ✅ Local import to avoid circular import
        
        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')
            
            if not csv_file:
                messages.error(request, '❌ Please select a CSV file.')
                return HttpResponseRedirect(request.path_info)
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, '❌ Please upload a CSV file only.')
                return HttpResponseRedirect(request.path_info)
            
            try:
                data = csv_file.read().decode('utf-8')
                io_string = io.StringIO(data)
                reader = csv.DictReader(io_string)
                
                success_count = 0
                error_count = 0
                error_messages = []
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        username = row.get('username', '').strip()
                        student_id = row.get('student_id', '').strip()
                        full_name = row.get('full_name', '').strip()
                        class_name = row.get('class_name', '').strip()
                        roll_number = row.get('roll_number', '').strip()
                        parent_name = row.get('parent_name', '').strip()
                        parent_phone = row.get('parent_phone', '').strip()
                        address = row.get('address', '').strip()
                        
                        if not username:
                            error_count += 1
                            error_messages.append(f"Row {row_num}: Username is required")
                            continue
                        
                        if User.objects.filter(username=username).exists():
                            error_count += 1
                            error_messages.append(f"Row {row_num}: Username '{username}' already exists")
                            continue
                        
                        if Student.objects.filter(student_id=student_id).exists():
                            error_count += 1
                            error_messages.append(f"Row {row_num}: Student ID '{student_id}' already exists")
                            continue
                        
                        # Create User
                        user = User.objects.create_user(
                            username=username,
                            password='student@123',
                            first_name=full_name.split()[0] if full_name else username,
                            last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
                            role='student',
                            phone=parent_phone,
                            status='approved',
                        )
                        
                        # Create Student
                        Student.objects.create(
                            user=user,
                            student_id=student_id.upper(),
                            full_name=full_name.title(),
                            class_name=class_name.title(),
                            roll_number=roll_number.upper(),
                            parent_name=parent_name.title(),
                            parent_phone=parent_phone,
                            address=address
                        )
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f"Row {row_num}: {str(e)}")
                
                if success_count > 0:
                    messages.success(request, f'✅ {success_count} students imported successfully!')
                if error_count > 0:
                    messages.warning(request, f'⚠️ {error_count} students failed to import!')
                    for msg in error_messages[:5]:
                        messages.error(request, msg)
                        
            except Exception as e:
                messages.error(request, f'❌ Error reading CSV file: {str(e)}')
            
            return HttpResponseRedirect('../')
        
        return render(request, 'admin/import_csv.html', {
            'title': 'Import Students from CSV',
            'model_name': 'Student',
            'fields': ['username', 'student_id', 'full_name', 'class_name', 'roll_number', 'parent_name', 'parent_phone', 'address'],
            'sample_csv': 'username,student_id,full_name,class_name,roll_number,parent_name,parent_phone,address\nraj123,STU001,Raj Kumar,Class 10,101,Suresh Kumar,9876543210,Delhi\npriya456,STU002,Priya Singh,Class 9,102,Neha Singh,9876543211,Mumbai',
            'password_note': 'Default password for imported students: student@123'
        })


# ============================================================
# TEACHER ADMIN WITH CSV IMPORT
# ============================================================

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher_id', 'full_name', 'subject', 'qualification', 'experience_years', 'phone', 'created_at')
    list_filter = ('subject', 'experience_years', 'created_at')
    search_fields = ('teacher_id', 'full_name', 'subject', 'qualification', 'phone')
    list_per_page = 25
    readonly_fields = ('created_at', 'updated_at')
    actions = [export_teachers_csv]
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.import_csv, name='import_teachers_csv'),
        ]
        return custom_urls + urls
    
    def import_csv(self, request):
        """Import teachers from CSV file"""
        from accounts.models import User  # ✅ Local import to avoid circular import
        
        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')
            
            if not csv_file:
                messages.error(request, '❌ Please select a CSV file.')
                return HttpResponseRedirect(request.path_info)
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, '❌ Please upload a CSV file only.')
                return HttpResponseRedirect(request.path_info)
            
            try:
                data = csv_file.read().decode('utf-8')
                io_string = io.StringIO(data)
                reader = csv.DictReader(io_string)
                
                success_count = 0
                error_count = 0
                error_messages = []
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        username = row.get('username', '').strip()
                        teacher_id = row.get('teacher_id', '').strip()
                        full_name = row.get('full_name', '').strip()
                        subject = row.get('subject', '').strip()
                        qualification = row.get('qualification', '').strip()
                        phone = row.get('phone', '').strip()
                        experience_years = row.get('experience_years', '0').strip()
                        
                        if not username:
                            error_count += 1
                            error_messages.append(f"Row {row_num}: Username is required")
                            continue
                        
                        if User.objects.filter(username=username).exists():
                            error_count += 1
                            error_messages.append(f"Row {row_num}: Username '{username}' already exists")
                            continue
                        
                        if Teacher.objects.filter(teacher_id=teacher_id).exists():
                            error_count += 1
                            error_messages.append(f"Row {row_num}: Teacher ID '{teacher_id}' already exists")
                            continue
                        
                        try:
                            exp_years = int(experience_years) if experience_years else 0
                        except ValueError:
                            exp_years = 0
                        
                        # Create User
                        user = User.objects.create_user(
                            username=username,
                            password='teacher@123',
                            first_name=full_name.split()[0] if full_name else username,
                            last_name=' '.join(full_name.split()[1:]) if len(full_name.split()) > 1 else '',
                            role='teacher',
                            phone=phone,
                            status='approved',
                        )
                        
                        # Create Teacher
                        Teacher.objects.create(
                            user=user,
                            teacher_id=teacher_id.upper(),
                            full_name=full_name.title(),
                            subject=subject.title(),
                            qualification=qualification,
                            experience_years=exp_years,
                            phone=phone
                        )
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f"Row {row_num}: {str(e)}")
                
                if success_count > 0:
                    messages.success(request, f'✅ {success_count} teachers imported successfully!')
                if error_count > 0:
                    messages.warning(request, f'⚠️ {error_count} teachers failed to import!')
                    for msg in error_messages[:5]:
                        messages.error(request, msg)
                        
            except Exception as e:
                messages.error(request, f'❌ Error reading CSV file: {str(e)}')
            
            return HttpResponseRedirect('../')
        
        return render(request, 'admin/import_csv.html', {
            'title': 'Import Teachers from CSV',
            'model_name': 'Teacher',
            'fields': ['username', 'teacher_id', 'full_name', 'subject', 'qualification', 'experience_years', 'phone'],
            'sample_csv': 'username,teacher_id,full_name,subject,qualification,experience_years,phone\nrajesh,TCH001,Rajesh Sharma,Mathematics,M.Sc,5,9876543210\nneha,TCH002,Neha Verma,Physics,M.Sc,3,9876543211',
            'password_note': 'Default password for imported teachers: teacher@123'
        })