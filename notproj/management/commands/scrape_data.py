from django.core.management.base import BaseCommand
from Notifier.scraper import scrap

class Command(BaseCommand):
    help = 'Scrapes notifications from multiple websites and saves them to the database'

    def handle(self, *args, **options):
        urls = [
            "https://www.cusrinagar.edu.in/Notification/NotificationListPartial",
            "https://www.nta.ac.in/NoticeBoardArchive"
        ]

        for url in urls:
            result = scrap(url)
            self.stdout.write(self.style.SUCCESS(result))
