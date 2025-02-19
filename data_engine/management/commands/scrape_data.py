from django.core.management.base import BaseCommand
from data_engine.scraper import scrap

class Command(BaseCommand):
    help = 'Scrapes notifications from the website and saves them to the database'

    def handle(self, *args, **options):
        url = "https://www.cusrinagar.edu.in/Notification/NotificationListPartial"
        result = scrap(url)
        self.stdout.write(self.style.SUCCESS(result))
