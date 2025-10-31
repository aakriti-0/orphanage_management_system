from django import forms
from django.contrib.auth.models import User
from orphanage.models import Staff, Child, NeedDonation
from orphanage.models import Expense

# -------------------------
# Admin Login Form
# -------------------------
class AdminLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

# -------------------------
# Admin Registration Form
# -------------------------
class AdminRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create Password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


# -------------------------
# Staff Form
# -------------------------
class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['name', 'role', 'phone', 'email', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# -------------------------
# Child Form
# -------------------------
class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['name', 'age', 'photo', 'admission_date', 'need', 'child_need_fulfilled']
        widgets = {
            'admission_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'need': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Describe the child’s needs'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'child_need_fulfilled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class NeedDonationForm(forms.ModelForm):
    class Meta:
        model = NeedDonation
        fields = ['title', 'section', 'category', 'description', 'amount_needed']


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['orphanage_name', 'total_amount', 'description']
        widgets = {
            'orphanage_name': forms.TextInput(attrs={'class': 'form-control'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
