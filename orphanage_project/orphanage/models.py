from django.db import models
from django.contrib.auth.models import User
from datetime import date

# Child Model 
class Child(models.Model):
    name = models.CharField(max_length=100)
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    )
    admission_date = models.DateField(default=date.today)
    photo = models.ImageField(upload_to='child_photos/', null=True, blank=True)
    priority = models.IntegerField(default=1)
    need = models.TextField(blank=True, null=True)
    age = models.IntegerField(null=True, blank=True)
    child_need_fulfilled = models.BooleanField(default=False)
    
    # Enhanced profile fields
    date_of_birth = models.DateField(null=True, blank=True, help_text="Child's date of birth")
    background = models.TextField(blank=True, null=True, help_text="Child's background story and history")
    hobbies_interests = models.TextField(blank=True, null=True, help_text="Child's hobbies, interests, and activities")
    personality = models.TextField(blank=True, null=True, help_text="Child's personality traits and characteristics")
    health_status = models.TextField(blank=True, null=True, help_text="Health conditions and medical information")
    education_level = models.CharField(max_length=50, blank=True, null=True, help_text="Current education level")
    favorite_subjects = models.CharField(max_length=200, blank=True, null=True, help_text="Favorite subjects or activities")
    special_skills = models.TextField(blank=True, null=True, help_text="Special talents or skills")
    dietary_requirements = models.TextField(blank=True, null=True, help_text="Any dietary restrictions or preferences")
    languages_spoken = models.CharField(max_length=200, blank=True, null=True, help_text="Languages the child speaks")
    is_available_for_adoption = models.BooleanField(default=True, help_text="Whether child is available for adoption")
    adoption_notes = models.TextField(blank=True, null=True, help_text="Special notes for potential adopters")

    def __str__(self):
        return self.name
    
    @property
    def calculated_age(self):
        """Calculate age from date of birth if available"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return self.age

#  Staff Model
class Staff(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

#  Donor Model
class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='donor_profile')

    def __str__(self):
        return self.user.username

#  Orphanage Model 
class Orphanage(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name

class NeedDonation(models.Model):
    SECTION_CHOICES = [
        ('Food', 'Food'),
        ('Education', 'Education'),
        ('Clothing', 'Clothing'),
        ('Health', 'Health'),
        ('Other', 'Other'),
    ]

    orphanage = models.ForeignKey(Orphanage, on_delete=models.CASCADE, related_name='needs')
    title = models.CharField(max_length=150, default="General Need")
    section = models.CharField(max_length=50, choices=SECTION_CHOICES, default="Other")
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100)  # add this if you want category

    amount_needed = models.DecimalField(max_digits=10, decimal_places=2)
    amount_raised = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fulfilled = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.fulfilled = self.amount_raised >= self.amount_needed
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.section}) - {self.orphanage.name}"


#  Donation Model 
class Donation(models.Model):
    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    allocated_need = models.ForeignKey(
        NeedDonation, null=True, blank=True, on_delete=models.SET_NULL, related_name='donations'
    )
    is_allocated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.donor.user.username} → ₹{self.amount}"

#  Staff Allocation Model 
class StaffAllocation(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='staff_allocations')
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='child_allocations')
    allocated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff.name} → {self.child.name}"

from django.db import models
from django.contrib.auth.models import User

class DonationAllocation(models.Model):
    donation = models.ForeignKey("Donation", on_delete=models.CASCADE)
    child = models.ForeignKey("Child", on_delete=models.CASCADE, null=True, blank=True)
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    need = models.ForeignKey("NeedDonation", on_delete=models.SET_NULL, null=True, blank=True)

    # NEW FIELD
    allocated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="allocations_made"
    )

    def __str__(self):
        return f"Allocation of {self.allocated_amount} from {self.donation} to {self.child or 'General'}"


class Allocation(models.Model):
    child = models.ForeignKey(Child, on_delete=models.CASCADE)
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE)
    allocated_amount = models.FloatField(db_column='amount')
    date = models.DateTimeField(auto_now_add=True, db_column='allocated_at')

class Expense(models.Model):
    orphanage_name = models.CharField(max_length=100, blank=True, null=True)  # optional if only one orphanage
    total_amount = models.FloatField()
    description = models.TextField()
    date = models.DateField(auto_now_add=True)

class ExpenseAllocation(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="allocations")
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="expense_allocations")
    amount = models.FloatField()

# Adopter Model
class Adopter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='adopter_profile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    annual_income = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    family_size = models.IntegerField(default=1)
    marital_status = models.CharField(
        max_length=20,
        choices=[
            ('Single', 'Single'),
            ('Married', 'Married'),
            ('Divorced', 'Divorced'),
            ('Widowed', 'Widowed')
        ],
        default='Single'
    )
    has_children = models.BooleanField(default=False)
    adoption_experience = models.TextField(blank=True, null=True)
    motivation = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.username})"

# Adoption Application Model
class AdoptionApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ]
    
    adopter = models.ForeignKey(Adopter, on_delete=models.CASCADE, related_name='adoption_applications')
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='adoption_applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    application_date = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_applications'
    )
    
    class Meta:
        unique_together = ['adopter', 'child']
    
    def __str__(self):
        return f"{self.adopter.user.get_full_name()} → {self.child.name} ({self.status})"

# Adoption Interest Model (for tracking interest before formal application)
class AdoptionInterest(models.Model):
    adopter = models.ForeignKey(Adopter, on_delete=models.CASCADE, related_name='interests')
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='interests')
    interest_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['adopter', 'child']
    
    def __str__(self):
        return f"{self.adopter.user.get_full_name()} interested in {self.child.name}"