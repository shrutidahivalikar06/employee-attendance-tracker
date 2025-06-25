from django.urls import path
from . import views



urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),  # ✅ ADD THIS LINE
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.custom_logout, name='logout'),
    path('submit-request/', views.submit_request, name='submit_request'),
    path('check-in/', views.check_in, name='check_in'),
    path('check-out/', views.check_out, name='check_out'),
    path('get-logs/', views.get_logs, name='get_logs'),
    path('hr-dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('update-request-status/<int:req_id>/<str:status>/', views.update_request_status, name='update_request_status'),
    path('yearly-report/', views.yearly_report, name='yearly_report'),

]