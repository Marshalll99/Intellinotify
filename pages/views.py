import json, re, threading
from collections import defaultdict
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.http import JsonResponse
from .forms import CustomUserCreationForm
from data_engine.models import Notification, ScheduledNotificationRequest
from data_engine.ai_query import query_ai
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

def run_full_scraper(domain, notification_name, user):
    """
    Full heavy scraping happening here without blocking chatbot.
    """
    from data_engine.models import ScheduledNotificationRequest
    from django.core.mail import send_mail
    from django.conf import settings

    summary = scrape_notification(domain, notification_name)

    if summary and summary != "❌ Notification not found.":
        req = ScheduledNotificationRequest.objects.filter(
            user=user,
            domain_or_url=domain,
            notification_name=notification_name,
            active=True
        ).first()
        if req:
            req.active = False
            req.save()

        if user and user.email:
            send_mail(
                f"✅ Notification Found: {notification_name}",
                summary,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )

def chatbot_query(request):
    if request.method == "POST":
        try:
            body_data = json.loads(request.body)
            user_message = body_data.get("query", "").strip()
        except json.JSONDecodeError:
            user_message = request.POST.get("query", "").strip()

        if not user_message:
            return JsonResponse({"response": "Please enter a message."}, status=400)

        prompt_for_intent = f"""
You are an assistant that must decide between two modes:
- For normal chat, output exactly: {{"intent": "chat", "answer": "your normal answer"}}
- If the user is asking for a specific website notification (for example, "Check if 'Admit Card 2025' is out on example.edu"), 
  output exactly: {{"intent": "notification", "domain": "example.edu", "notification_name": "Admit Card 2025"}}
Do not output any extra text.
User message: "{user_message}"
"""
        ai_intent_raw = query_ai(prompt_for_intent).strip()
        print(f"AI Intent: {ai_intent_raw}")

        try:
            ai_intent = json.loads(ai_intent_raw)
        except Exception as e:
            fallback_answer = query_ai(user_message)
            print(f"AI Intent Parsing Error: {e}")
            return JsonResponse({"response": fallback_answer})

        if ai_intent.get("intent") == "chat":
            print(f"AI Chat Response: {ai_intent.get('answer')}")
            return JsonResponse({"response": ai_intent.get("answer", "I'm here to help!")})

        elif ai_intent.get("intent") == "notification":
            domain = ai_intent.get("domain", "").strip()
            notification_name = ai_intent.get("notification_name", "Specific Notification").strip()
            print(f"AI Notification Domain: {domain}")
            print(f"AI Notification Name: {notification_name}")

            if not domain:
                fallback_answer = query_ai(user_message)
                return JsonResponse({"response": fallback_answer})

            # Start full scraping in a background thread immediately
            if request.user.is_authenticated:
                ScheduledNotificationRequest.objects.update_or_create(
                    user=request.user,
                    domain_or_url=domain,
                    notification_name=notification_name,
                    defaults={"active": True}
                )

                threading.Thread(target=run_full_scraper, args=(domain, notification_name, request.user)).start()

            else:
                # Unauthenticated users won't receive email notifications
                threading.Thread(target=run_full_scraper, args=(domain, notification_name, None)).start()

            # Immediate polite fallback
            fallback_message = (
                f"📢 We’re checking for '{notification_name}' on {domain} right now. "
                "Please stay tuned — we'll notify you once the update is found!"
            )
            return JsonResponse({"response": fallback_message})

        else:
            fallback_answer = query_ai(user_message)
            return JsonResponse({"response": fallback_answer})

    return JsonResponse({"error": "Invalid request"}, status=400)

def chat_view(request):
    return render(request, "pages/chat.html")
