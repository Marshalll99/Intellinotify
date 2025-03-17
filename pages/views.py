import json, re
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

def chatbot_query(request):
    """
    This view processes user queries. It first asks the AI to classify the intent
    in structured JSON. If the AI determines that the user wants a specific website 
    notification (e.g. "Admit Card 2025" from example.edu), we try to retrieve a full 
    summary immediately via our Celery task. If a valid summary is found, it is returned.
    Otherwise, we schedule an alert so that when the notification becomes available,
    the user will be notified via email.
    """
    if request.method == "POST":
        try:
            body_data = json.loads(request.body)
            user_message = body_data.get("query", "").strip()
        except json.JSONDecodeError:
            user_message = request.POST.get("query", "").strip()

        if not user_message:
            return JsonResponse({"response": "Please enter a message."}, status=400)

        # Step 1: Ask AI for intent using a structured JSON prompt.
        prompt_for_intent = f"""
You are an assistant that must decide between two modes:
- For normal chat, output exactly: {{"intent": "chat", "answer": "your normal answer"}}
- If the user is asking for a specific website notification (for example, "Check if 'Admit Card 2025' is out on example.edu"), 
  output exactly: {{"intent": "notification", "domain": "example.edu", "notification_name": "Admit Card 2025"}}
Do not output any extra text.
User message: "{user_message}"
"""
        ai_intent_raw = query_ai(prompt_for_intent).strip()

        try:
            ai_intent = json.loads(ai_intent_raw)
        except Exception as e:
            # Fallback to normal chat if parsing fails.
            fallback_answer = query_ai(user_message)
            return JsonResponse({"response": fallback_answer})

        if ai_intent.get("intent") == "chat":
            return JsonResponse({"response": ai_intent.get("answer", "I'm here to help!")})
        elif ai_intent.get("intent") == "notification":
            domain = ai_intent.get("domain", "").strip()
            notification_name = ai_intent.get("notification_name", "Specific Notification").strip()
            if not domain:
                fallback_answer = query_ai(user_message)
                return JsonResponse({"response": fallback_answer})
            # Attempt immediate scraping by calling our Celery task and waiting up to 30 seconds.
            try:
                summary = scrape_notification.delay(domain, notification_name).get(timeout=30)
            except Exception as e:
                summary = ""

            if summary and summary != "NOT FOUND":
                # Return the summary as the response.
                return JsonResponse({"response": summary})
            else:
                # If nothing valid was retrieved, store a scheduled alert.
                if request.user.is_authenticated:
                    ScheduledNotificationRequest.objects.update_or_create(
                        user=request.user,
                        domain_or_url=domain,
                        notification_name=notification_name,
                        defaults={"active": True}
                    )
                    return JsonResponse({
                        "response": (
                            f"We couldn't procure '{notification_name}' from {domain} right now. "
                            "We'll monitor the site and email you once the complete information is available."
                        )
                    })
                else:
                    return JsonResponse({
                        "response": (
                            f"We couldn't procure '{notification_name}' from {domain} at the moment. "
                            "Please provide your email so we can notify you when it becomes available."
                        )
                    })
        else:
            # Fallback if the AI's response doesn't match expected structure.
            fallback_answer = query_ai(user_message)
            return JsonResponse({"response": fallback_answer})

    return JsonResponse({"error": "Invalid request"}, status=400)

def chat_view(request):
    return render(request, "pages/chat.html")
