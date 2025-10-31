from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from orphanage.models import (
    Child, Staff, StaffAllocation,
    Donation, NeedDonation
)

def public_dashboard(request):
    children = Child.objects.all()
    return render(request, 'public/dashboard.html', {'children': children})

def public_children(request):
    children = Child.objects.all()
    return render(request, 'orphanage/public_children.html', {'children': children})

def child_detail(request, id):
    child = get_object_or_404(Child, pk=id)
    allocations = StaffAllocation.objects.filter(child=child).select_related('staff')
    return render(request, 'orphanage/child_detail.html', {
        'child': child,
        'allocations': allocations
    })
def child_profile(request, child_id):
    child = get_object_or_404(Child, id=child_id)
    return render(request, 'public/child_profile.html', {'child': child})

def donor_recommendation_view(request):
    needs = NeedDonation.objects.filter(fulfilled=False)
    needs_sorted = sorted(
        needs,
        key=lambda n: n.amount_needed - n.amount_raised,
        reverse=True
    )
    return render(request, "orphanage/public/donor_recommendation.html", {
        'needs': needs_sorted
    })

@login_required
def donate_to_need(request, need_id):
    if request.method == "POST":
        need = get_object_or_404(NeedDonation, id=need_id)
        try:
            amount = int(request.POST.get('donation_amount'))
        except ValueError:
            messages.error(request, "Invalid donation amount")
            return redirect('orphanage:donor_recommendation')

        remaining = need.amount_needed - need.amount_raised
        if amount <= 0 or amount > remaining:
            messages.error(request, "Donation amount must be between 1 and remaining needed")
            return redirect('orphanage:donor_recommendation')

        Donation.objects.create(
            amount=amount,
            donor=request.user  
        )

        need.amount_raised += amount
        need.fulfilled = need.amount_raised >= need.amount_needed
        need.save()

        messages.success(request, f"Thank you! You donated ₹{amount} for {need.title}")
    return redirect('orphanage:donor_recommendation')