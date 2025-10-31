from django.urls import path
from orphanage.views import  donor_views, admin_views, adopter_views
from orphanage.views.public_views import public_dashboard
from orphanage.views import public_views
from orphanage.views import donor_views
from .views.public_views import public_children, child_detail

app_name = 'orphanage'

urlpatterns = [
    path('', public_dashboard, name='public_dashboard'),
    path('children/', public_children, name='public_children'),
    path('child/<int:id>/', child_detail, name='child_detail'),
path('donor/register/', donor_views.donor_register, name='donor_register'),
    path('donor/login/', donor_views.donor_login, name='donor_login'),
    path('donor/logout/', donor_views.donor_logout, name='donor_logout'),
    path('donor/dashboard/', donor_views.donor_dashboard, name='donor_dashboard'),
    path('donor/donate/', donor_views.donate, name='donate'),
    path('donor/my-allocations.csv', donor_views.donor_allocation_report_csv, name='donor_allocation_report_csv'),
    path('donor/make-donation/', donor_views.make_donation_view, name='make_donation'),
    path('donor/recommendations/', donor_views.donor_recommendation_view, name='donor_recommendations'),
    path('donor/make-donation/<int:need_id>/', donor_views.make_donation_view, name='make_donation_for_need'),
    path('child/<int:pk>/', public_views.child_detail, name='public_child_detail'),
    path('donor/recommend/', donor_views.donor_recommendation_view, name='donor_recommendation'),  # ✅ add this
    path('donor/donate/<int:need_id>/', donor_views.donate_to_need, name='donate_to_need'),
    path('donor/allocate-donation/<int:donation_id>/', donor_views.allocate_existing_donation, name='allocate_existing_donation'),
    path("allocate/", admin_views.run_allocation, name="run_allocation"),
    path("allocations/", admin_views.view_allocations, name="view_allocations"),        
    path('admin/child/<int:pk>/', admin_views.admin_child_detail, name='admin_child_detail'),
    path('admin/login/', admin_views.admin_login, name='admin_login'),
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),    
    path('admin/children/', admin_views.admin_children_list, name='admin_children_list'),
    path('admin/child/<int:pk>/edit/', admin_views.admin_edit_child, name='admin_edit_child'),
    path('admin/child/<int:pk>/delete/', admin_views.admin_delete_child, name='admin_delete_child'),
    path('admin/logout/', admin_views.admin_logout, name='admin_logout'),
    path('admin/staff/', admin_views.staff_list, name='staff_list'),
    path('admin/add_staff/', admin_views.add_staff, name='add_staff'),
    path('admin/add_child/', admin_views.add_child, name='add_child'),
    path('admin/staff_allocations/', admin_views.staff_allocation_list, name='staff_allocation_list'),
    path('admin/allocate_donations/', admin_views.allocate_donations_view, name='allocate_donations'),
    path('admin/needs/', admin_views.need_list, name='need_list'),
    path('admin/add-need/', admin_views.add_need, name='add_need'),
    path('admin/expenses/', admin_views.expense_list, name='expense_list'),
    path('admin/expenses/add/', admin_views.add_expense, name='add_expense'),
    path('admin/allocate_donations_ajax/', admin_views.allocate_donations_ajax, name='allocate_donations_ajax'),
    path('allocation_results/', admin_views.allocation_results, name='allocation_results'),
    path('admin/donation-allocations/', admin_views.admin_donation_allocations, name='admin_donation_allocations'),
    path("allocate/<int:donation_id>/", admin_views.allocate_view, name="allocate_view"),
    path('admin/donations/<int:donation_id>/allocate-child/', admin_views.admin_allocate_donation_to_child, name='admin_allocate_donation_to_child'),
    path('admin/adopters/', admin_views.admin_adopters_list, name='admin_adopters_list'),
    path('admin/adopter/<int:adopter_id>/', admin_views.admin_adopter_detail, name='admin_adopter_detail'),
    path('admin/adopter/<int:adopter_id>/approve/', admin_views.admin_approve_adopter, name='admin_approve_adopter'),
    path('admin/adoption-applications/', admin_views.admin_adoption_applications, name='admin_adoption_applications'),
    path('admin/review-application/<int:application_id>/', admin_views.admin_review_application, name='admin_review_application'),

    # Adopter URLs
    path('adopter/register/', adopter_views.adopter_register, name='adopter_register'),
    path('adopter/login/', adopter_views.adopter_login, name='adopter_login'),
    path('adopter/logout/', adopter_views.adopter_logout, name='adopter_logout'),
    path('adopter/dashboard/', adopter_views.adopter_dashboard, name='adopter_dashboard'),
    path('adopter/browse-children/', adopter_views.browse_children, name='browse_children'),
    path('adopter/child/<int:child_id>/', adopter_views.child_detail_adopter, name='child_detail_adopter'),
    path('adopter/express-interest/<int:child_id>/', adopter_views.express_interest, name='express_interest'),
    path('adopter/apply-adoption/<int:child_id>/', adopter_views.apply_for_adoption, name='apply_for_adoption'),
    path('adopter/my-applications/', adopter_views.my_applications, name='my_applications'),
    path('adopter/my-interests/', adopter_views.my_interests, name='my_interests'),
    path('adopter/update-profile/', adopter_views.update_profile, name='update_profile'),

]
