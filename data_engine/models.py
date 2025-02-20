# data_engine/models.py

from django.db import models
from urllib.parse import urlparse  # Add this import

class Notification(models.Model):
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=500)  # Use URLField if you prefer
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def base_url(self):
        parsed = urlparse(self.url)
        return parsed.netloc or "Unknown"

    def __str__(self):
        return self.title
