from celery import shared_task
from django.conf import settings
from data_engine.google_search import get_google_search_results
from data_engine.scraper import UniversalScraper
from data_engine.ai_query import query_ai
from django.core.mail import send_mail
from data_engine.models import ScheduledNotificationRequest
from django.db import transaction

@shared_task
def scrape_notification(domain_or_url, notification_name):
    """
    1) Google search for 'domain_or_url + notification'
    2) Scrape best link
    3) Pass content to AI to see if the specific notification_name is there
    4) Return the snippet if found
    """
    # 1) Google Search
    results = get_google_search_results(domain_or_url)
    if not results:
        return ""

    best_url = results[0]["link"]
    scraper = UniversalScraper(best_url)
    scraped_content = scraper.run_scraper()

    # 2) Let AI see if it contains the user’s desired notification
    prompt = f"""
    The user wants the specific notification: '{notification_name}' 
    from the domain: {domain_or_url}.
    Below is the scraped text:
    {scraped_content}

    If you find that specific notification info, output it exactly.
    If not found, output 'NOT FOUND'.
    """
    snippet = query_ai(prompt).strip()
    return snippet

@shared_task
def check_scheduled_requests():
    """
    Called periodically (e.g. Celery beat) to see if previously-unfound 
    notifications are now available.
    """
    with transaction.atomic():
        active_reqs = ScheduledNotificationRequest.objects.select_for_update().filter(active=True)
        for req in active_reqs:
            snippet = scrape_notification(domain_or_url=req.domain_or_url, 
                                          notification_name=req.notification_name)
            if snippet and snippet != "NOT FOUND":
                # We found the notification
                if req.user and req.user.email:
                    send_mail(
                        subject=f"Notification Found: {req.notification_name}",
                        message=f"We found your notification:\n\n{snippet}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[req.user.email],
                        fail_silently=True,
                    )
                req.active = False
                req.save()
