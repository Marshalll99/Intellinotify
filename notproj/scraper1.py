import requests
from bs4 import BeautifulSoup
from .models import Notification
from urllib.parse import urljoin

def scrap(url):
    """
    Scrapes data from the given URL and saves notifications to the database.
    """
    notifications = []  # Ensure 'notifications' is always initialized
    
    if url == "https://www.cusrinagar.edu.in/Notification/NotificationListPartia":
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
        # print("Response Content (first 500 chars):", response.content[:500])  # Print preview of response content
        # print(f"Status Code: {response.status_code}")
        # print(f"Response Headers: {response.headers}")
        # print(f"Response Content (first 1000 chars): {response.content[:1000]}")
        html_doc = response.content
        soup = BeautifulSoup(html_doc, 'html.parser')
        
        data = soup.find_all('a', title=True)
        count = 0
        for i, link in enumerate(data):
            title = link["title"]
            href = base_url + link["href"]
            # Print for debugging purposes
            print(f"{i+1}. {title} - {href}")
            
            # Create and save a Notification instance
            Notification.objects.create(title=title, url=href)
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
        a_tag = item.find('a')
        if a_tag and a_tag.has_attr('href'):
            notification_href = a_tag['href']
            notification_href = urljoin(base_url, notification_href)
        else:
            notification_href = ""  #
        print(f"Notification: {notification_text}")
        if notification_href:
            print(f"Link: {notification_href}")
        
        Notification.objects.create(title=notification_text, url=notification_href)
        count += 1

    return f"Scraped and saved {count} notifications from {url}"
        # for item in data:
        #     print ( item.text)
        # return "Scraped and saved notifications from NTA"
        # # print (data)
        # # return "Scraped and saved notifications from NTA"
    
# scrap("https://www.nta.ac.in/NoticeBoardArchive")