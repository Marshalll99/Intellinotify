from django.contrib import admin
from .models import Notification, RecentEmail

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "published_at")

@admin.register(RecentEmail)
class RecentEmailAdmin(admin.ModelAdmin):
    list_display = ("subject", "sender", "received_at")
