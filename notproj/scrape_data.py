from django.core.management.base import BaseCommand
from data_engine.scraper import scrap

class Command(BaseCommand):
    help = 'Scrapes notifications from multiple websites and saves them to the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--site',
            type=str,
            choices=['cusrinagar', 'nta', 'all'],
            default='all',
            help="Choose which site to scrape: 'cusrinagar' (CUSR), 'nta' (NTA), or 'all' (both)."
        )

    def handle(self, *args, **options):
        site = options['site']
        
        url_map = {
            "cusrinagar": "https://www.cusrinagar.edu.in/Notification/NotificationListPartial",
            "nta": "https://www.nta.ac.in/NoticeBoardArchive"
        }
        
        if site == "all":
            urls = url_map.values()
        else:
            urls = [url_map[site]]

        for url in urls:
            result = scrap(url)
            self.stdout.write(self.style.SUCCESS(result))
