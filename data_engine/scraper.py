import requests
from bs4 import BeautifulSoup
from .models import Notification

def scrap(url):
    """
    Scrapes data from the given URL and saves notifications to the database.
    """
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
