import scrapy
from scrapy.crawler import CrawlerProcess
import re

class GoogleSearchSpider(scrapy.Spider):
    name = "google_search"
    start_urls = []

    def __init__(self, query):
        formatted_query = query.replace(" ", "+")
        self.start_urls = [f"https://www.google.com/search?q={formatted_query}"]

    def parse(self, response):
        """Extracts top Google Search results."""
        results = []
        for result in response.css("div.tF2Cxc"):
            title = result.css("h3::text").get()
            link = result.css("a::attr(href)").get()
            if title and link:
                results.append({"title": title, "link": link})
        return results

def get_google_search_results(query):
    """Runs the Google Search Spider."""
    process = CrawlerProcess(settings={"LOG_ENABLED": False})
    spider = GoogleSearchSpider(query)
    process.crawl(spider)
    process.start()
    return spider.parse  # Returns a list of top search results
