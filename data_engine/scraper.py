# data_engine/scraper.py

import requests
from bs4 import BeautifulSoup
from .models import Notification
from urllib.parse import urljoin
from datetime import datetime

def scrap(url):
    """
    Scrapes data from the given URL and saves notifications to the database.
    """
    notifications = []  # Initialize notifications list

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
        html_doc = response.content
        soup = BeautifulSoup(html_doc, 'html.parser')
        
        data = soup.find_all('a', title=True)
        count = 0
        for i, link in enumerate(data):
            title = link["title"]
            # Use urljoin to create an absolute URL from the base and the link's href.
            href = urljoin(base_url, link["href"])
            
            # Attempt to get a published date from an attribute (if available).
            # This assumes the element might have a 'data-published' attribute.
            published_date_str = link.get("data-published")  
            if published_date_str:
                try:
                    # Adjust the format as per the actual data format.
                    published_at = datetime.strptime(published_date_str, '%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    published_at = None
            else:
                published_at = None

            print(f"{i+1}. {title} - {href}")
            
            # Create and save a Notification instance with the published date (if found)
            Notification.objects.create(title=title, url=href, published_at=published_at)
            count += 1

        return f"Scraped and saved {count} notifications from {url}"
    
    elif url == "https://www.nta.ac.in/NoticeBoardArchive":
        base_url = "https://www.nta.ac.in"
        response = requests.get(url)
        html_doc = response.content
        soup = BeautifulSoup(html_doc, 'html.parser')
        data = soup.find_all('content', style="color:#012B55")
        notifications = data[:20]
    
    count = 0
    for item in notifications:
        notification_text = item.get_text(strip=True)
        a_tag = item.find('a', href = True)
        if a_tag:
            notification_href = a_tag['href']
            notification_href = urljoin(base_url, notification_href)
        else:
            notification_href = ""
        print(f"Notification: {notification_text}")
        if notification_href:
            print(f"Link: {notification_href}")
        
        # For this branch, no published date is scraped; it remains None.
        Notification.objects.create(title=notification_text, url=notification_href)
        count += 1

    return f"Scraped and saved {count} notifications from {url}"

