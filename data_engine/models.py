from django.db import models
from urllib.parse import urlparse  

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
