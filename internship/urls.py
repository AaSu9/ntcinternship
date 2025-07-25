from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('packages/', views.packages, name='packages'),
    path('apply/', views.apply, name='apply'),
    path('status/', views.status_view, name='status'),
    path('checkin/', views.checkin, name='checkin'),
    path('attendance/', views.attendance_calendar, name='attendance'),
    path('user-checkin/', views.user_checkin, name='user_checkin'),
    path('profile/', views.profile_update, name='profile_update'),
    path('quiz/', views.quiz_game, name='quiz_game'),
    path('quiz/leaderboard/<str:category>/', views.quiz_leaderboard, name='quiz_leaderboard'),
    path('tasks/', views.task_progress, name='task_progress'),
    path('tasks/upload/', views.upload_deliverable, name='upload_deliverable'),
    path('about-internship/', views.about_internship, name='about_internship'),
] 