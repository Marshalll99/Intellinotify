from data_engine.models import ScheduledNotificationRequest
from data_engine.scraper import UniversalScraper
from data_engine.ai_query import query_ai
from django.core.mail import send_mail
from django.conf import settings

def check_scheduled_requests():
    """Cron job or Celery task that runs 2x a day to see if any notifications are now available."""
    active_reqs = ScheduledNotificationRequest.objects.filter(active=True)

    for req in active_reqs:
        # Attempt scraping
        domain_or_url = req.domain_or_url
        # For background checks, we skip google search or do it again? 
        # We'll do it again in case the best link changed.
        # But let's be minimal: just scrape the domain directly:
        scraper = UniversalScraper(domain_or_url)
        content = scraper.run_scraper()

        if not content.strip():
            # Not found anything new. We'll keep it active.
            continue

        # Summarize with AI
        summary_prompt = f"""
        The user wants notifications from {domain_or_url}.
        This is the newly scraped content:
        {content}
        If you see relevant notifications, summarize them. 
        Otherwise, say 'No relevant notifications yet.'
        """
        summary = query_ai(summary_prompt)

        # Decide if summary suggests we found something
        if "No relevant notifications yet." in summary:
            # Not found. Keep active
            continue

        # Otherwise, we found something. Email the user
        # Make sure your Django email settings are set up in settings.py
        user_email = req.user.email if req.user else None
        if user_email:
            send_mail(
                subject=f"New Notification from {domain_or_url}",
                message=summary,
                from_email=settings.DEFAULT_FROM_EMAIL,  # or any valid email
                recipient_list=[user_email],
                fail_silently=True
            )

        # Mark it inactive so we don't keep emailing
        req.active = False
        req.save()
