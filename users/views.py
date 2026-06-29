from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Student, Teacher

# Simple views for users app (can be extended later)
@login_required
def user_profile(request):
    return render(request, 'users/profile.html')

@login_required
def user_list(request):
    return render(request, 'users/list.html')