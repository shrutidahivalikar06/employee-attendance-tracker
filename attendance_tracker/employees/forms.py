from django import forms
from .models import Employee

# Signup Form using ModelForm
class SignupForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'email', 'phone', 'employee_code', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

# Login Form (doesn't need to be a ModelForm)
class LoginForm(forms.Form):
    username = forms.CharField(label="Email or Employee Code")
    password = forms.CharField(widget=forms.PasswordInput)