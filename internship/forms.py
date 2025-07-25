from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import InternshipApplication, Profile

UNIVERSITY_CHOICES = [
    ('', 'Select University'),
    ('TU', 'Tribhuvan University'),
    ('PU', 'Purbanchal University'),
    ('KU', 'Kathmandu University'),
    ('PoU', 'Pokhara University'),
    ('Other', 'Other'),
]
PROGRAM_CHOICES = [
    ('', 'Select Program'),
    ('BSc CSIT', 'BSc CSIT'),
    ('BE', 'Bachelor of Engineering'),
    ('BCA', 'Bachelor of Computer Application'),
    ('BBA', 'Bachelor of Business Administration'),
    ('BIT', 'Bachelor of Information Technology'),
    ('Other', 'Other'),
]
class UserRegisterForm(UserCreationForm):
    phone = forms.CharField(label='Phone Number', max_length=20, required=False)
    email = forms.EmailField(label='Email', required=False)
    full_name = forms.CharField(label='Full Name', max_length=100)
    university = forms.ChoiceField(label='University', choices=UNIVERSITY_CHOICES)
    college_name = forms.CharField(label='College Name', max_length=100)
    program = forms.ChoiceField(label='Program', choices=PROGRAM_CHOICES)
    year = forms.CharField(label='Year', max_length=20)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['phone', 'email', 'full_name', 'university', 'college_name', 'program', 'year', 'password1', 'password2']
    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get('phone')
        email = cleaned_data.get('email')
        if not phone and not email:
            raise forms.ValidationError('Please provide either a phone number or an email address.')
        return cleaned_data

class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_photo']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'university_college', 'program_year', 'profile_photo']

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'username']

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Phone or Email')

class InternshipApplicationForm(forms.ModelForm):
    class Meta:
        model = InternshipApplication
        fields = ['package', 'gpa_or_marks', 'area_of_interest', 'resume']
        widgets = {
            'package': forms.Select(attrs={'class': 'form-input'}),
            'gpa_or_marks': forms.TextInput(attrs={'class': 'form-input', 'placeholder': ' '}),
            'area_of_interest': forms.Select(attrs={'class': 'form-input'}),
            'resume': forms.ClearableFileInput(attrs={'class': 'form-input-file', 'accept': 'application/pdf'}),
        }

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            if not resume.name.lower().endswith('.pdf'):
                raise forms.ValidationError('Only PDF files are allowed.')
            if resume.size > 2.5 * 1024 * 1024:
                raise forms.ValidationError('File size must be under 2.5MB.')
        return resume 