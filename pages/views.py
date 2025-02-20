from django.shortcuts import render

def home(request):
    return render(request, 'pages/home.html')

def notifications(request):
    # In the future, pass dynamic data to notifications page
    return render(request, 'pages/notifications.html')

