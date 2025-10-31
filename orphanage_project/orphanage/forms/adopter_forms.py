from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from orphanage.models import Adopter, AdoptionApplication, AdoptionInterest

class AdopterRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=15, required=True)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True)
    occupation = forms.CharField(max_length=100, required=True)
    annual_income = forms.DecimalField(max_digits=12, decimal_places=2, required=True)
    family_size = forms.IntegerField(min_value=1, required=True)
    marital_status = forms.ChoiceField(
        choices=[
            ('Single', 'Single'),
            ('Married', 'Married'),
            ('Divorced', 'Divorced'),
            ('Widowed', 'Widowed')
        ],
        required=True
    )
    has_children = forms.BooleanField(required=False)
    adoption_experience = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        help_text="Describe any previous adoption experience (optional)"
    )
    motivation = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=True,
        help_text="Please explain your motivation for adoption"
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Create adopter profile
            Adopter.objects.create(
                user=user,
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                occupation=self.cleaned_data['occupation'],
                annual_income=self.cleaned_data['annual_income'],
                family_size=self.cleaned_data['family_size'],
                marital_status=self.cleaned_data['marital_status'],
                has_children=self.cleaned_data['has_children'],
                adoption_experience=self.cleaned_data['adoption_experience'],
                motivation=self.cleaned_data['motivation']
            )
        return user

class AdopterLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class AdoptionInterestForm(forms.ModelForm):
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Any additional notes or questions about this child (optional)"
    )

    class Meta:
        model = AdoptionInterest
        fields = ['notes']

class AdoptionApplicationForm(forms.ModelForm):
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=True,
        help_text="Please provide additional information about your application"
    )

    class Meta:
        model = AdoptionApplication
        fields = ['notes']

    def __init__(self, *args, **kwargs):
        self.adopter = kwargs.pop('adopter', None)
        self.child = kwargs.pop('child', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        application = super().save(commit=False)
        if self.adopter:
            application.adopter = self.adopter
        if self.child:
            application.child = self.child
        
        if commit:
            application.save()
        return application

class AdopterProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Adopter
        fields = [
            'phone', 'address', 'occupation', 'annual_income', 
            'family_size', 'marital_status', 'has_children', 
            'adoption_experience', 'motivation'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'adoption_experience': forms.Textarea(attrs={'rows': 4}),
            'motivation': forms.Textarea(attrs={'rows': 4}),
        }
