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
