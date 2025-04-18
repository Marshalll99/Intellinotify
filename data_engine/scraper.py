
import threading
import requests
import re
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from .pdf_handler import extract_text_from_pdf
from .google_search import google_search_top_url
from .models import ScraperChoice, NotificationPageMapping
from scrapy.crawler import CrawlerProcess
import scrapy

class SimpleSpider(scrapy.Spider):
    name = "simple_spider"
    start_urls = []

    def __init__(self, url):
        super().__init__()
        self.start_urls = [url]
        self.page_text = ""
        self.pdf_links = []

    def parse(self, response):
        self.page_text = response.text
        self.pdf_links = response.css('a::attr(href)').re(r'.*\.pdf')

class UniversalScraper:
    def __init__(self, domain_or_url, notification_name=None):
        self.domain_or_url = domain_or_url
        self.notification_name = notification_name
        self.session = requests.Session()
        self.text = ""
        self.pdfs = []
        self.load_url = ""

    def detect_notification_page(self):
        domain = urlparse(self.domain_or_url).netloc or self.domain_or_url.replace('https://', '').replace('http://', '')
        mapping = NotificationPageMapping.objects.filter(domain=domain).first()

        if mapping:
            print(f"✅ Found mapped notifications page: {mapping.notification_page_url}")
            return mapping.notification_page_url

        print(f"🔍 No mapping found. Using Google search...")
        return None

    def fast_scrape(self, url):
        print(f"⚙️ Trying requests for {url}")
        try:
            response = self.session.get(url, timeout=10)  # 10 seconds timeout
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                self.text = soup.get_text(separator="\n", strip=True)
                self.pdfs = [link["href"] for link in soup.find_all("a", href=True) if link["href"].lower().endswith(".pdf")]
                return True
        except Exception as e:
            print(f"Requests error: {e}")
        return False

    def playwright_scrape(self, url):
        print(f"⚙️ Trying playwright for {url}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=20000)  # 20 seconds timeout
                self.text = page.content()
                self.pdfs = [a.get_attribute("href") for a in page.query_selector_all("a") if a.get_attribute("href") and a.get_attribute("href").lower().endswith(".pdf")]
                browser.close()
                return True
        except PlaywrightTimeout:
            print(f"Playwright timeout after 20 seconds.")
        except Exception as e:
            print(f"Playwright error: {e}")
        return False

    def scrapy_scrape(self, url):
        print(f"⚙️ Trying scrapy for {url}")
        try:
            process = CrawlerProcess(settings={
                "LOG_ENABLED": False,
                "USER_AGENT": "Mozilla/5.0",
            })
            spider = SimpleSpider(url)
            process.crawl(spider)
            process.start()

            self.text = spider.page_text
            self.pdfs = spider.pdf_links
            return True
        except Exception as e:
            print(f"Scrapy error: {e}")
        return False

    def run_scraper(self):
        mapped_url = self.detect_notification_page()

        if mapped_url:
            url_to_scrape = mapped_url
        else:
            url_to_scrape = google_search_top_url(self.domain_or_url)

        parsed = urlparse(url_to_scrape)
        if not parsed.scheme:
            url_to_scrape = "https://" + url_to_scrape

        self.load_url = url_to_scrape
        tool_record = ScraperChoice.objects.filter(url=url_to_scrape).first()

        if tool_record:
            tool = tool_record.tool
            print(f"🔍 Preferred scraping tool: {tool}")
        else:
            tool = None

        # Smart switching logic
        print(f"⚡ Attempting with: {tool or 'requests'}")

        if (tool == "requests" or tool is None) and self.fast_scrape(url_to_scrape):
            if not tool_record:
                ScraperChoice.objects.create(url=url_to_scrape, tool="requests")
            return self.text, self.pdfs

        if (tool == "playwright" or tool is None) and self.playwright_scrape(url_to_scrape):
            if tool_record:
                tool_record.tool = "playwright"
                tool_record.save()
            else:
                ScraperChoice.objects.create(url=url_to_scrape, tool="playwright")
            return self.text, self.pdfs

        if (tool == "scrapy" or tool is None) and self.scrapy_scrape(url_to_scrape):
            if tool_record:
                tool_record.tool = "scrapy"
                tool_record.save()
            else:
                ScraperChoice.objects.create(url=url_to_scrape, tool="scrapy")
            return self.text, self.pdfs

        print(f"❌ All scraping methods failed.")
        return "", []

    def find_notification(self, notification_name):
        print(f"🔎 Searching notification '{notification_name}' in scraped data...")

        lower_text = self.text.lower()
        matches = [m for m in re.finditer(re.escape(notification_name.lower()), lower_text)]

        if matches:
            print(f"✅ Found notification match in HTML text.")
            match = matches[0]
            start, end = max(match.start() - 300, 0), min(match.end() + 300, len(self.text))
            snippet = self.text[start:end]
            return snippet, None

        print(f"🔍 Notification not found in HTML. Checking PDFs...")

        start_time = time.time()
        for pdf_link in self.pdfs:
            if time.time() - start_time > 30:  # max 30 seconds total for all PDFs
                print(f"⚠️ Timed out checking PDFs.")
                break

            full_pdf_url = pdf_link if pdf_link.startswith("http") else f"https://{urlparse(self.load_url).netloc}/{pdf_link.lstrip('/')}"
            pdf_text = extract_text_from_pdf(full_pdf_url)
            if pdf_text and notification_name.lower() in pdf_text.lower():
                print(f"✅ Found inside PDF: {full_pdf_url}")
                return None, full_pdf_url

        print(f"❌ Notification not found after PDF checking.")
        return None, None
