import json, re
from collections import defaultdict
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from .forms import CustomUserCreationForm
from data_engine.models import Notification, ScheduledNotificationRequest
from data_engine.ai_query import query_ai
from django.core.mail import send_mail
from data_engine.tasks import scrape_notification  # Celery task for scraping

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
            user = form.save()
            login(request, user)
            return redirect('home')
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

def chatbot_query(request):
    """Main chat view.
    AI first determines if the user is asking for a site notification.
    - If not, a normal chat response is returned.
    - Otherwise, we dispatch a Celery task to do scraping and summarization.
    """
    if request.method == "POST":
        # Parse the JSON body
        try:
            body_data = json.loads(request.body)
            user_message = body_data.get("query", "").strip()
        except json.JSONDecodeError:
            user_message = request.POST.get("query", "").strip()

        if not user_message:
            return JsonResponse({"response": "Please enter a message."}, status=400)

        # Step A: Ask AI if the user is requesting a notification.
        prompt_for_intent = f"""
        The user says: "{user_message}"
        
        If the user is requesting a website's notification info, 
        please output the domain or URL.
        Otherwise, output exactly "NO".
        """
        ai_decision = query_ai(prompt_for_intent).strip()

        if ai_decision.lower() == "no":
            # Step B: Normal chat – simply reply via AI.
            normal_chat_response = query_ai(user_message)
            return JsonResponse({"response": normal_chat_response})
        else:
            # Step C: The AI returned a domain/URL.
            domain_or_url = ai_decision
            # Optionally, extract a specific notification name from the user's message.
            notification_name = extract_notification_name(user_message)
            # Dispatch a background Celery task to scrape and process the requested notification.
            scrape_notification.delay(domain_or_url, notification_name)
            return JsonResponse({
                "response": f"Scraping for {domain_or_url} is in progress. We'll notify you if we find the notification: {notification_name}"
            })

    return JsonResponse({"error": "Invalid request"}, status=400)

def extract_notification_name(user_message):
    """
    Naively extracts text in quotes as the notification name.
    For example, if the user writes: 
        Check if "Admit Card 2025" is out on example.edu.
    it will return 'Admit Card 2025'.
    Otherwise, returns a default string.
    """
    match = re.search(r'"(.*?)"', user_message)
    if match:
        return match.group(1)
    return "Specific Notification"

def schedule_alert(user, domain_or_url):
    """Stores a record so that a background job can re-check periodically."""
    if user.is_authenticated:
        ScheduledNotificationRequest.objects.update_or_create(
            user=user,
            domain_or_url=domain_or_url,
            defaults={"active": True}
        )
    else:
        pass

def chat_view(request):
    return render(request, "pages/chat.html")
