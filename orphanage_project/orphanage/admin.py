from django.contrib import admin
from .models import Child,Donor
from .models import Allocation
@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('name', 'admission_date', 'gender')  
    search_fields = ('name',)  


admin.site.register(Donor)

from django.contrib import admin

from .models import NeedDonation

@admin.register(NeedDonation)
class NeedDonationAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount_needed', 'amount_raised', 'fulfilled')
    list_filter = ('fulfilled',)
    search_fields = ('category',)

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from django.utils.html import format_html

from orphanage.allocation_algorithm import allocate_donations
@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = ('child', 'donation', 'allocated_amount', 'date')
    
    change_list_template = "admin/allocation_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("run-allocation/", self.admin_site.admin_view(self.run_allocation), name="run_allocation"),
        ]
        return custom_urls + urls

    def run_allocation(self, request):
        allocate_donations()
        self.message_user(request, "Donations allocated successfully!", level=messages.SUCCESS)
        return redirect("..")
