from django.db import models
from django.contrib.auth import get_user_model
from urllib.parse import urlparse

class NotificationPageMapping(models.Model):
    domain = models.CharField(max_length=255, unique=True)
    notification_page_url = models.URLField()

    def __str__(self):
        return f"{self.domain} -> {self.notification_page_url}"

class Notification(models.Model):
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    @property
    def base_url(self):
        parsed = urlparse(self.url)
        return parsed.netloc or "Unknown"

    def __str__(self):
        return self.title

class RecentEmail(models.Model):
    sender = models.EmailField(default="default@example.com")
    subject = models.CharField(max_length=255, default="No Subject")
    received_at = models.DateTimeField(auto_now_add=True)
    email_content = models.TextField()
    response_content = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Email from {self.sender} at {self.received_at}"

class ScraperChoice(models.Model):
    url = models.URLField(unique=True)
    tool = models.CharField(
        max_length=20,
        choices=[("scrapy", "Scrapy"), ("playwright", "Playwright"), ("requests", "Requests")]  # Added "requests" properly
    )
    last_attempted = models.DateTimeField(auto_now=True)  # When last tried
    last_success = models.DateTimeField(null=True, blank=True)  # When last success
    fail_count = models.IntegerField(default=0)  #How many failures happened

    def __str__(self):
        return f"{self.url} -> {self.tool}"

class ScheduledNotificationRequest(models.Model):
    """
    Tracks user requests for a specific notification on a site.
    e.g. user wants "Admit Card 2025" from example.edu
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True)
    domain_or_url = models.CharField(max_length=255)
    notification_name = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.domain_or_url}] => {self.notification_name} (Active: {self.active})"
