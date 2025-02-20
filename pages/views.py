from collections import defaultdict
from django.shortcuts import render
from data_engine.models import Notification
from django.http import HttpResponse

def home(request):
    return render(request, 'pages/home.html')

def notifications(request):
    notifications_qs = Notification.objects.all().order_by('-created_at')
    grouped_notifications = defaultdict(list)
    for notification in notifications_qs:
        grouped_notifications[notification.base_url].append(notification)
    # Sort groups by the base URL (alphabetically)
    grouped_notifications = dict(sorted(grouped_notifications.items()))
    return render(request, 'pages/notifications.html', {
        'grouped_notifications': grouped_notifications
    })

def signup(request):
    # Placeholder for signup functionality
    return HttpResponse("Signup page placeholder.")

def signin(request):
    # Placeholder for signin functionality
    return HttpResponse("Signin page placeholder.")
