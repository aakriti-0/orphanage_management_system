#greedy algorithm implementation
from decimal import Decimal
from orphanage.models import Donation, NeedDonation, Child, Staff, StaffAllocation, DonationAllocation

# Greedy Donation Allocation
def greedy_donation_allocation(donation: Donation):
   
    remaining_amount = donation.amount

    needs = NeedDonation.objects.filter(fulfilled=False).order_by('-amount_needed')

    for need in needs:
        need_remaining = need.amount_needed - need.amount_raised
        if need_remaining <= 0:
            need.fulfilled = True
            need.save()
            continue

        allocation_amount = min(remaining_amount, need_remaining)

        DonationAllocation.objects.create(
            donation=donation,
            need_donation=need,
            amount_allocated=allocation_amount
        )

        need.amount_raised += Decimal(allocation_amount)
        if need.amount_raised >= need.amount_needed:
            need.fulfilled = True
        need.save()

        remaining_amount -= Decimal(allocation_amount)
        if remaining_amount <= 0:
            break

    donation.allocated_to_child = remaining_amount <= 0
    donation.save()


# Greedy Staff Allocation
def greedy_staff_allocation():
   
    unallocated_children = Child.objects.exclude(
        id__in=StaffAllocation.objects.values_list('child_id', flat=True)
    )

    available_staff = list(Staff.objects.filter(is_available=True))

    for child in unallocated_children:
        if not available_staff:
            break  

        staff = available_staff.pop(0)  

        StaffAllocation.objects.create(child=child, staff=staff)

        staff.is_available = False
        staff.save()


from orphanage.models import Donation, NeedDonation

def allocate_donations():
    """
    Allocate unallocated donations to unmet needs.
    """
    unallocated_donations = Donation.objects.filter(is_allocated=False).order_by('date')
    
    unmet_needs = NeedDonation.objects.filter(fulfilled=False).order_by('amount_needed')

    for donation in unallocated_donations:
        remaining_amount = donation.amount

        for need in unmet_needs:
            need_remaining = need.amount_needed - need.amount_raised
            if need_remaining <= 0:
                continue

            allocation_amount = min(remaining_amount, need_remaining)
            
            # Update the need
            need.amount_raised += allocation_amount
            if need.amount_raised >= need.amount_needed:
                need.fulfilled = True
            need.save()

            # Update the donation
            donation.allocated_need = need
            donation.is_allocated = True
            donation.save()

            remaining_amount -= allocation_amount
            if remaining_amount <= 0:
                break
