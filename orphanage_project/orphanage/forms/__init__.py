# orphanage/forms/__init__.py
from django import forms
from orphanage.models import Child, Staff   # make sure these models exist

# --- Child Form ---
class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = "__all__"

# --- Staff Form (optional, if you need it too) ---
class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = "__all__"
