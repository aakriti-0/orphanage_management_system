from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from orphanage.models import (
    Child, Staff, Donor, Donation, NeedDonation,
    StaffAllocation, DonationAllocation, Allocation,
    Adopter, AdoptionApplication, AdoptionInterest
)
from orphanage.forms.admin_forms import StaffForm, ChildForm, NeedDonationForm
from orphanage.utils import greedy_staff_allocation
from orphanage.forms.admin_forms import ExpenseForm
from orphanage.models import Expense

#  Session Check Decorator 
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_logged_in'):
            return redirect('orphanage:admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper

# Admin Login 
def admin_login(request):
    if request.session.get('admin_logged_in'):
        return redirect('orphanage:admin_dashboard')

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username == "admin" and password == "admin123":
            request.session['admin_logged_in'] = True
            return redirect('orphanage:admin_dashboard')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "orphanage/admin/admin_login.html")

# Admin Logout 
def admin_logout(request):
    request.session.flush()
    return redirect('orphanage:admin_login')

#  Dashboard 

@admin_required
def admin_dashboard(request):
    allocations = DonationAllocation.objects.all()
    children = Child.objects.all()
    needs = NeedDonation.objects.all()
    unallocated_donations = Donation.objects.filter(is_allocated=False).order_by('-date')
    
    # Admin allocation report data
    from django.db.models import Sum
    allocations_by_child = (
        allocations
        .values('child__name')
        .annotate(total=Sum('allocated_amount'))
        .order_by('child__name')
    )
    allocations_by_donor = (
        allocations
        .values('donation__donor__user__username')
        .annotate(total=Sum('allocated_amount'))
        .order_by('donation__donor__user__username')
    )
    detailed_allocations = (
        allocations
        .select_related('child', 'donation', 'donation__donor__user', 'donation__allocated_need')
        .order_by('-date')
    )

    context = {
        "allocations": allocations,
        "children": children,
        "needs": needs,
        "total_children": children.count(),
        "total_donors": Donation.objects.values("donor").distinct().count(),
        "total_donations": Donation.objects.all().count(),
        "total_allocations": allocations.count(),
        "available_funds": sum(d.amount for d in Donation.objects.all()) -
                           sum(a.allocated_amount for a in allocations),
        "unallocated_donations": unallocated_donations,
        "allocations_by_child": allocations_by_child,
        "allocations_by_donor": allocations_by_donor,
        "detailed_allocations": detailed_allocations,
    }
    return render(request, "orphanage/admin/admin_dashboard.html", context)


@admin_required
def allocate_view(request, donation_id):
    donation = Donation.objects.get(id=donation_id)
    needs = NeedDonation.objects.filter(fulfilled=False)
    children = Child.objects.all()

    allocated_by_user = request.user if getattr(request.user, 'is_authenticated', False) else None
    allocate_donations(donation, needs, children, allocated_by=allocated_by_user)

    return redirect("orphanage:admin_dashboard")

@admin_required
def staff_list(request):
    staffs = Staff.objects.all()
    return render(request, 'orphanage/admin/staff_list.html', {'staffs': staffs})

@admin_required
def add_staff(request):
    form = StaffForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Staff added successfully!")
        return redirect('orphanage:staff_list')
    return render(request, 'orphanage/admin/add_staff.html', {'form': form})

#  Child Management 
@admin_required
def add_child(request):
    form = ChildForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Child added successfully!")
        return redirect('orphanage:admin_dashboard')
    return render(request, 'orphanage/admin/add_child.html', {'form': form})

#  Staff Allocation 
@admin_required
def staff_allocation_list(request):
    greedy_staff_allocation()
    allocations = StaffAllocation.objects.select_related('child', 'staff').all()
    return render(request, 'orphanage/admin/staff_allocation_list.html', {'allocations': allocations})

# Donation Allocation 
@admin_required
def allocate_donations_view(request):
    donations = Donation.objects.filter(is_allocated=False)
    needs = NeedDonation.objects.filter(fulfilled=False)

    with transaction.atomic():
        for donation in donations:
            remaining_amount = float(donation.amount)
            for need in needs:
                remaining_need = float(need.amount_needed) - float(need.amount_raised)
                if remaining_need <= 0:
                    continue

                allocation_amount = min(remaining_amount, remaining_need)

                DonationAllocation.objects.create(
                    donation=donation,
                    need=need,
                    allocated_amount=allocation_amount
                )

                need.amount_raised = float(need.amount_raised) + allocation_amount
                need.fulfilled = need.amount_raised >= need.amount_needed
                need.save()

                remaining_amount -= allocation_amount
                if remaining_amount <= 0:
                    break

            donation.is_allocated = remaining_amount <= 0
            donation.save()

    messages.success(request, "Donations allocated successfully!")
    return redirect('orphanage:admin_dashboard')

#  Need List
@admin_required
def need_list(request):
    needs = NeedDonation.objects.order_by('-amount_needed')
    return render(request, 'orphanage/admin/need_list.html', {'needs': needs})

from orphanage.models import NeedDonation, Orphanage

def add_need(request):
    default_orphanage, _ = Orphanage.objects.get_or_create(name="Default Orphanage")

    if request.method == "POST":
        form = NeedDonationForm(request.POST)
        if form.is_valid():
            need = form.save(commit=False)
            need.orphanage = default_orphanage
            need.save()
            messages.success(request, "Need created successfully!")
            return redirect('orphanage:need_list')
    else:
        form = NeedDonationForm()

    return render(request, "orphanage/admin/add_need.html", {"form": form})

# AJAX Donation Allocation 
@admin_required
def allocate_donations_ajax(request):
    donations = Donation.objects.filter(is_allocated=False).order_by('-amount')
    children = Child.objects.all().order_by('admission_date')

    allocations = []

    with transaction.atomic():
        for child in children:
            for donation in donations:
                if not donation.is_allocated:
                    Allocation.objects.create(
                        child=child,
                        donation=donation,
                        allocated_amount=donation.amount
                    )
                    donation.is_allocated = True
                    donation.save()
                    allocations.append(f"Allocated {donation.amount} to {child.name}")
                    break

    return JsonResponse({'allocations': allocations})

# Allocation Results 
@admin_required
def allocation_results(request):
    allocations = Allocation.objects.select_related('child', 'donation__allocated_need').all()
    return render(request, 'orphanage/admin/allocation_results.html', {
        'allocations': allocations
    })

from django.shortcuts import render, get_object_or_404, redirect
from orphanage.models import Child, StaffAllocation

def admin_child_detail(request, pk):
    if not request.session.get('admin_logged_in'):
        return redirect('orphanage:admin_login')

    child = get_object_or_404(Child, pk=pk)
    allocations = StaffAllocation.objects.filter(child=child).select_related('staff')
    return render(request, 'orphanage/child_detail.html', {
        'child': child,
        'allocations': allocations
    })

@admin_required
def admin_children_list(request):
    children = (
        Child.objects.all()
        .order_by('name')
        .prefetch_related('staff_allocations__staff')
    )

    context = {
        'children': children,
    }
    return render(request, 'orphanage/admin/children_list.html', context)


@admin_required
def admin_allocate_donation_to_child(request, donation_id):
    donation = get_object_or_404(Donation, id=donation_id)
    children = Child.objects.all().order_by('name')

    allocated_total = (
        DonationAllocation.objects
        .filter(donation=donation)
        .aggregate(total=Sum('allocated_amount'))
        .get('total') or 0
    )

    donation_remaining = float(donation.amount) - float(allocated_total)

    if request.method == 'POST':
        child_id = request.POST.get('child_id')
        amount_str = request.POST.get('amount')

        try:
            amount = float(amount_str)
        except (TypeError, ValueError):
            messages.error(request, 'Enter a valid amount.')
            return redirect('orphanage:admin_allocate_donation_to_child', donation_id=donation.id)

        if not child_id:
            messages.error(request, 'Select a child.')
            return redirect('orphanage:admin_allocate_donation_to_child', donation_id=donation.id)

        if amount <= 0 or amount > donation_remaining:
            messages.error(request, 'Amount must be > 0 and within remaining balance.')
            return redirect('orphanage:admin_allocate_donation_to_child', donation_id=donation.id)

        child = get_object_or_404(Child, id=child_id)

        DonationAllocation.objects.create(
            donation=donation,
            child=child,
            allocated_amount=amount,
            allocated_by=request.user if getattr(request.user, 'is_authenticated', False) else None
        )

        # Update donation allocated flag if fully allocated
        new_total = (
            DonationAllocation.objects
            .filter(donation=donation)
            .aggregate(total=Sum('allocated_amount'))
            .get('total') or 0
        )
        donation.is_allocated = float(new_total) >= float(donation.amount)
        donation.save()

        messages.success(request, f'Allocated {amount} to {child.name}.')
        return redirect('orphanage:admin_donation_allocations')

    context = {
        'donation': donation,
        'children': children,
        'donation_remaining': donation_remaining,
        'allocated_total': allocated_total,
    }
    return render(request, 'orphanage/admin/allocate_donation_to_child.html', context)

@admin_required
def admin_edit_child(request, pk):
    child = get_object_or_404(Child, pk=pk)
    form = ChildForm(request.POST or None, request.FILES or None, instance=child)
    if form.is_valid():
        form.save()
        messages.success(request, "Child updated successfully!")
        return redirect('orphanage:admin_children_list')
    return render(request, 'orphanage/admin/edit_child.html', {'form': form, 'child': child})

@admin_required
def admin_delete_child(request, pk):
    child = get_object_or_404(Child, pk=pk)
    if request.method == 'POST':
        child.delete()
        messages.success(request, "Child deleted successfully!")
        return redirect('orphanage:admin_children_list')
    return render(request, 'orphanage/admin/confirm_delete_child.html', {'child': child})

from django.http import JsonResponse
from orphanage.models import Donation, NeedDonation

def allocate_donations_ajax(request):
    """
    Simple allocation: assign unallocated donations to needs in order.
    """
    allocations_result = []

    # Fetch unallocated donations
    donations = Donation.objects.filter(is_allocated=False).order_by('date')
    # Fetch needs that are not fulfilled
    needs = NeedDonation.objects.filter(fulfilled=False).order_by('id')

    for donation in donations:
        remaining_amount = donation.amount
        for need in needs:
            if need.fulfilled:
                continue
            required_amount = need.amount_needed - need.amount_raised
            allocated_amount = min(remaining_amount, required_amount)

            if allocated_amount > 0:
                # Allocate donation
                need.amount_raised += allocated_amount
                if need.amount_raised >= need.amount_needed:
                    need.fulfilled = True
                need.save()

                # Mark donation partially/fully allocated
                remaining_amount -= allocated_amount

                allocations_result.append(
                    f"Donation {donation.id} allocated {allocated_amount} to {need.title}"
                )

                if remaining_amount <= 0:
                    donation.is_allocated = True
                    donation.save()
                    break

        if remaining_amount > 0:
            donation.amount -= remaining_amount  
            donation.save()

    if not allocations_result:
        allocations_result.append("No donations to allocate.")

    return JsonResponse({"allocations": allocations_result})


def allocate_existing_donation(request, donation_id):
    donation = get_object_or_404(Donation, id=donation_id)

    children = Child.objects.all() 

    if request.method == "POST":
        for child in children:
            field_name = f"child_{child.id}"
            amount = request.POST.get(field_name)
            if amount:
                amount = float(amount)
                allocation, created = Allocation.objects.update_or_create(
                    donation=donation,
                    child=child,
                    defaults={"allocated_amount": amount}
                )

        messages.success(request, f"Donation #{donation.id} allocated successfully!")
        return redirect("orphanage:donor_dashboard")

    context = {
        "donation": donation,
        "children": children,
    }
    return render(request, "donor/allocate_existing_donation.html", context)


from orphanage.models import Allocation

def run_allocation(request):
    allocate_donations()
    messages.success(request, "Donations have been allocated successfully!")
    return redirect("view_allocations")

def view_allocations(request):
    allocations = Allocation.objects.select_related("child", "donation")
    return render(request, "orphanage/allocations.html", {"allocations": allocations})

@admin_required
def expense_list(request):
    expenses = Expense.objects.all().order_by('-date')
    return render(request, 'orphanage/admin/expense_list.html', {'expenses': expenses})

@admin_required
def add_expense(request):
    form = ExpenseForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Expense recorded successfully!")
        return redirect('orphanage:expense_list')
    return render(request, 'orphanage/admin/add_expense.html', {'form': form})

@admin_required
def admin_donation_allocations(request):
    allocations = (
        Allocation.objects
        .select_related('child', 'donation__donor__user', 'donation__allocated_need')
        .order_by('-date')
    )
    return render(request, 'orphanage/admin/donation_allocations.html', {
        'allocations': allocations
    })

@admin_required
def admin_adopters_list(request):
    adopters = Adopter.objects.select_related('user').order_by('-created_at')
    return render(request, 'orphanage/admin/adopters_list.html', {
        'adopters': adopters
    })

@admin_required
def admin_adopter_detail(request, adopter_id):
    adopter = get_object_or_404(Adopter, id=adopter_id)
    applications = AdoptionApplication.objects.filter(adopter=adopter).order_by('-application_date')
    interests = AdoptionInterest.objects.filter(adopter=adopter).order_by('-interest_date')
    
    return render(request, 'orphanage/admin/adopter_detail.html', {
        'adopter': adopter,
        'applications': applications,
        'interests': interests
    })

@admin_required
def admin_approve_adopter(request, adopter_id):
    adopter = get_object_or_404(Adopter, id=adopter_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            adopter.is_approved = True
            adopter.save()
            messages.success(request, f'Adopter {adopter.user.get_full_name()} has been approved!')
        elif action == 'reject':
            adopter.is_approved = False
            adopter.save()
            messages.warning(request, f'Adopter {adopter.user.get_full_name()} has been rejected.')
        
        return redirect('orphanage:admin_adopters_list')
    
    return render(request, 'orphanage/admin/approve_adopter.html', {
        'adopter': adopter
    })

@admin_required
def admin_adoption_applications(request):
    applications = AdoptionApplication.objects.select_related(
        'adopter__user', 'child', 'reviewed_by'
    ).order_by('-application_date')
    
    return render(request, 'orphanage/admin/adoption_applications.html', {
        'applications': applications
    })

@admin_required
def admin_review_application(request, application_id):
    application = get_object_or_404(AdoptionApplication, id=application_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        application.status = status
        application.notes = notes
        application.reviewed_by = request.user
        application.review_date = timezone.now()
        application.save()
        
        status_display = dict(AdoptionApplication.STATUS_CHOICES)[status]
        messages.success(request, f'Application status updated to: {status_display}')
        return redirect('orphanage:admin_adoption_applications')
    
    return render(request, 'orphanage/admin/review_application.html', {
        'application': application
    })
