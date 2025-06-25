from django.db import models
from django.contrib.auth.models import User
class Employee(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    employee_code = models.CharField(max_length=10, unique=True)
    password = models.CharField(max_length=100)
    is_hr = models.BooleanField(default=False)  # False = Employee, True = HR

    

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_code})"


class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee.employee_code} - {self.date}"
    

class Request(models.Model):
    empid = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    reason = models.TextField(default="Not specified")  # ✅ ADD DEFAULT HERE

    status_choices = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=10, choices=status_choices, default='pending')

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.reason[:30]}"
# Create your models here.

from django.db import models
class CheckLog(models.Model):
    user = models.ForeignKey(Employee, on_delete=models.CASCADE)
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(null=True, blank=True)
    def __str__(self):
      return f"{self.user} - Checked in at {self.check_in}"

 
