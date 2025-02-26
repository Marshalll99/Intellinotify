from collections import defaultdict
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import CustomUserCreationForm 
from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from data_engine.models import Notification

def home(request):
    return render(request, 'pages/home.html')

def notifications(request):
    notifications_qs = Notification.objects.all().order_by('-created_at')
    grouped_notifications = defaultdict(list)
    for notification in notifications_qs:
        grouped_notifications[notification.base_url].append(notification)
    grouped_notifications = dict(sorted(grouped_notifications.items()))
    return render(request, 'pages/notifications.html', {
        'grouped_notifications': grouped_notifications
    })

def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            print("DEBUG: Email entered by user:", form.cleaned_data.get("email"))  # Debugging
            user = form.save(commit=True)  # Save with commit=True
            login(request, user)  # Log the user in after signup
            return redirect('home')
        else:
            print("DEBUG: Form errors:", form.errors)  # Debugging
    else:
        form = CustomUserCreationForm()
    return render(request, 'pages/signup.html', {"form": form})

def signin(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'pages/signin.html', {"form": form})
