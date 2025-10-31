from .models import DonationAllocation

def allocate_donations(donation, needs, children, allocated_by=None):
    allocations = []

    remaining_amount = float(donation.amount)

    for need in needs:
        if remaining_amount <= 0:
            break

        remaining_needed = float(need.amount_needed) - float(need.amount_raised)
        if remaining_needed <= 0:
            continue

        amount_to_allocate = min(remaining_amount, remaining_needed)
        allocation = DonationAllocation.objects.create(
            donation=donation,
            allocated_amount=amount_to_allocate,
            need=need,
            allocated_by=allocated_by
        )
        allocations.append(allocation)

        need.amount_raised = float(need.amount_raised) + amount_to_allocate
        need.fulfilled = need.amount_raised >= need.amount_needed
        need.save()

        remaining_amount -= amount_to_allocate

    if remaining_amount > 0 and children:
        per_child = remaining_amount / len(children)
        for child in children:
            allocation = DonationAllocation.objects.create(
                donation=donation,
                child=child,
                allocated_amount=per_child,
                allocated_by=allocated_by
            )
            allocations.append(allocation)
        remaining_amount = 0

    return allocations
