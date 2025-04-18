# populate_notification_pages.py

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')  # adjust if your settings module path is different
django.setup()

from data_engine.models import NotificationPageMapping

# Predefined mappings you want to populate
notification_mappings = [
    {"domain": "cusrinagar.edu.in", "notification_page_url": "https://www.cusrinagar.edu.in/Notification/NotificationListPartial"},
    {"domain": "nta.ac.in", "notification_page_url": "https://www.nta.ac.in/NoticeBoardArchive"},
    {"domain": "jeemain.nta.nic.in", "notification_page_url": "https://jeemain.nta.nic.in/"},
    {"domain": "neet.nta.nic.in", "notification_page_url": "https://neet.nta.nic.in/"},
    # ➡️ Add more as needed
]

def populate_mappings():
    for mapping in notification_mappings:
        obj, created = NotificationPageMapping.objects.get_or_create(
            domain=mapping["domain"],
            defaults={"notification_page_url": mapping["notification_page_url"]}
        )
        if created:
            print(f"✅ Created new mapping for {mapping['domain']}")
        else:
            print(f"ℹ️ Mapping for {mapping['domain']} already exists.")

if __name__ == "__main__":
    populate_mappings()
