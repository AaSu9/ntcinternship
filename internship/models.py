from django.db import models
from django.contrib.auth.models import User

class InternshipPackage(models.Model):
    CATEGORY_CHOICES = [
        ('Technical', 'Technical'),
        ('Software', 'Software'),
        ('Admin/HR', 'Admin/HR'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    eligibility = models.TextField()
    period = models.CharField(max_length=100)
    seats = models.PositiveIntegerField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    university_college = models.CharField(max_length=100)
    program_year = models.CharField(max_length=100)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    def __str__(self):
        return self.full_name

class InternshipApplication(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]
    UNIVERSITY_CHOICES = [
        ('TU', 'Tribhuvan University'),
        ('KU', 'Kathmandu University'),
        ('PU', 'Pokhara University'),
        ('PoU', 'Purbanchal University'),
        ('Other', 'Other'),
    ]
    PROGRAM_CHOICES = [
        ('BE Computer', 'BE Computer'),
        ('BE Electronics', 'BE Electronics'),
        ('BSc CSIT', 'BSc CSIT'),
        ('BCA', 'BCA'),
        ('BIT', 'BIT'),
        ('Other', 'Other'),
    ]
    INTEREST_CHOICES = [
        ('Networking', 'Networking'),
        ('Software Development', 'Software Development'),
        ('Telecom', 'Telecom'),
        ('Cyber Security', 'Cyber Security'),
        ('Other', 'Other'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    package = models.ForeignKey(InternshipPackage, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    university_college = models.CharField(max_length=100, choices=UNIVERSITY_CHOICES)
    program_year = models.CharField(max_length=100, choices=PROGRAM_CHOICES)
    gpa_or_marks = models.CharField(max_length=20)
    area_of_interest = models.CharField(max_length=100, choices=INTEREST_CHOICES)
    resume = models.FileField(upload_to='resumes/')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.email})"

class Attendance(models.Model):
    intern = models.ForeignKey(InternshipApplication, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(auto_now_add=True)
    checkin_time = models.TimeField(auto_now_add=True)

    class Meta:
        unique_together = ('intern', 'date')
        ordering = ['-date', '-checkin_time']

    def __str__(self):
        return f"{self.intern.full_name} - {self.date}" 