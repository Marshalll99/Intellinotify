from collections import defaultdict
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import CustomUserCreationForm 
from django.contrib.auth import login, authenticate
from django.http import HttpResponse
from data_engine.models import Notification
from django.http import JsonResponse
from data_engine.google_search import get_google_search_results
from data_engine.scraper import UniversalScraper
from data_engine.ai_query import query_ai

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
            user = form.save(commit=True)  
            login(request, user)  
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

def chatbot_query(request):
    """Handles chatbot queries, triggers Google Search, scraping, and AI processing."""
    if request.method == "POST":
        query = request.POST.get("query", "").strip()
        if not query:
            return JsonResponse({"error": "Query cannot be empty"}, status=400)

        # 1️⃣ Generate Google Search results
        search_results = get_google_search_results(query)
        if not search_results:
            return JsonResponse({"error": "No search results found."}, status=400)

        best_url = search_results[0]["link"]  # Pick top result

        # 2️⃣ Scrape the best result
        scraper = UniversalScraper(best_url)
        scraped_content = scraper.run_scraper()

        # 3️⃣ AI Summarization
        final_response = query_ai(f"Summarize the following information: {scraped_content}")

        return JsonResponse({"response": final_response})

    return JsonResponse({"error": "Invalid request"}, status=400)

def chat_view(request):
    return render(request, "pages/chat.html")
