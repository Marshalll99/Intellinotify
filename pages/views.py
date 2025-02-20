from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'pages/home.html')

def notifications(request):
    return render(request, 'pages/notifications.html')

def signup(request):
    # Placeholder for signup functionality
    return HttpResponse("Signup page placeholder.")

def signin(request):
    # Placeholder for signin functionality
    return HttpResponse("Signin page placeholder.")
