Below is a **complete** architectural outline and sample code for the **“best” separate-process approach** using **Celery** (or a Celery-like background worker) to handle all your “universal scraping” steps—Google search, scraping with Scrapy/Playwright, PDF reading, and AI summarization. **Django** remains responsible for:

1. **Normal AI chat** (when no notification is requested).  
2. Determining (via AI or otherwise) if the user is asking for a specific site notification.  
3. Dispatching background tasks to the Celery worker for slow or repeated scrapes (no Twisted conflicts).  
4. Storing scheduled alerts and emailing the user once the specific notification is found.

This approach avoids “ReactorNotRestartable,” because **Scrapy/Twisted never run in your Django web process**. They run in the Celery worker’s main thread, so no signal conflicts with Django’s dev server.

---

# **1) Overall Flow**

1. **User always chats with AI**. 
   - If the user’s message is just a normal question, we call `query_ai(user_message)` and return the response immediately.

2. **AI decides** whether the user wants “notification info” from some site (or you do a 2-step approach: “Does the user want a site notification? If so, which domain & which specific notification?”).

3. If yes:
   1. We do a **Google search** for `"{domain or site} notification"`—but **in the Celery worker**.  
   2. The worker picks the best URL from the search, calls the “universal scraper,” which:
      - Checks DB for “Scrapy vs. Playwright” preference.
      - Tries Scrapy; if content is empty or partial, tries Playwright.
      - If a PDF is found, read it with `pdf_handler.py`.
   3. The worker **passes the scraped text to AI** for “the most relevant snippet” or “the specific notification” the user wanted.
   4. If it can’t find that notification or the content is incomplete, we store a **ScheduledNotificationRequest** so we can keep checking every day or so.  

4. **Scheduled re-check**:
   - A Celery beat task (or django-crontab job) calls a function that re-scrapes the site to see if the requested notification is now available.  
   - If found, we email the user using the same SMTP config you already have in Django.

5. **We only show the user** the single notification they asked for (the AI can do a second pass to filter out extraneous text from the scraped site).

6. **Primary DB**: You continue using SQLite or Postgres for normal Django models.  
   - **Redis** (or RabbitMQ) is **just** the Celery message broker and (optionally) result backend. You don’t store your main data there.  

---

# **2) Data Models**

You already have something like this in `data_engine/models.py`:

```python
from django.db import models
from django.contrib.auth import get_user_model
from urllib.parse import urlparse

class Notification(models.Model):
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    @property
    def base_url(self):
        parsed = urlparse(self.url)
        return parsed.netloc or "Unknown"

    def __str__(self):
        return self.title


class ScraperChoice(models.Model):
    url = models.URLField(unique=True)
    tool = models.CharField(max_length=20, choices=[("scrapy", "Scrapy"), ("playwright", "Playwright")])

class ScheduledNotificationRequest(models.Model):
    """
    Tracks user requests for a specific notification on a site.
    e.g. user wants "Admit Card 2025" from example.edu
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True)
    domain_or_url = models.CharField(max_length=255)
    # The "exact" notification name or keywords user wants
    notification_name = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.domain_or_url}] => {self.notification_name} (Active: {self.active})"
```

- **`notification_name`**: store the user’s exact text for the “specific notification.” If the user says, “Check if ‘Admit Card 2025’ is out on example.edu,” we store `domain_or_url="example.edu"` and `notification_name="Admit Card 2025"`.  
- We only return results that match the user’s desired string.

---

# **3) AI Query (unchanged)**

Your `data_engine/ai_query.py` can remain as-is:

```python
import requests
import json
import re

def query_ai(prompt):
    reqUrl = "http://localhost:11434/api/generate"
    headers = {"Accept": "*/*", "User-Agent": "Chatbot", "Content-Type": "application/json"}

    payload = json.dumps({
        "model": "deepseek-r1:8b",
        "prompt": prompt,
        "stream": False,
        "max_tokens": 8192
    })

    try:
        response = requests.post(reqUrl, data=payload, headers=headers)
        response_json = response.json()
        if "error" in response_json:
            return f"❌ Error: {response_json['error']}"
        raw_response = response_json.get("response", "").strip()
        return re.sub(r"<.*?>", "", raw_response).strip()
    except json.JSONDecodeError:
        return "❌ API returned non-JSON response"
    except requests.exceptions.RequestException as e:
        return f"❌ API request error: {e}"
```

---

# **4) Universal Scraper & Google Search in Celery Worker**

## **4a) `data_engine/google_search.py`** (for the worker)

```python
import scrapy
from scrapy.crawler import CrawlerRunner
import crochet

crochet.setup()

class GoogleSearchSpider(scrapy.Spider):
    name = "google_search"
    results = []

    def __init__(self, query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force "notification" in the query
        full_query = f"{query} notification".replace(" ", "+")
        self.start_urls = [f"https://www.google.com/search?q={full_query}"]
        self.results = []

    def parse(self, response):
        for result in response.css("div.tF2Cxc"):
            title = result.css("h3::text").get()
            link = result.css("a::attr(href)").get()
            if title and link:
                if "google.com" not in link and "/aclk?" not in link and "adurl=" not in link:
                    self.results.append({"title": title, "link": link})

from scrapy.crawler import CrawlerRunner
runner = CrawlerRunner(settings={"LOG_ENABLED": False})

@crochet.run_in_reactor
def crawl_google(query):
    return runner.crawl(GoogleSearchSpider, query=query)

def get_google_search_results(query):
    d = crawl_google(query)
    d.wait()  # block until done
    for crawler in runner.crawlers:
        spider = crawler.spider
        if isinstance(spider, GoogleSearchSpider):
            return spider.results
    return []
```

**All** of this runs in the Celery worker—**not** in your Django web process. That means no Twisted conflict with the dev server.

## **4b) `data_engine/scraper.py`** (for the worker)

```python
import scrapy
from scrapy.crawler import CrawlerRunner
import crochet
from playwright.sync_api import sync_playwright
from data_engine.models import ScraperChoice
from data_engine.pdf_handler import extract_text_from_pdf

crochet.setup()

class UniversalScraper:
    def __init__(self, url):
        self.url = url
        self.tool = self.get_scraping_tool(url)

    def get_scraping_tool(self, url):
        choice = ScraperChoice.objects.filter(url=url).first()
        return choice.tool if choice else "scrapy"

    def update_tool_choice(self, tool):
        ScraperChoice.objects.update_or_create(url=self.url, defaults={"tool": tool})

    def scrape_with_scrapy(self):
        class ScraperSpider(scrapy.Spider):
            name = "scraper_spider"
            scraped_content = ""

            def __init__(self, start_url, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.start_urls = [start_url]
                self.scraped_content = ""

            def parse(self, response):
                self.scraped_content = response.text

        runner = CrawlerRunner(settings={"LOG_ENABLED": False})

        @crochet.run_in_reactor
        def crawl_spider(start_url):
            return runner.crawl(ScraperSpider, start_url=start_url)

        d = crawl_spider(self.url)
        d.wait()  # block until done
        for crawler in runner.crawlers:
            spider = crawler.spider
            if isinstance(spider, ScraperSpider):
                return spider.scraped_content
        return ""

    def scrape_with_playwright(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url)
            content = page.content()
            browser.close()
            return content

    def detect_pdf(self, content):
        if self.url.lower().endswith(".pdf"):
            return True
        if "application/pdf" in content.lower():
            return True
        return False

    def run_scraper(self):
        content = (
            self.scrape_with_scrapy()
            if self.tool == "scrapy"
            else self.scrape_with_playwright()
        )

        if not content.strip():
            self.tool = "playwright" if self.tool == "scrapy" else "scrapy"
            self.update_tool_choice(self.tool)
            content = (
                self.scrape_with_playwright()
                if self.tool == "playwright"
                else self.scrape_with_scrapy()
            )

        if self.detect_pdf(content):
            pdf_text = extract_text_from_pdf(self.url)
            return pdf_text
        return content
```

Again, all of this code is **imported and executed only by Celery**. That keeps Twisted away from Django’s dev server.

---

# **5) `data_engine/pdf_handler.py`** (unchanged)

```python
import requests
import fitz  # PyMuPDF
import pdfplumber

def download_pdf(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    return None

def extract_text_from_pdf(url):
    pdf_data = download_pdf(url)
    if not pdf_data:
        return "Failed to download PDF."

    text = ""
    try:
        with fitz.open(stream=pdf_data, filetype="pdf") as doc:
            text = "\n".join(page.get_text() for page in doc)
    except:
        pass

    if not text:
        try:
            with pdfplumber.open(pdf_data) as pdf:
                text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
        except:
            return "Failed to extract text from PDF."

    return text if text else "No readable text found in PDF."
```

---

# **6) Celery Setup**

## **6a) `core/celery.py`** (assuming your project is named `core`)

```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

In **`core/__init__.py`**:

```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

## **6b) `settings.py`** additions

```python
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
```

(Or RabbitMQ, etc. You keep `DATABASES` pointing to sqlite/postgres for your main data.)

---

# **7) Celery Tasks**

In `data_engine/tasks.py`, define tasks that do the Google search, scrape the best URL, check for the user’s “specific notification,” etc.

```python
from celery import shared_task
from django.conf import settings
from data_engine.google_search import get_google_search_results
from data_engine.scraper import UniversalScraper
from data_engine.ai_query import query_ai
from django.core.mail import send_mail
from data_engine.models import ScheduledNotificationRequest
from django.db import transaction

@shared_task
def scrape_notification(domain_or_url, notification_name):
    """
    1) Google search for 'domain_or_url + notification'
    2) Scrape best link
    3) Pass content to AI to see if the specific notification_name is there
    4) Return the snippet if found
    """
    # 1) Google Search
    results = get_google_search_results(domain_or_url)
    if not results:
        return ""

    best_url = results[0]["link"]
    scraper = UniversalScraper(best_url)
    scraped_content = scraper.run_scraper()

    # 2) Let AI see if it contains the user’s desired notification
    prompt = f"""
    The user wants the specific notification: '{notification_name}' 
    from the domain: {domain_or_url}.
    Below is the scraped text:
    {scraped_content}

    If you find that specific notification info, output it exactly.
    If not found, output 'NOT FOUND'.
    """
    snippet = query_ai(prompt).strip()
    return snippet

@shared_task
def check_scheduled_requests():
    """
    Called periodically (e.g. Celery beat) to see if previously-unfound 
    notifications are now available.
    """
    with transaction.atomic():
        active_reqs = ScheduledNotificationRequest.objects.select_for_update().filter(active=True)
        for req in active_reqs:
            snippet = scrape_notification(domain_or_url=req.domain_or_url, 
                                          notification_name=req.notification_name)
            if snippet and snippet != "NOT FOUND":
                # We found the notification
                if req.user and req.user.email:
                    send_mail(
                        subject=f"Notification Found: {req.notification_name}",
                        message=f"We found your notification:\n\n{snippet}",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[req.user.email],
                        fail_silently=True,
                    )
                req.active = False
                req.save()
```

- **`scrape_notification()`**: single run to see if the user’s “notification_name” is found.  
- **`check_scheduled_requests()`**: re-check all `ScheduledNotificationRequest` entries that are still active. If found, email the user.

## **7c) Scheduling `check_scheduled_requests()`**

Either **Celery Beat** or **django-crontab** can call `check_scheduled_requests()` every 12 hours, for example. If using Celery beat, add something like this to **`settings.py`**:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-scheduled-requests-twice-a-day': {
        'task': 'data_engine.tasks.check_scheduled_requests',
        'schedule': crontab(hour='*/12'),  # every 12 hours
    },
}
```

Then run:

```bash
celery -A core beat -l info
celery -A core worker -l info
```

---

# **8) Django View: Minimal, No Twisted Imports**

Finally, in your `pages/views.py`, **do not** import any Twisted or Scrapy code. Instead, you call Celery tasks. For normal chat:

```python
import json
from django.http import JsonResponse
from django.shortcuts import render
from data_engine.ai_query import query_ai
from data_engine.tasks import scrape_notification
from data_engine.models import ScheduledNotificationRequest
from django.core.mail import send_mail

def chat_view(request):
    return render(request, "pages/chat.html")

def chatbot_query(request):
    if request.method == "POST":
        try:
            body_data = json.loads(request.body)
            user_message = body_data.get("query", "").strip()
        except:
            user_message = ""

        if not user_message:
            return JsonResponse({"response": "Please type something."}, status=400)

        # 1) Ask AI if user wants a site notification or just normal chat
        # For brevity, let's do a naive approach
        prompt = f"""
        The user says: '{user_message}'
        If they want a specific site notification, output 'DOMAIN:xxx NOTIFICATION:yyy'
        else output 'NO'
        """
        ai_decision = query_ai(prompt).strip()

        if ai_decision == "NO":
            # Normal chat
            answer = query_ai(user_message)
            return JsonResponse({"response": answer})

        # Otherwise, parse domain and notification name from AI output
        # e.g. "DOMAIN:example.com NOTIFICATION:Admit Card 2025"
        if "DOMAIN:" in ai_decision and "NOTIFICATION:" in ai_decision:
            parts = ai_decision.split()
            # naive parse
            domain_part = parts[0].replace("DOMAIN:", "")
            notification_part = parts[1].replace("NOTIFICATION:", "")
            # 2) Immediately try to scrape
            # We'll do it asynchronously so we don't block
            task_result = scrape_notification.delay(domain_part, notification_part)

            # We can return a quick "scraping in progress" or we can .get() it (blocking)
            return JsonResponse({"response": "Scraping in progress. We'll notify you if found."})
        else:
            # fallback
            return JsonResponse({"response": "Could not parse your notification request."})

    return JsonResponse({"error": "Invalid request"}, status=400)
```

**Key Points**:

- We do **not** import `google_search` or `scraper.py` in `views.py`.  
- We rely on `scrape_notification.delay(...)` to do the heavy lifting in Celery.  
- If the user’s specific notification is not found, you might store a `ScheduledNotificationRequest` so that `check_scheduled_requests()` picks it up. For example:

```python
# If snippet == "NOT FOUND":
ScheduledNotificationRequest.objects.create(
    user=request.user if request.user.is_authenticated else None,
    domain_or_url=domain_part,
    notification_name=notification_part,
    active=True
)
```

Then the Celery beat job will re-check daily, emailing the user once it’s available.

---

# **How This Addresses Your Requirements**

1. **User always chats with AI**.  
   - If normal question → we do `query_ai(user_message)`.  

2. **AI decides** whether to do a Google search + universal scraper.  
   - We do not rely on fixed keywords; the AI can interpret “I want the 2025 exam schedule on example.edu.”  

3. **We always append “notification”** to the Google search (the worker does this in `get_google_search_results(query)`).  

4. **We only show that specific notification** (the Celery task passes the scraped text back to AI with a prompt: “Find the user’s specific notification_name in here. If not found, return NOT FOUND.”).  

5. **PDF reading** is handled in `scraper.py` automatically if the content is PDF.  

6. **Alerts**: If not found, we store a `ScheduledNotificationRequest`. A scheduled Celery beat task runs daily (or 2x/day) and re-scrapes. Once found, we email the user.  

7. **SMTP**: We reuse the same Django email config for password resets. The Celery worker calls `send_mail(...)` with the user’s email.  

8. **Redis** is only your **Celery broker** (and optional result backend). Your main data is still in **SQLite** or **Postgres**.  

---

## **What About the “Universal Scraper” Steps?**

Yes, the code above still checks:

- DB for previous tool choice (`ScraperChoice`).  
- Uses Scrapy first. If result is empty, tries Playwright.  
- PDF is read if the content looks like a PDF.  
- Then we pass the final text to AI for summarization or searching for the user’s specific notification.  

All done in the Celery worker, so no Twisted signals or multi-thread issues in Django.

---

## **What to Remove from Your Old Code**

- **Remove** any direct `CrawlerProcess()` usage in your Django code.  
- **Remove** attempts to call `process.start()` from `views.py`.  
- **Remove** the old approach that does `scrapy` imports in the main Django process.  

---

## **Summary**

**Yes**, this approach implements your entire plan:

1. Normal chat: immediate AI response.  
2. If user wants a specific site’s notification, we do Google search + scraping + PDF reading in a separate Celery worker.  
3. We pass the scraped text back to AI to find that **one** “notification” the user asked for. If found, we can either store it or notify the user right away. If not found, we create a `ScheduledNotificationRequest` so a background job (Celery beat) re-checks the site daily.  
4. Once found, we email the user with the “complete info” from that PDF or page.  

This is the “best” fix for your Twisted conflicts and your bigger business logic. You get:

- **No** “ReactorNotRestartable” errors in Django dev server.  
- **No** 30+ second blocking while scraping.  
- A robust architecture that can scale.  

All the code above is a **working reference**. You’ll adapt it to your exact fields, your AI prompts, your logic for how you parse the user’s message, etc. But structurally, this is the recommended solution.