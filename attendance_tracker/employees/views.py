from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Employee, Attendance, Request, CheckLog
from .forms import SignupForm, LoginForm
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from datetime import datetime, date, time

def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                employee = Employee.objects.get(Q(email=username) | Q(employee_code=username))
                
                if employee.password == password:
                    request.session['employee_id'] = employee.id
                    request.session['is_hr'] = employee.is_hr
                    messages.success(request, f"Welcome, {employee.first_name}!")
                    return redirect('dashboard')
                else:
                    form.add_error(None, "Incorrect password.")

            except Employee.DoesNotExist:
                form.add_error(None, "Employee not found.")

    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        request.session.flush()
        messages.success(request, "Logged out successfully.")
        return redirect('login')
    return redirect('dashboard')

def get_employee_from_session(request):
    employee_id = request.session.get('employee_id')
    if not employee_id:
        return None
    try:
        employee = Employee.objects.get(id=employee_id)
        return employee
    except Employee.DoesNotExist:
        return None

def dashboard(request):
    employee = get_employee_from_session(request)
    if not employee:
        messages.error(request, "Please login first.")
        return redirect('login')

    # Fetch logs for this employee (using employee id or username depending on CheckLog model)
    logs = CheckLog.objects.filter(user=employee).order_by('-check_in')

    # To disable Check In button if there is an active check-in without check-out
    has_active_log = CheckLog.objects.filter(user=employee, check_out__isnull=True).exists()
    requests = Request.objects.filter(empid=employee.employee_code)


    return render(request, 'employee-dashboard.html', {
        'employee': employee,
        'logs': logs,
        'has_active_log': has_active_log,
        'requests': requests,  # ⬅️ Send this to template

    })

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt  # If using AJAX with fetch, handle CSRF properly

def check_in(request):
    if request.method == 'POST':
        employee = get_employee_from_session(request)
        if not employee:
            return JsonResponse({'error': 'Not logged in'}, status=401)

        active_log = CheckLog.objects.filter(user=employee, check_out__isnull=True).first()
        if active_log:
            return JsonResponse({'error': 'Already checked in'}, status=400)
        else:
            checkin_time = timezone.now()
            CheckLog.objects.create(user=employee, check_in=checkin_time)
            # Optionally serialize logs to update the table
            return JsonResponse({'check_in': checkin_time.strftime("%H:%M:%S %d/%m/%Y")})

    return JsonResponse({'error': 'Invalid method'}, status=405)

def check_out(request):
    if request.method == 'POST':
        employee = get_employee_from_session(request)
        if not employee:
            return JsonResponse({'error': 'Not logged in'}, status=401)

        active_log = CheckLog.objects.filter(user=employee, check_out__isnull=True).first()
        if not active_log:
            return JsonResponse({'error': 'No active check-in found'}, status=400)
        else:
            checkout_time = timezone.now()
            active_log.check_out = checkout_time
            active_log.save()
            # Calculate hours worked
            hours_worked = (checkout_time - active_log.check_in).total_seconds() / 3600
            hours_worked_str = f"{hours_worked:.2f}"
            return JsonResponse({
                'check_out': checkout_time.strftime("%H:%M:%S %d/%m/%Y"),
                'hours_worked': hours_worked_str
            })

    return JsonResponse({'error': 'Invalid method'}, status=405)

def submit_request(request):
    if request.method == 'POST':
        empid = request.POST.get('empid')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        reason = request.POST.get('reason')

        Request.objects.create(
            empid=empid,
            first_name=first_name,
            last_name=last_name,
            reason=reason
        )
        messages.success(request, "Request submitted successfully!")
        return redirect('dashboard')
    return redirect('dashboard')

from django.http import JsonResponse
from django.utils.timezone import localtime

def get_logs(request):
    employee = get_employee_from_session(request)
    if not employee:
        return JsonResponse([], safe=False)

    logs = CheckLog.objects.filter(user=employee).order_by('-check_in')
    data = []
    for log in logs:
        hours = None
        if log.check_out:
            delta = log.check_out - log.check_in
            hours = f"{delta.total_seconds() / 3600:.2f}"
        data.append({
            'check_in': localtime(log.check_in).strftime("%H:%M:%S %d/%m/%Y"),
            'check_out': localtime(log.check_out).strftime("%H:%M:%S %d/%m/%Y") if log.check_out else None,
            'hours_worked': hours,
        })
    return JsonResponse(data, safe=False)

def hr_dashboard(request):
    employee = get_employee_from_session(request)
    if not employee or not employee.is_hr:
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    all_logs = CheckLog.objects.select_related('user').order_by('-check_in')
    requests = Request.objects.all().order_by('-id')

    return render(request, 'hr-dashboard.html', {
        'employee': employee,
        'logs': all_logs,
        'requests': requests,
    })


from django.views.decorators.http import require_POST
@require_POST
def update_request_status(request, req_id, status):
    if not get_employee_from_session(request).is_hr:
        return redirect('dashboard')

    try:
        req = Request.objects.get(id=req_id)
        if status in ['approved', 'rejected']:
            req.status = status
            req.save()
            messages.success(request, f"Request {status}.")
    except Request.DoesNotExist:
        messages.error(request, "Request not found.")
    
    return redirect('hr_dashboard')

from django.shortcuts import get_object_or_404

@require_POST
def handle_request_action(request, req_id):
    req = get_object_or_404(Request, id=req_id)
    action = request.POST.get('action')

    if action == 'approve':
        req.status = 'approved'
    elif action == 'reject':
        req.status = 'rejected'

    req.save()
    messages.success(request, f"Request {action}d successfully.")
    return redirect('hr_dashboard')

from employees.models import CheckLog
def yearly_report(request):
    employee_obj = get_employee_from_session(request)
    if not employee_obj:
        messages.error(request, "Please log in first.")
        return redirect('login')

    records = None
    selected_date = None

    if request.method == "POST":
        selected_date = request.POST.get("selected_date")
        if selected_date:
            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
            records = CheckLog.objects.filter(
                user=employee_obj,
                check_in__date=date_obj
            )

    return render(request, "yearly_report.html", {
        "records": records,
        "selected_date": selected_date
    })

from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    logout(request)
    return redirect('login')  # Replace with your login URL name
