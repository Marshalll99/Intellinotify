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
        # -- CUS Srinagar branch remains unchanged --
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
        
        # Get full titles from <content> tags with the given style.
        title_elements = soup.find_all('content', style="color:#012B55")
        # Get PDF links from <a> tags that end with .pdf.
        pdf_links = [a for a in soup.find_all('a', href=True) 
                     if a['href'].strip().lower().endswith('.pdf')]
        
        # Zip the two lists; assume that they correspond in order.
        notifications = list(zip(title_elements, pdf_links))[:20]
        
        count = 0
        for title_elem, link in notifications:
            # Use the text from the <content> tag for the notification title.
            title = title_elem.get_text(strip=True)
            # Get the href from the <a> tag and build an absolute URL.
            href = link.get('href', '').strip()
            absolute_href = urljoin(base_url, href) if href else ""
            
            print(f"Notification: {title}")
            print(f"Link: {absolute_href}")
            Notification.objects.create(title=title, url=absolute_href)
            count += 1

        return f"Scraped and saved {count} notifications from {url}"
