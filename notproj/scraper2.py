import requests
from bs4 import BeautifulSoup
from .models import Notification
from urllib.parse import urljoin
from datetime import datetime
import os

def scrap(url):
    """
    Scrapes data from the given URL and saves notifications to the database.
    """
    if url == "https://www.cusrinagar.edu.in/Notification/NotificationListPartial":
        base_url = "https://www.cusrinagar.edu.in"
        form_data = {
            'parameter[PageInfo][PageNumber]': 1,
            'parameter[PageInfo][PageSize]': 50,
            'parameter[PageInfo][DefaultOrderByColumn]': 'CreatedOn',
            'parameter[SortInfo][ColumnName]': '',
            'parameter[SortInfo][OrderBy]': 1,
            'otherParam1': ''
        }
        
        response = requests.post(url, data=form_data)
        soup = BeautifulSoup(response.content, 'html.parser')
        data = soup.find_all('a', title=True)
        count = 0
        for i, link in enumerate(data):
            title = link["title"]
            href = urljoin(base_url, link["href"])
            published_date_str = link.get("data-published")  
            if published_date_str:
                try:
                    published_at = datetime.strptime(published_date_str, '%Y-%m-%d %H:%M:%S')
                except Exception:
                    published_at = None
            else:
                published_at = None

            print(f"{i+1}. {title} - {href}")
            Notification.objects.create(title=title, url=href, published_at=published_at)
            count += 1

        return f"Scraped and saved {count} notifications from {url}"
    
    elif url == "https://www.nta.ac.in/NoticeBoardArchive":
        base_url = "https://www.nta.ac.in"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for all <a> tags with href that ends with .pdf (assumed to be notifications)
        pdf_links = [a for a in soup.find_all('a', href=True) if a['href'].strip().lower().endswith('.pdf')]
        
        # If no PDF links are found, log a message for debugging
        if not pdf_links:
            print("No PDF links found using href filter; trying alternative approach.")
            pdf_links = soup.find_all('a', href=True)
        
        notifications = pdf_links[:20]  # Limit to first 20 notifications
        
        count = 0
        for item in notifications:
            notification_text = item.get_text(strip=True)
            notification_href = item.get('href', '').strip()
            if notification_href:
                # Build absolute URL from base_url and relative href.
                absolute_href = urljoin(base_url, notification_href)
            else:
                absolute_href = ""
            
            # If no title is provided, use the filename as a fallback.
            if not notification_text:
                notification_text = os.path.basename(absolute_href)
            
            print(f"Notification: {notification_text}")
            print(f"Link: {absolute_href}")
            
            Notification.objects.create(title=notification_text, url=absolute_href)
            count += 1

        return f"Scraped and saved {count} notifications from {url}"
