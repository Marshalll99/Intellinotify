# data_engine/models.py

from django.db import models
from urllib.parse import urlparse  # To extract the domain

class Notification(models.Model):
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=500)  # Consider using URLField if desired.
    created_at = models.DateTimeField(auto_now_add=True)  # Time of scraping
    published_at = models.DateTimeField(null=True, blank=True)  # Actual publishing date from website

    @property
    def base_url(self):
        parsed = urlparse(self.url)
        return parsed.netloc or "Unknown"

    def __str__(self):
        return self.title
