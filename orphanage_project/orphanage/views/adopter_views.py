from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from orphanage.models import Child, Adopter, AdoptionApplication, AdoptionInterest
from orphanage.forms.adopter_forms import (
    AdopterRegistrationForm, AdopterLoginForm, AdoptionInterestForm, 
    AdoptionApplicationForm, AdopterProfileUpdateForm
)

def adopter_register(request):
    if request.method == 'POST':
        form = AdopterRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created successfully for {username}! Please wait for admin approval.')
            return redirect('orphanage:adopter_login')
    else:
        form = AdopterRegistrationForm()
    
    return render(request, 'orphanage/adopter/register.html', {'form': form})

def adopter_login(request):
    if request.method == 'POST':
        form = AdopterLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                try:
                    adopter = user.adopter_profile
                    if adopter.is_approved:
                        login(request, user)
                        messages.success(request, f'Welcome back, {user.get_full_name()}!')
                        return redirect('orphanage:adopter_dashboard')
                    else:
                        messages.warning(request, 'Your account is pending admin approval. Please wait.')
                except Adopter.DoesNotExist:
                    messages.error(request, 'Adopter profile not found.')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AdopterLoginForm()
    
    return render(request, 'orphanage/adopter/login.html', {'form': form})

@login_required
def adopter_dashboard(request):
    try:
        adopter = request.user.adopter_profile
    except Adopter.DoesNotExist:
        messages.error(request, 'Adopter profile not found.')
        return redirect('orphanage:adopter_register')
    
    # Get adopter's applications and interests
    applications = AdoptionApplication.objects.filter(adopter=adopter).order_by('-application_date')
    interests = AdoptionInterest.objects.filter(adopter=adopter).order_by('-interest_date')
    
    # Get children available for adoption (not already applied for)
    applied_child_ids = applications.values_list('child_id', flat=True)
    available_children = Child.objects.exclude(id__in=applied_child_ids)[:6]
    
    context = {
        'adopter': adopter,
        'applications': applications[:5],  
        'interests': interests[:5],  
        'available_children': available_children,
        'total_applications': applications.count(),
        'pending_applications': applications.filter(status='pending').count(),
    }
    
    return render(request, 'orphanage/adopter/dashboard.html', context)

@login_required
def browse_children(request):
    try:
        adopter = request.user.adopter_profile
    except Adopter.DoesNotExist:
        messages.error(request, 'Adopter profile not found.')
        return redirect('orphanage:adopter_register')
    
    # Get search parameters
    search_query = request.GET.get('search', '')
    gender_filter = request.GET.get('gender', '')
    age_min = request.GET.get('age_min', '')
    age_max = request.GET.get('age_max', '')
    
    # Get children available for adoption
    applied_child_ids = AdoptionApplication.objects.filter(adopter=adopter).values_list('child_id', flat=True)
    children = Child.objects.exclude(id__in=applied_child_ids)
    
    # Apply filters
    if search_query:
        children = children.filter(name__icontains=search_query)
    
    if gender_filter:
        children = children.filter(gender=gender_filter)
    
    if age_min:
        children = children.filter(age__gte=age_min)
    
    if age_max:
        children = children.filter(age__lte=age_max)
    
    # Pagination
    paginator = Paginator(children, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'gender_filter': gender_filter,
        'age_min': age_min,
        'age_max': age_max,
    }
    
    return render(request, 'orphanage/adopter/browse_children.html', context)

@login_required
def child_detail_adopter(request, child_id):
    try:
        adopter = request.user.adopter_profile
    except Adopter.DoesNotExist:
        messages.error(request, 'Adopter profile not found.')
        return redirect('orphanage:adopter_register')
    
    child = get_object_or_404(Child, id=child_id)
    
    # Check if adopter has already applied for this child
    existing_application = AdoptionApplication.objects.filter(adopter=adopter, child=child).first()
    existing_interest = AdoptionInterest.objects.filter(adopter=adopter, child=child).first()
    
    context = {
        'child': child,
        'adopter': adopter,
        'existing_application': existing_application,
        'existing_interest': existing_interest,
    }
    
    return render(request, 'orphanage/adopter/child_detail.html', context)

@login_required
def express_interest(request, child_id):
    try:
        adopter = request.user.adopter_profile
    except Adopter.DoesNotExist:
        messages.error(request, 'Adopter profile not found.')
        return redirect('orphanage:adopter_register')
    
    child = get_object_or_404(Child, id=child_id)
    
    # Check if already expressed interest
    if AdoptionInterest.objects.filter(adopter=adopter, child=child).exists():
        messages.info(request, 'You have already expressed interest in this child.')
        return redirect('orphanage:child_detail_adopter', child_id=child_id)
    
    if request.method == 'POST':
        form = AdoptionInterestForm(request.POST)
        if form.is_valid():
            interest = form.save(commit=False)
            interest.adopter = adopter
            interest.child = child
            interest.save()
            messages.success(request, f'Interest expressed for {child.name}! You can now apply for adoption.')
            return redirect('orphanage:child_detail_adopter', child_id=child_id)
    else:
        form = AdoptionInterestForm()
    
    context = {
        'form': form,
        'child': child,
        'adopter': adopter,
    }
    
    return render(request, 'orphanage/adopter/express_interest.html', context)

@login_required
def apply_for_adoption(request, child_id):
    try:
        adopter = request.user.adopter_profile
    except Adopter.DoesNotExist:
        messages.error(request, 'Adopter profile not found.')
        return redirect('orphanage:adopter_register')
    
    child = get_object_or_404(Child, id=child_id)
    
    # Check if already applied
    if AdoptionApplication.objects.filter(adopter=adopter, child=child).exists():
        messages.info(request, 'You have already applied for this child.')
        return redirect('orphanage:child_detail_adopter', child_id=child_id)
    
    # Check if adopter has expressed interest first
    if not AdoptionInterest.objects.filter(adopter=adopter, child=child).exists():
        messages.warning(request, 'Please express interest first before applying for adoption.')
        return redirect('orphanage:express_interest', child_id=child_id)
    
    if request.method == 'POST':
        form = AdoptionApplicationForm(request.POST, adopter=adopter, child=child)
        if form.is_valid():
            application = form.save()
            messages.success(request, f'Application submitted for {child.name}! We will review your application.')
            return redirect('orphanage:adopter_dashboard')
    else:
        form = AdoptionApplicationForm(adopter=adopter, child=child)
    
    context = {
        'form': form,
        'child': child,
        'adopter': adopter,
    }
    
    return render(request, 'orphanage/adopter/apply_adoption.html', context)

@login_required
def my_applications(request):
    try:
        adopter = request.user.adopter_profile
    except Adopter.DoesNotExist:
        messages.error(request, 'Adopter profile not found.')
        return redirect('orphanage:adopter_register')
    
    applications = AdoptionApplication.objects.filter(adopter=adopter).order_by('-application_date')
    
    # Pagination
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'adopter': adopter,
    }
    
    return render(request, 'orphanage/adopter/my_applications.html', context)

@login_required
def my_interests(request):
    try:
        adopter = request.user.adopter_profile
    except Adopter.DoesNotExist:
        messages.error(request, 'Adopter profile not found.')
        return redirect('orphanage:adopter_register')
    
    interests = AdoptionInterest.objects.filter(adopter=adopter).order_by('-interest_date')
    
    # Pagination
    paginator = Paginator(interests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'adopter': adopter,
    }
    
    return render(request, 'orphanage/adopter/my_interests.html', context)

@login_required
def update_profile(request):
    try:
        adopter = request.user.adopter_profile
    except Adopter.DoesNotExist:
        messages.error(request, 'Adopter profile not found.')
        return redirect('orphanage:adopter_register')
    
    if request.method == 'POST':
        form = AdopterProfileUpdateForm(request.POST, instance=adopter)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('orphanage:adopter_dashboard')
    else:
        form = AdopterProfileUpdateForm(instance=adopter)
    
    context = {
        'form': form,
        'adopter': adopter,
    }
    
    return render(request, 'orphanage/adopter/update_profile.html', context)

def adopter_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('orphanage:public_dashboard')
