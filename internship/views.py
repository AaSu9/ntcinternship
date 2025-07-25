from django.shortcuts import render, redirect
from .forms import InternshipApplicationForm
from .models import InternshipApplication
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from .models import Attendance
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserLoginForm, ProfilePhotoForm
from .models import Profile
from .models import InternshipPackage
from calendar import monthrange
from datetime import date
import qrcode
from io import BytesIO
import base64
from django.core.files.uploadedfile import InMemoryUploadedFile
from .forms import ProfileUpdateForm, UserUpdateForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import QuizScore, TaskDeliverable
import random
from django.views.decorators.http import require_POST

def homepage(request):
    latest_application = None
    if request.user.is_authenticated:
        latest_application = request.user.internshipapplication_set.order_by('-submitted_at').first()
    return render(request, 'internship/homepage.html', {'latest_application': latest_application})

@csrf_protect
def apply(request):
    submitted = False
    application_id = None
    if not request.user.is_authenticated:
        return redirect('login')
    package_id = request.GET.get('package')
    initial = {}
    form_kwargs = {}
    package_name = None
    if package_id:
        initial['package'] = package_id
        form_kwargs['initial'] = initial
        try:
            package_obj = InternshipPackage.objects.get(pk=package_id)
            package_name = str(package_obj)
        except InternshipPackage.DoesNotExist:
            package_name = "Selected Package"
    if request.method == 'POST':
        form = InternshipApplicationForm(request.POST, request.FILES, **form_kwargs)
        if form.is_valid():
            profile = Profile.objects.get(user=request.user)
            application = form.save(commit=False)
            application.user = request.user
            application.full_name = profile.full_name
            application.email = request.user.email
            application.phone_number = request.user.username
            application.university_college = profile.university_college
            application.program_year = profile.program_year
            if package_id:
                application.package_id = package_id
            application.save()
            submitted = True
            application_id = application.id
            messages.success(request, 'Your application has been submitted successfully!')
            return render(request, 'internship/apply.html', {
                'form': InternshipApplicationForm(),
                'submitted': submitted,
                'application_id': application_id,
                'locked_package': package_id,
                'locked_package_name': package_name
            })
        else:
            messages.error(request, 'Please correct the errors below and resubmit the form.')
    else:
        form = InternshipApplicationForm(**form_kwargs)
    return render(request, 'internship/apply.html', {
        'form': form,
        'submitted': submitted,
        'application_id': application_id,
        'locked_package': package_id,
        'locked_package_name': package_name
    })

@csrf_protect
def checkin(request):
    checked_in = False
    already_checked_in = False
    not_found = False
    intern = None
    if request.method == 'POST':
        query = request.POST.get('query')
        intern = None
        if query.isdigit():
            intern = InternshipApplication.objects.filter(id=query, status='Accepted').first()
        if not intern:
            intern = InternshipApplication.objects.filter(email=query, status='Accepted').order_by('-submitted_at').first()
        if intern:
            today = timezone.now().date()
            if Attendance.objects.filter(intern=intern, date=today).exists():
                already_checked_in = True
            else:
                Attendance.objects.create(intern=intern)
                checked_in = True
        else:
            not_found = True
    return render(request, 'internship/checkin.html', {'checked_in': checked_in, 'already_checked_in': already_checked_in, 'not_found': not_found})

@csrf_protect
def status_view(request):
    status = None
    not_found = False
    attendance_count = None
    last_checkin = None
    if request.method == 'POST':
        query = request.POST.get('query')
        application = None
        if query.isdigit():
            application = InternshipApplication.objects.filter(id=query).first()
        if not application:
            application = InternshipApplication.objects.filter(email=query).order_by('-submitted_at').first()
        if application:
            status = application.status
            attendance_count = application.attendances.count()
            last_att = application.attendances.order_by('-date', '-checkin_time').first()
            last_checkin = last_att.date if last_att else None
        else:
            not_found = True
    return render(request, 'internship/status.html', {'status': status, 'not_found': not_found, 'attendance_count': attendance_count, 'last_checkin': last_checkin})

@csrf_protect
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # Set username to phone if provided, else email
            phone = form.cleaned_data.get('phone')
            email = form.cleaned_data.get('email')
            full_name = form.cleaned_data.get('full_name')
            university_college = form.cleaned_data.get('university_college')
            program_year = form.cleaned_data.get('program_year')
            user = form.save(commit=False)
            if phone:
                user.username = phone
            else:
                user.username = email
            user.email = email or ''
            user.save()
            # Create profile
            Profile.objects.create(
                user=user,
                full_name=full_name,
                university_college=university_college,
                program_year=program_year
            )
            login(request, user)
            return redirect('homepage')
    else:
        form = UserRegisterForm()
    return render(request, 'internship/register.html', {'form': form})

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('homepage')
    else:
        form = UserLoginForm()
    return render(request, 'internship/login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return redirect('homepage')

def packages(request):
    packages = InternshipPackage.objects.all().order_by('category', 'name')
    grouped = {'Technical': [], 'Software': [], 'Admin/HR': []}
    for pkg in packages:
        grouped[pkg.category].append(pkg)
    return render(request, 'internship/packages.html', {'grouped': grouped})

@login_required
def attendance_calendar(request):
    # Find the user's accepted application
    application = InternshipApplication.objects.filter(user=request.user, status='Accepted').first()
    if not application:
        return render(request, 'internship/attendance.html', {'not_accepted': True})
    today = date.today()
    year, month = today.year, today.month
    days_in_month = monthrange(year, month)[1]
    attendance_days = set(application.attendances.filter(date__year=year, date__month=month).values_list('date', flat=True))
    calendar_days = []
    for day in range(1, days_in_month + 1):
        d = date(year, month, day)
        calendar_days.append({'date': d, 'present': d in attendance_days})
    return render(request, 'internship/attendance.html', {
        'calendar_days': calendar_days,
        'month': today.strftime('%B'),
        'year': year,
        'not_accepted': False,
    })

@login_required
def dashboard(request):
    latest_application = request.user.internshipapplication_set.order_by('-submitted_at').first()
    # Prefer accepted application if it exists
    application = InternshipApplication.objects.filter(user=request.user, status='Accepted').order_by('-submitted_at').first()
    if not application:
        application = latest_application
    profile = Profile.objects.filter(user=request.user).first()
    context = {'application': application, 'profile': profile, 'latest_application': latest_application}
    # --- Add category-specific tasks ---
    def get_category_tasks(category):
        if category == 'Technical':
            return [
                'Design and implement a network topology for a simulated telecom environment.',
                'Configure and secure a Cisco router and switch for a branch office.',
                'Analyze network traffic using Wireshark and report on anomalies.',
                'Develop a disaster recovery plan for NTC’s core network.',
                'Present a seminar on 5G technology and its impact on telecom infrastructure.'
            ]
        elif category == 'Software':
            return [
                'Build a Django web app to manage internal NTC projects.',
                'Develop a REST API for telecom service provisioning.',
                'Automate daily report generation using Python scripts.',
                'Create a dashboard for real-time monitoring of telecom KPIs.',
                'Integrate SMS gateway functionality into an existing application.'
            ]
        elif category == 'Admin/HR':
            return [
                'Design an onboarding process for new NTC interns.',
                'Conduct a survey and analyze employee satisfaction data.',
                'Draft a policy for remote work and present to HR.',
                'Organize a virtual team-building event and report outcomes.',
                'Prepare a compliance checklist for HR documentation.'
            ]
        else:
            return []
    # --- End tasks function ---
    if not application:
        context['show_apply'] = True
    elif application.status == 'Pending':
        context['pending'] = True
    elif application.status == 'Rejected':
        context['rejected'] = True
    elif application.status == 'Accepted':
        # Handle profile photo upload
        if request.method == 'POST' and 'profile_photo' in request.FILES:
            form = ProfilePhotoForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
        else:
            form = ProfilePhotoForm(instance=profile)
        # QR code generation (encode all user details except photo)
        qr_data = f"""
NTC-INTERNSHIP-ID: {request.user.id}
Name: {profile.full_name}
Email: {request.user.email}
Phone: {request.user.username}
University: {profile.university_college}
Program/Year: {profile.program_year}
"""
        qr = qrcode.QRCode(box_size=4, border=2)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_img_b64 = base64.b64encode(buffer.getvalue()).decode()
        # Benefits and attendance for accepted interns
        today = date.today()
        year, month = today.year, today.month
        days_in_month = monthrange(year, month)[1]
        attendance_days = set(application.attendances.filter(date__year=year, date__month=month).values_list('date', flat=True))
        # Build mini calendar structure
        import calendar
        cal = calendar.Calendar()
        month_days = list(cal.itermonthdates(year, month))
        calendar_weeks = []
        week = []
        for d in month_days:
            if d.month != month:
                week.append(None)
            else:
                week.append({
                    'date': d,
                    'present': d in attendance_days,
                    'is_past': d < today,
                })
            if len(week) == 7:
                calendar_weeks.append(week)
                week = []
        if week:
            calendar_weeks.append(week)
        # Attendance check-in for user
        can_checkin = not application.attendances.filter(date=today).exists()
        total_present = sum(1 for week in calendar_weeks for day in week if day and day['present'])
        total_absent = sum(1 for week in calendar_weeks for day in week if day and day['is_past'] and not day['present'])
        context.update({
            'accepted': True,
            'calendar_weeks': calendar_weeks,
            'month': today.strftime('%B'),
            'year': year,
            'package': application.package,
            'benefits': [
                {'icon': '🍱', 'title': 'Lunch', 'desc': 'Free lunch provided daily at NTC canteen.'},
                {'icon': '📶', 'title': 'Data/Voice Pack', 'desc': 'Monthly data and voice pack for all interns.'},
                {'icon': '💼', 'title': 'Certificate', 'desc': 'Internship completion certificate from NTC.'},
            ],
            'profile_photo_form': form,
            'qr_img_b64': qr_img_b64,
            'can_checkin': can_checkin,
            'total_present': total_present,
            'total_absent': total_absent,
            'tasks': get_category_tasks(application.package.category if application.package else None),
        })
    return render(request, 'internship/dashboard.html', context)

@login_required
def user_checkin(request):
    # Only allow check-in for accepted interns
    application = InternshipApplication.objects.filter(user=request.user, status='Accepted').first()
    if not application:
        return redirect('dashboard')
    today = date.today()
    already_checked_in = application.attendances.filter(date=today).exists()
    if request.method == 'POST' and not already_checked_in:
        Attendance.objects.create(intern=application)
        messages.success(request, 'Attendance marked successfully for today!')
        return redirect('dashboard')
    return render(request, 'internship/user_checkin.html', {'already_checked_in': already_checked_in})

@login_required
def profile_update(request):
    profile = Profile.objects.get(user=request.user)
    if request.method == 'POST':
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if p_form.is_valid() and u_form.is_valid():
            p_form.save()
            u_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('dashboard')
    else:
        p_form = ProfileUpdateForm(instance=profile)
        u_form = UserUpdateForm(instance=request.user)
    return render(request, 'internship/profile_update.html', {'p_form': p_form, 'u_form': u_form})

# --- Quiz Game View ---
@login_required
def quiz_game(request):
    application = InternshipApplication.objects.filter(user=request.user, status='Accepted').order_by('-submitted_at').first()
    if not application or not application.package:
        return redirect('dashboard')
    category = application.package.category
    quiz_data = {
        'Technical': [
            {'q': 'What does a router do in a network?', 'options': ['Routes data packets', 'Stores files', 'Prints documents', 'Encrypts emails'], 'a': 0, 'explanation': 'A router directs data packets between networks.'},
            {'q': 'Which protocol is used for secure web browsing?', 'options': ['HTTP', 'FTP', 'SSH', 'HTTPS'], 'a': 3, 'explanation': 'HTTPS encrypts data for secure web communication.'},
            {'q': 'What is the main benefit of 5G over 4G?', 'options': ['Lower cost', 'Higher speed and lower latency', 'More colors', 'Bigger screens'], 'a': 1, 'explanation': '5G offers much higher speed and lower latency than 4G.'},
        ],
        'Software': [
            {'q': 'Which framework is used for Python web development?', 'options': ['React', 'Django', 'Laravel', 'Spring'], 'a': 1, 'explanation': 'Django is a popular Python web framework.'},
            {'q': 'What does REST stand for?', 'options': ['Really Easy Simple Test', 'Representational State Transfer', 'Random Event Synchronous Task', 'Remote Execution Service Tool'], 'a': 1, 'explanation': 'REST stands for Representational State Transfer.'},
            {'q': 'Which HTTP method is used to update data?', 'options': ['GET', 'POST', 'PUT', 'DELETE'], 'a': 2, 'explanation': 'PUT is used to update data in RESTful APIs.'},
        ],
        'Admin/HR': [
            {'q': 'What is the main goal of onboarding?', 'options': ['Increase sales', 'Integrate new employees', 'Reduce taxes', 'Buy equipment'], 'a': 1, 'explanation': 'Onboarding helps new employees integrate into the organization.'},
            {'q': 'Which law protects employee rights in Nepal?', 'options': ['Consumer Act', 'Labour Act', 'Education Act', 'Banking Act'], 'a': 1, 'explanation': 'The Labour Act protects employee rights in Nepal.'},
            {'q': 'What is a key benefit of team-building?', 'options': ['Lower salaries', 'Better teamwork', 'Longer hours', 'More paperwork'], 'a': 1, 'explanation': 'Team-building improves teamwork and collaboration.'},
        ],
    }
    # Retake logic
    if request.GET.get('retake') == '1':
        request.session.pop('quiz_score', None)
        request.session.pop('quiz_completed', None)
        request.session.pop('quiz_order', None)
        request.session.pop('quiz_option_order', None)
    # Randomize questions and options
    questions = quiz_data.get(category, [])
    if 'quiz_order' not in request.session:
        order = list(range(len(questions)))
        random.shuffle(order)
        request.session['quiz_order'] = order
    else:
        order = request.session['quiz_order']
    randomized_questions = [questions[i].copy() for i in order]
    # Randomize options for each question
    if 'quiz_option_order' not in request.session:
        option_orders = []
        for q in randomized_questions:
            opts = list(enumerate(q['options']))
            random.shuffle(opts)
            option_orders.append([i for i, _ in opts])
            q['options'] = [opt for _, opt in opts]
            # Update answer index
            q['a'] = option_orders[-1].index(q['a'])
        request.session['quiz_option_order'] = option_orders
    else:
        option_orders = request.session['quiz_option_order']
        for q, opt_order in zip(randomized_questions, option_orders):
            q['options'] = [q['options'][i] for i in opt_order]
            q['a'] = opt_order.index(q['a'])
    score = request.session.get('quiz_score', 0)
    completed = request.session.get('quiz_completed', False)
    feedback = []
    if request.method == 'POST':
        answers = [int(request.POST.get(f'q{i}', -1)) for i in range(len(randomized_questions))]
        score = sum(1 for i, q in enumerate(randomized_questions) if answers[i] == q['a'])
        feedback = [answers[i] == q['a'] for i, q in enumerate(randomized_questions)]
        request.session['quiz_score'] = score
        request.session['quiz_completed'] = True
        completed = True
        QuizScore.objects.update_or_create(user=request.user, category=category, defaults={'score': score})
    zipped_qf = list(zip(randomized_questions, feedback)) if feedback else None
    return render(request, 'internship/quiz_game.html', {
        'questions': randomized_questions,
        'score': score,
        'completed': completed,
        'category': category,
        'feedback': feedback,
        'zipped_qf': zipped_qf,
        'retake_url': '/quiz/?retake=1',
    })

# --- Quiz Leaderboard View ---
@login_required
def quiz_leaderboard(request, category):
    top_scores = QuizScore.objects.filter(category=category).select_related('user').order_by('-score', 'taken_at')[:10]
    return render(request, 'internship/quiz_leaderboard.html', {
        'category': category,
        'top_scores': top_scores,
    })

# --- Task Progress Tracker (AJAX) ---
@csrf_exempt
@login_required
def task_progress(request):
    application = InternshipApplication.objects.filter(user=request.user, status='Accepted').order_by('-submitted_at').first()
    if not application or not application.package:
        return JsonResponse({'error': 'No accepted application.'}, status=403)
    category = application.package.category
    def get_category_tasks(category):
        if category == 'Technical':
            return [
                {'title': 'Design and implement a network topology for a simulated telecom environment.', 'details': 'Use Cisco Packet Tracer or GNS3. Submit your topology file.'},
                {'title': 'Configure and secure a Cisco router and switch for a branch office.', 'details': 'Document your configuration and upload screenshots.'},
                {'title': 'Analyze network traffic using Wireshark and report on anomalies.', 'details': 'Upload your analysis report (PDF).'},
                {'title': 'Develop a disaster recovery plan for NTC’s core network.', 'details': 'Submit a written plan (PDF or DOCX).'},
                {'title': 'Present a seminar on 5G technology and its impact on telecom infrastructure.', 'details': 'Upload your presentation slides.'}
            ]
        elif category == 'Software':
            return [
                {'title': 'Build a Django web app to manage internal NTC projects.', 'details': 'Upload your code (ZIP) and a short demo video.'},
                {'title': 'Develop a REST API for telecom service provisioning.', 'details': 'Submit API documentation and code.'},
                {'title': 'Automate daily report generation using Python scripts.', 'details': 'Upload your script and a sample report.'},
                {'title': 'Create a dashboard for real-time monitoring of telecom KPIs.', 'details': 'Upload dashboard screenshots and code.'},
                {'title': 'Integrate SMS gateway functionality into an existing application.', 'details': 'Submit integration code and a test report.'}
            ]
        elif category == 'Admin/HR':
            return [
                {'title': 'Design an onboarding process for new NTC interns.', 'details': 'Upload your process document.'},
                {'title': 'Conduct a survey and analyze employee satisfaction data.', 'details': 'Submit your survey results and analysis.'},
                {'title': 'Draft a policy for remote work and present to HR.', 'details': 'Upload your policy draft.'},
                {'title': 'Organize a virtual team-building event and report outcomes.', 'details': 'Submit event plan and feedback summary.'},
                {'title': 'Prepare a compliance checklist for HR documentation.', 'details': 'Upload your checklist.'}
            ]
        else:
            return []
    tasks = get_category_tasks(category)
    if 'task_progress' not in request.session:
        request.session['task_progress'] = [False] * len(tasks)
    progress = request.session['task_progress']
    if request.method == 'POST':
        idx = int(request.POST.get('task_idx', -1))
        if 0 <= idx < len(tasks):
            progress[idx] = not progress[idx]
            request.session['task_progress'] = progress
    percent = int(100 * sum(progress) / len(tasks)) if tasks else 0
    # Add deliverable info
    deliverables = [None] * len(tasks)
    for i in range(len(tasks)):
        d = TaskDeliverable.objects.filter(user=request.user, category=category, task_index=i).order_by('-uploaded_at').first()
        if d:
            deliverables[i] = {'file_url': d.file.url, 'uploaded_at': d.uploaded_at.strftime('%Y-%m-%d %H:%M')}
    return JsonResponse({'tasks': tasks, 'progress': progress, 'percent': percent, 'deliverables': deliverables})

# --- Task Deliverable Upload View ---
@require_POST
@login_required
def upload_deliverable(request):
    application = InternshipApplication.objects.filter(user=request.user, status='Accepted').order_by('-submitted_at').first()
    if not application or not application.package:
        return JsonResponse({'error': 'No accepted application.'}, status=403)
    category = application.package.category
    idx = int(request.POST.get('task_idx', -1))
    file = request.FILES.get('file')
    if file and 0 <= idx < 5:
        TaskDeliverable.objects.update_or_create(user=request.user, category=category, task_index=idx, defaults={'file': file})
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid upload.'}, status=400)

def about_internship(request):
    return render(request, 'internship/about_internship.html') 