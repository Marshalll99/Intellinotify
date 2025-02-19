import requests
from bs4 import BeautifulSoup
from .models import Notification

def scrap(url):
    """
    Scrapes data from the given URL and saves notifications to the database.
    """
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
        html_doc = response.content
        soup = BeautifulSoup(html_doc, 'html.parser')
        
        data = soup.find_all('a', title=True)
        count = 0
        for i, link in enumerate(data):
            title = link["title"]
            href = link["href"]
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
        for item in data:
            print ( item.text)
        return "Scraped and saved notifications from NTA"
        # print (data)
        # return "Scraped and saved notifications from NTA"
    
scrap("https://www.nta.ac.in/NoticeBoardArchive")