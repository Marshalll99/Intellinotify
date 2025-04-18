from django.contrib import admin
from .models import Notification, RecentEmail, ScraperChoice, ScheduledNotificationRequest, NotificationPageMapping

admin.site.register(NotificationPageMapping)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "published_at")

@admin.register(RecentEmail)
class RecentEmailAdmin(admin.ModelAdmin):
    list_display = ("subject", "sender", "received_at")

@admin.register(ScraperChoice)
class ScraperChoiceAdmin(admin.ModelAdmin):
    list_display = ("url", "tool")

@admin.register(ScheduledNotificationRequest)
class ScheduledNotificationRequestAdmin(admin.ModelAdmin):
    list_display = ("domain_or_url", "notification_name", "active")
    list_filter = ("active",)
    search_fields = ("domain_or_url", "notification_name")
    date_hierarchy = "created_at"                