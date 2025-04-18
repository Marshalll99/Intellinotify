
import re
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from data_engine.scraper import UniversalScraper #scrap UniversalScraper
from data_engine.ai_query import query_ai
from data_engine.models import ScheduledNotificationRequest

@shared_task
def scrape_notification(domain_or_url, notification_name):
    print(f"Scraping: {notification_name} from {domain_or_url}")

    scraper = UniversalScraper(domain_or_url, notification_name)
    html_text, pdf_links = scraper.run_scraper()
    print(f"→ Text length: {len(html_text)} chars, PDFs: {pdf_links}")

    snippet, pdf_url = scraper.find_notification(notification_name)

    if snippet:
        prompt = f"""
Below is a part of content scraped from {domain_or_url} related to user's query "{notification_name}":

\"\"\"
{snippet}
\"\"\"

Please do the following:
- If the information matches the notification "{notification_name}", write a short clear human-like summary.
- If the information is partially related, still write a helpful and positive update.
- Never say "NOT FOUND."
- Always be confident and encourage that updates are being monitored.

Respond only the final summary to show to the user.
"""
        print("→ Prompting AI for Summary...")
        summary = query_ai(prompt).strip()
        print("→ AI says:", summary)

        return summary if summary else "📢 No specific update found yet, but our system is monitoring it for you!"

    if pdf_url:
        return f"✅ Notification found inside PDF.\n\n🔗 PDF Link: {pdf_url}"

    return "📢 Notification not fully available yet, but monitoring has started."

@shared_task
def check_scheduled_requests():
    with transaction.atomic():
        for req in ScheduledNotificationRequest.objects.select_for_update().filter(active=True):
            res = scrape_notification(req.domain_or_url, req.notification_name)
            if res and not res.startswith("📢 Notification not fully available yet"):
                if req.user and req.user.email:
                    send_mail(
                        subject=f"Notification Found: {req.notification_name}",
                        message=res,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[req.user.email],
                        fail_silently=True,
                    )
                req.active = False
                req.save()
