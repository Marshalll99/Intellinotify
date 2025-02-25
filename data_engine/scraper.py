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
        # --- CUS Srinagar branch (unchanged) ---
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
        rows = soup.select("tbody tr")  # Select all table rows in the tbody
        count = 0
        for i, row in enumerate(rows):
            tds = row.find_all("td")
            # Extract the posting date from the second <td>
            posting_date_str = tds[1].get_text(strip=True)
            try:
                published_at = datetime.strptime(posting_date_str, "%d-%B-%Y")
            except Exception:
                published_at = None
            
            # Extract the title and URL from the <a> in the third <td>
            link = tds[2].find("a", title=True)
            if link:
                title = link["title"]
                href = urljoin(base_url, link["href"])
            else:
                title = tds[0].get_text(strip=True)
                href = base_url

            print(f"{i+1}. {title} - {href}")
            Notification.objects.create(title=title, url=href, published_at=published_at)
            count += 1

        return f"Scraped and saved {count} notifications from {url}"

    
    elif url == "https://www.nta.ac.in/NoticeBoardArchive":
        base_url = "https://www.nta.ac.in"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get full titles from <content> tags with the specific style.
        title_elements = soup.find_all('content', style="color:#012B55")
        # Get PDF links from <a> tags that end with .pdf.
        pdf_links = [a for a in soup.find_all('a', href=True) if a['href'].strip().lower().endswith('.pdf')]
        # Pair titles and links (assuming they correspond in order) and limit to 20.
        notifications = list(zip(title_elements, pdf_links))[:20]
    
        count = 0
        for title_elem, link in notifications:
            # Extract the full notification title.
            title = title_elem.get_text(strip=True)
            # Extract the href and build an absolute URL.
            href = link.get('href', '').strip()
            absolute_href = urljoin(base_url, href) if href else ""
            
            # Extract published date from the URL.
            # Expected URL pattern: .../Notice_20250223164251.pdf
            published_at = None
            if absolute_href:
                try:
                    # Find the last underscore and the ".pdf" portion.
                    underscore_index = absolute_href.rfind('_')
                    dot_index = absolute_href.lower().rfind('.pdf')
                    if underscore_index != -1 and dot_index != -1 and dot_index > underscore_index:
                        # Get the numeric part after '_' and before '.pdf'
                        date_time_str = absolute_href[underscore_index+1:dot_index]  # e.g. "20250223164251"
                        # Extract only the first 8 digits representing YYYYMMDD.
                        date_str = date_time_str[:8]
                        published_at = datetime.strptime(date_str, '%Y%m%d')
                except Exception as e:
                    published_at = None
            
            print(f"Notification: {title}")
            print(f"Link: {absolute_href}")
            print(f"Published Date: {published_at}")
            
            Notification.objects.create(title=title, url=absolute_href, published_at=published_at)
            count += 1

        return f"Scraped and saved {count} notifications from {url}"
