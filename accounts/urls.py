# accounts/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# ✅ Comment out app_name since using direct URLs
# app_name = 'accounts'

urlpatterns = [
    # ==================== AUTHENTICATION ====================
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # ==================== OTP BASED PASSWORD RESET ====================
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('set-new-password/', views.set_new_password, name='set_new_password'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    
    # ==================== PASSWORD CHANGE (LOGGED IN USERS) ====================
    path('password-change/', views.change_password, name='change_password'),
    
    # ==================== PROFILE ====================
    path('profile/', views.view_profile, name='view_profile'),
    path('profile/update-pic/', views.update_profile_pic, name='update_profile_pic'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    
    # ==================== DIRECTOR DASHBOARD ====================
    path('director/', views.director_dashboard, name='director_dashboard'),
    path('director/notifications/send/', views.send_notification, name='send_notification'),
    
    # ==================== DIRECTOR - MANAGE ALL USERS ====================
    path('director/users/', views.manage_all_users, name='manage_all_users'),
    path('director/users/change-password/<int:user_id>/', views.admin_change_password, name='admin_change_password'),
    path('director/users/reset-password/<int:user_id>/', views.admin_reset_password, name='admin_reset_password'),
    
    # ==================== DIRECTOR - STUDENT MANAGEMENT ====================
    path('director/students/', views.manage_students, name='manage_students'),
    path('director/students/add/', views.add_student, name='add_student'),
    path('director/students/edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('director/students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    
    # ==================== DIRECTOR - TEACHER MANAGEMENT ====================
    path('director/teachers/', views.manage_teachers, name='manage_teachers'),
    path('director/teachers/add/', views.add_teacher, name='add_teacher'),
    path('director/teachers/edit/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    path('director/teachers/delete/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),
    
    # ==================== DIRECTOR - SUBJECT MANAGEMENT ====================
    path('director/subjects/', views.manage_subjects, name='manage_subjects'),
    path('director/subjects/add/', views.add_subject, name='add_subject'),
    path('director/subjects/edit/<int:subject_id>/', views.edit_subject, name='edit_subject'),
    path('director/subjects/delete/<int:subject_id>/', views.delete_subject, name='delete_subject'),
    path('director/subjects/assign/<int:subject_id>/', views.assign_teacher_to_subject, name='assign_teacher_to_subject'),
    
    # ==================== DIRECTOR - ATTENDANCE ====================
    path('director/attendance/', views.attendance_overview, name='attendance_overview'),
    path('director/attendance/download/', views.download_attendance_report, name='download_attendance_report'),
    
    # ==================== DIRECTOR - CSV UPLOAD ====================
    path('director/students/upload/', views.upload_students_csv, name='upload_students_csv'),
    path('director/teachers/upload/', views.upload_teachers_csv, name='upload_teachers_csv'),
    path('director/subjects/upload/', views.upload_subjects_csv, name='upload_subjects_csv'),
    
    # ==================== DIRECTOR - CSV DOWNLOAD ====================
    path('director/students/download/', views.download_students_csv, name='download_students_csv'),
    path('director/teachers/download/', views.download_teachers_csv, name='download_teachers_csv'),
    path('director/attendance/download-full/', views.download_full_attendance_csv, name='download_full_attendance_csv'),
    path('director/marks/download-full/', views.download_full_marks_csv, name='download_full_marks_csv'),
    
    # ==================== DIRECTOR - NOTIFICATION MANAGEMENT ====================
    path('director/notifications/', views.manage_notifications, name='manage_notifications'),
    path('director/notifications/add/', views.add_notification, name='add_notification'),
    path('director/notifications/edit/<int:notif_id>/', views.edit_notification, name='edit_notification'),
    path('director/notifications/delete/<int:notif_id>/', views.delete_notification, name='delete_notification'),
    
    # ==================== DIRECTOR - USER APPROVAL MANAGEMENT ====================
    path('director/users/pending/', views.pending_users, name='pending_users'),
    path('director/users/approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('director/users/reject/<int:user_id>/', views.reject_user, name='reject_user'),
    path('director/users/approved/', views.approved_users, name='approved_users'),
    path('director/users/rejected/', views.rejected_users, name='rejected_users'),
    
    # ==================== TEACHER DASHBOARD ====================
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/students/', views.teacher_manage_students, name='teacher_manage_students'),
    path('teacher/students/edit/<int:student_id>/', views.teacher_edit_student, name='teacher_edit_student'),
    
    # ==================== TEACHER - MONTHLY ATTENDANCE ====================
    path('teacher/monthly-attendance/', views.monthly_attendance_calendar, name='monthly_attendance_calendar'),
    path('teacher/attendance/update-monthly/', views.update_monthly_attendance, name='update_monthly_attendance'),
    
    # ==================== TEACHER - MARKS MANAGEMENT ====================
    path('teacher/manage-marks/', views.teacher_manage_marks, name='teacher_manage_marks'),
    path('teacher/add-marks/', views.add_marks, name='add_marks'),
    path('teacher/edit-marks/<int:marks_id>/', views.edit_marks, name='edit_marks'),
    path('teacher/delete-marks/<int:marks_id>/', views.delete_marks, name='delete_marks'),
    path('teacher/student-marks-detail/<int:student_id>/', views.student_marks_detail, name='student_marks_detail'),
    
    # ==================== TEACHER - AJAX ENDPOINTS ====================
    path('teacher/get-students-by-subject/', views.get_students_by_subject, name='get_students_by_subject'),
    path('teacher/get-student-attendance/<int:student_id>/', views.get_student_attendance, name='get_student_attendance'),
    
    # ==================== TEACHER - CSV OPERATIONS ====================
    path('teacher/upload-marks-csv/', views.teacher_upload_marks_csv, name='teacher_upload_marks_csv'),
    path('teacher/upload-attendance-csv/', views.teacher_upload_attendance_csv, name='teacher_upload_attendance_csv'),
    path('teacher/download-class-students/', views.download_class_students_csv, name='download_class_students_csv'),
    path('teacher/download-marks-sample/', views.download_marks_sample_csv, name='download_marks_sample_csv'),
    path('teacher/download-attendance-sample/', views.download_attendance_sample_csv, name='download_attendance_sample_csv'),
    
    # ==================== TEACHER - ATTENDANCE DETAILS ====================
    path('teacher/attendance-details/<int:attendance_id>/', views.teacher_attendance_details, name='teacher_attendance_details'),
    
    # ==================== STUDENT DASHBOARD ====================
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('student/marks/', views.student_marks, name='student_marks'),
    
    # ==================== STUDENT - MONTHLY ATTENDANCE ====================
    path('student/monthly-attendance/', views.student_monthly_attendance, name='student_monthly_attendance'),
    path('student/attendance/monthly-data/', views.student_monthly_attendance_data, name='student_monthly_attendance_data'),
    
    # ==================== STUDENT - CSV DOWNLOAD ====================
    path('student/attendance/download/', views.student_download_attendance_csv, name='student_download_attendance_csv'),
    path('student/marks/download/', views.student_download_marks_csv, name='student_download_marks_csv'),
    
    # ==================== NOTIFICATIONS (FOR ALL USERS) ====================
    path('notifications/', views.view_notifications, name='view_notifications'),
    path('notifications/mark-read/<int:notif_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # ==================== AJAX ENDPOINTS ====================
    path('get-csrf-token/', views.get_csrf_token, name='get_csrf_token'),
    path('check-username/', views.check_username_availability, name='check_username_availability'),
    
    # ==================== HEALTH CHECK ====================
    path('health/', views.health_check, name='health_check'),
]

# ==================== ERROR HANDLERS ====================
handler403 = 'accounts.views.custom_403'
handler404 = 'accounts.views.custom_404'
handler500 = 'accounts.views.custom_500'