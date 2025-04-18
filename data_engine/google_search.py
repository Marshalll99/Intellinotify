# data_engine/google_search.py

import requests
from django.conf import settings

def google_search_top_url(domain):
    query = f"site:{domain} notifications"
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={settings.GOOGLE_API_KEY}&cx={settings.CSE_ID}"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            results = response.json().get("items", [])
            for item in results:
                link = item.get("link", "")
                if any(word in link.lower() for word in ["notification", "notice", "news", "updates"]):
                    print(f"✅ Best notification page found by search: {link}")
                    return link
            if results:
                print(f"🟠 No clean match, fallback to first result: {results[0]['link']}")
                return results[0]['link']
    except Exception as e:
        print(f"Google Search Error: {e}")

    print(f"❌ No result found, fallback to domain itself: {domain}")
    return f"https://{domain}" if not domain.startswith("http") else domain
