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
