import requests
from bs4 import BeautifulSoup
import time

# Sky is not the limit, mind is the limit.


def scrap(url):
    base_url = "https://www.cusrinagar.edu.in"
    # n_href = ""
    form_data = {
        'parameter[PageInfo][PageNumber]': 1,
        'parameter[PageInfo][PageSize]': 50,
        'parameter[PageInfo][DefaultOrderByColumn]': 'CreatedOn',
        'parameter[SortInfo][ColumnName]': '',
        'parameter[SortInfo][OrderBy]': 1,
        'otherParam1': ''
    }
    html_doc = requests.post(url, data=form_data).content
    soup = BeautifulSoup(html_doc, 'html.parser')
    data = soup.find_all('a', title=True)
    for i in range(len(data)):
        print(f"\n{i+1}. ", data[i]["title"], data[i]["href"])  # type: ignore
        n_href = data[i]["href"]  # type: ignore

    #! Pdf save karny k liye

    # n_url = base_url + n_href  # type: ignore
    # with open("n_url.pdf", "wb") as f:
    #     f.write(requests.get(n_url).content)

    return f"scraped data for {url}"


if __name__ == "__main__":
    url = "https://www.cusrinagar.edu.in/Notification/NotificationListPartial"
    # total_time_taken = 0

    # for i in range(10):
    #     start_time = time.time()
    #     data = scrap(url)
    #     end_time = time.time()
    #     time_taken = end_time - start_time
    #     print(f"Time taken to scrape: {time_taken} seconds")
    #     total_time_taken += time_taken

    # print(f"Average time taken to scrape: {total_time_taken/10} seconds")
    data = scrap(url)
    print(data)
    
