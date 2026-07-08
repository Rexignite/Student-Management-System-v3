import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import User
from users.models import Student, Teacher
from academic.models import Subject
from django.contrib.auth.hashers import make_password

print("🚀 Starting data import...")

# 1. Create Superuser (Director)
if not User.objects.filter(username='director').exists():
    User.objects.create(
        username='director',
        email='riteshyadav.22564@gmail.com',
        password=make_password('Director@123'),
        role='director',
        status='approved',
        is_superuser=True,
        is_staff=True,
        is_active=True
    )
    print("✅ Director created: director / Director@123")
else:
    print("ℹ️ Director already exists")

# 2. Create Student
if not User.objects.filter(username='student1').exists():
    user = User.objects.create(
        username='student1',
        email='student1@gmail.com',
        password=make_password('Student@123'),
        role='student',
        status='approved',
        is_active=True
    )
    Student.objects.create(
        user=user,
        student_id='STU2024001',
        full_name='Rahul Sharma',
        class_name='12th Science',
        roll_number='001',
        parent_name='Mr. Sharma',
        parent_phone='9876543210',
        address='Mumbai, Maharashtra'
    )
    print("✅ Student created: student1 / Student@123")
else:
    print("ℹ️ Student already exists")

# 3. Create Teacher
if not User.objects.filter(username='teacher1').exists():
    user = User.objects.create(
        username='teacher1',
        email='teacher1@gmail.com',
        password=make_password('Teacher@123'),
        role='teacher',
        status='approved',
        is_active=True
    )
    Teacher.objects.create(
        user=user,
        teacher_id='TCH2024001',
        full_name='Dr. Priya Patel',
        subject='Mathematics',
        qualification='Ph.D. in Mathematics',
        experience_years=10,
        phone='9876543211'
    )
    print("✅ Teacher created: teacher1 / Teacher@123")
else:
    print("ℹ️ Teacher already exists")

# 4. Create Subject
teacher = Teacher.objects.first()
if not Subject.objects.filter(subject_code='MATH101').exists() and teacher:
    Subject.objects.create(
        subject_code='MATH101',
        subject_name='Mathematics',
        teacher=teacher,
        description='Basic Mathematics Course'
    )
    print("✅ Subject created: MATH101 - Mathematics")
else:
    print("ℹ️ Subject already exists or no teacher found")

print("🎉 Data import completed!")
