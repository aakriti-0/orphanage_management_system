from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from orphanage.forms.donor_forms import DonorRegistrationForm, DonationForm
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from orphanage.models import Donor, Donation, NeedDonation, Child, Orphanage, DonationAllocation, Allocation
from orphanage.utils import allocate_donations
from decimal import Decimal

#  Donor Registration 
def donor_register(request):
    if request.method == 'POST':
        form = DonorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            Donor.objects.create(user=user)
            messages.success(request, 'Registration successful. Please login.')
            return redirect('orphanage:donor_login')
    else:
        form = DonorRegistrationForm()
    return render(request, 'orphanage/donor/donor_register.html', {'form': form})

#  Donor Login 
def donor_login(request):
    if request.user.is_authenticated:
        if Donor.objects.filter(user=request.user).exists():
            return redirect('orphanage:donor_dashboard')
        else:
            logout(request)
            messages.error(request, "Unauthorized access.")
            return redirect('orphanage:donor_login')

    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None and Donor.objects.filter(user=user).exists():
            login(request, user)
            return redirect('orphanage:donor_dashboard')
        else:
            messages.error(request, "Invalid email/password or not a donor account.")
    return render(request, 'orphanage/donor/donor_login.html')

#  Donor Logout 
@login_required
def donor_logout(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('orphanage:donor_login')

#  Donor Dashboard
@login_required
def donor_dashboard(request):
    donor = get_object_or_404(Donor, user=request.user)
    donations = Donation.objects.filter(donor=donor).order_by('-date')

    total_donations = sum((d.amount for d in donations), Decimal("0"))
    from orphanage.models import Allocation
    total_allocated = Allocation.objects.filter(donation__donor=donor).aggregate(
        total=Sum('allocated_amount')
    )['total'] or 0
    # Normalize to Decimal for a consistent balance calculation
    try:
        total_allocated = Decimal(str(total_allocated))
    except Exception:
        total_allocated = Decimal("0")
    available_balance = (total_donations or Decimal("0")) - (total_allocated or Decimal("0"))
    needs = (
        NeedDonation.objects.filter(fulfilled=False)
        .annotate(
            remaining_needed=ExpressionWrapper(
                F('amount_needed') - F('amount_raised'),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
    )
    children = Child.objects.filter(child_need_fulfilled=False)
    allocations = (
        Allocation.objects.select_related('child', 'donation')
        .filter(donation__donor=donor)
        .order_by('-date')
    )

    # Grouped summaries for report
    allocations_by_child = (
        allocations
        .values('child__name')
        .annotate(total=Sum('allocated_amount'))
        .order_by('child__name')
    )
    allocations_by_need = (
        allocations
        .values('donation__allocated_need__title')
        .annotate(total=Sum('allocated_amount'))
        .order_by('donation__allocated_need__title')
    )
    
    # Detailed allocation breakdown for donor report
    detailed_allocations = (
        allocations
        .select_related('child', 'donation', 'donation__allocated_need')
        .order_by('-date')
    )

    context = {
        'donor': donor,
        'donations': donations,
        'total_donations': total_donations,
        'total_allocated': total_allocated,
        'total_allocations': total_allocated,
        'available_balance': available_balance,
        'needs': needs,
        'children': children,
        'allocations': allocations,
        'allocations_by_child': allocations_by_child,
        'allocations_by_need': allocations_by_need,
        'detailed_allocations': detailed_allocations,
    }
    return render(request, 'orphanage/donor/dashboard.html', context)

#  Make Donation 
@login_required
def make_donation_view(request):
    """
    Donor can make a donation to a specific need and/or children.
    """
    donor = get_object_or_404(Donor, user=request.user)
    needs = NeedDonation.objects.filter(fulfilled=False)
    children = Child.objects.all()

    if request.method == "POST":
        amount = request.POST.get("amount")
        need_id = request.POST.get("need_id")
        # Single child selection from dashboard form
        child_id = request.POST.get("child_id")

        if not amount:
            messages.error(request, "Please enter a donation amount.")
            return redirect('orphanage:donor_dashboard')

        # Create the donation record
        donation_amount = Decimal(amount)
        donation = Donation.objects.create(donor=donor, amount=donation_amount)

        # Allocate to a specific need (optional)
        if need_id:
            need = get_object_or_404(NeedDonation, id=need_id)
            donation.allocated_need = need
            need.amount_raised += donation_amount
            need.fulfilled = need.amount_raised >= need.amount_needed
            need.save()
            donation.save()

        # Allocate to a specific child (from dashboard dropdown)
        if child_id:
            try:
                child = Child.objects.get(id=child_id)
                # Record allocation for the child
                from orphanage.models import Allocation
                Allocation.objects.create(
                    donation=donation,
                    child=child,
                    allocated_amount=float(donation_amount)
                )
                donation.is_allocated = True
                donation.save()
            except Child.DoesNotExist:
                messages.error(request, "Selected child not found.")
                return redirect('orphanage:donor_dashboard')

        try:
            allocate_donations()
        except Exception:
            pass

        messages.success(request, "Donation successful!")
        return redirect('orphanage:donor_dashboard')

    context = {
        'donor': donor,
        'needs': needs,
        'children': children
    }
    return render(request, 'orphanage/donor/make_donation.html', context)

#  Donation Form View
@login_required
def donate(request):
    """
    Form-based donation (alternative to make_donation_view).
    """
    donor = get_object_or_404(Donor, user=request.user)
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = donor
            donation.save()
            allocate_donations()
            messages.success(request, "Thank you for your donation!")
            return redirect('orphanage:donor_dashboard')
    else:
        form = DonationForm()
    return render(request, 'orphanage/donor/donate.html', {'form': form})

#  Donor Recommendations 
@login_required
def donor_recommendation_view(request):
    needs = NeedDonation.objects.filter(fulfilled=False).order_by('-amount_needed')[:5]
    return render(request, 'orphanage/donor/recommendations.html', {
        'recommended_needs': needs
    })

# Allocate Existing Donation 
@login_required
def allocate_existing_donation(request, donation_id):
    donation = get_object_or_404(Donation, id=donation_id)
    donor = get_object_or_404(Donor, user=request.user)
    orphanage = Orphanage.objects.first()
    children = Child.objects.filter(orphanage=orphanage).order_by('needs_score')  # prioritize need

    if request.method == "POST":
        selected_children_ids = request.POST.getlist('children')
        selected_children = Child.objects.filter(id__in=selected_children_ids)
        donation.allocated_children.set(selected_children)
        donation.save()
        messages.success(request, "Donation allocated to children successfully!")
        return redirect('orphanage:donor_dashboard')

    context = {
        'donation': donation,
        'children': children
    }
    return render(request, 'orphanage/donor/allocate_donation.html', context)

@login_required
def donate_to_need(request, need_id):
    donor = get_object_or_404(Donor, user=request.user)
    need = get_object_or_404(NeedDonation, id=need_id)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        if not amount:
            messages.error(request, "Please enter a donation amount.")
            return redirect('orphanage:donor_dashboard')

        donation_amount = Decimal(amount)
        donation = Donation.objects.create(donor=donor, amount=donation_amount, allocated_need=need)
        need.amount_raised += donation_amount
        need.fulfilled = need.amount_raised >= need.amount_needed
        need.save()
        donation.save()

        allocate_donations()
        messages.success(request, "Donation made to the need successfully!")
        return redirect('orphanage:donor_dashboard')

    context = {
        'donor': donor,
        'need': need
    }
    return render(request, 'orphanage/donor/donate_to_need.html', context)


#  Allocation Report CSV 
@login_required
def donor_allocation_report_csv(request):
    import csv
    from django.http import HttpResponse

    donor = get_object_or_404(Donor, user=request.user)
    qs = (
        Allocation.objects
        .select_related('child', 'donation', 'donation__allocated_need')
        .filter(donation__donor=donor)
        .order_by('child__name', 'date')
    )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="my_allocations.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Child Name', 'Allocation Amount (₹)', 'Need Title', 'Donation ID'])
    for a in qs:
        writer.writerow([
            a.date.strftime('%Y-%m-%d %H:%M'),
            a.child.name if a.child else 'General Fund',
            f"₹{a.allocated_amount}",
            a.donation.allocated_need.title if getattr(a.donation, 'allocated_need', None) else 'General Donation',
            a.donation.id
        ])
    return response
