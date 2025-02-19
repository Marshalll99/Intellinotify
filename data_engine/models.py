# data_engine/models.py

from django.db import models

class Notification(models.Model):
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=500)  # Use URLField if you prefer
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
