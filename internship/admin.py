from django.contrib import admin
from .models import InternshipApplication, Attendance, InternshipPackage, Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'university_college', 'program_year', 'profile_photo')
    search_fields = ('user__username', 'full_name', 'university_college')

@admin.register(InternshipPackage)
class InternshipPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'period', 'seats')
    search_fields = ('name', 'category')

@admin.register(InternshipApplication)
class InternshipApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'university_college', 'program_year', 'gpa_or_marks', 'area_of_interest', 'status', 'submitted_at', 'resume', 'package')
    list_filter = ('university_college', 'gpa_or_marks', 'area_of_interest', 'status', 'package')
    search_fields = ('full_name', 'email', 'university_college', 'area_of_interest')
    actions = ['accept_applications', 'reject_applications']

    def accept_applications(self, request, queryset):
        queryset.update(status='Accepted')
    accept_applications.short_description = "Mark selected applications as Accepted"

    def reject_applications(self, request, queryset):
        queryset.update(status='Rejected')
    reject_applications.short_description = "Mark selected applications as Rejected"

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('intern', 'date', 'checkin_time')
    list_filter = ('date', 'intern__university_college', 'intern__program_year')
    search_fields = ('intern__full_name', 'intern__email') 