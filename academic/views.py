from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Subject, Attendance, Marks

@login_required
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'academic/subjects.html', {'subjects': subjects})

@login_required
def attendance_report(request):
    return render(request, 'academic/attendance.html')

@login_required
def marks_report(request):
    return render(request, 'academic/marks.html')