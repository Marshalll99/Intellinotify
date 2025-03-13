import scrapy
from playwright.sync_api import sync_playwright
from data_engine.models import ScraperChoice
from data_engine.pdf_handler import extract_text_from_pdf
import requests
import mimetypes

class UniversalScraper:
    def __init__(self, url):
        self.url = url
        self.tool = self.get_scraping_tool(url)

    def get_scraping_tool(self, url):
        """Check DB for previous tool choice; use Scrapy by default."""
        choice = ScraperChoice.objects.filter(url=url).first()
        return choice.tool if choice else "scrapy"

    def update_tool_choice(self, tool):
        """Save best tool choice in DB for future scraping."""
        ScraperChoice.objects.update_or_create(url=self.url, defaults={"tool": tool})

    def scrape_with_scrapy(self):
        """Scrapes content using Scrapy."""
        class ScraperSpider(scrapy.Spider):
            name = "scraper"
            start_urls = [self.url]

            def parse(self, response):
                return response.text

        from scrapy.crawler import CrawlerProcess
        process = CrawlerProcess(settings={"LOG_ENABLED": False})
        process.crawl(ScraperSpider)
        process.start()

        return ScraperSpider.parse

    def scrape_with_playwright(self):
        """Scrapes content using Playwright."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url)
            content = page.content()
            browser.close()
            return content

    def detect_pdf(self, response_text):
        """Checks if the scraped content is a PDF link."""
        if "application/pdf" in response_text or self.url.endswith(".pdf"):
            return True
        return False

    def run_scraper(self):
        """Decides whether to use Scrapy or Playwright based on data quality."""
        content = self.scrape_with_scrapy() if self.tool == "scrapy" else self.scrape_with_playwright()

        if not content.strip():
            self.tool = "playwright" if self.tool == "scrapy" else "scrapy"
            self.update_tool_choice(self.tool)
            content = self.scrape_with_playwright() if self.tool == "playwright" else self.scrape_with_scrapy()

        if self.detect_pdf(content):
            pdf_text = extract_text_from_pdf(self.url)
            return pdf_text
        
        return content
