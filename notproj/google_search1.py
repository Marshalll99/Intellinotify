import scrapy
from scrapy.crawler import CrawlerRunner
import crochet

# Initialize Crochet at the beginning of the module.
crochet.setup()

class GoogleSearchSpider(scrapy.Spider):
    name = "google_search"
    results = []

    def __init__(self, query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Append "notification" to the query, then build the URL.
        full_query = f"{query} notification".replace(" ", "+")
        self.start_urls = [f"https://www.google.com/search?q={full_query}"]
        self.results = []

    def parse(self, response):
        # Extract search results using CSS selectors.
        for result in response.css("div.tF2Cxc"):
            title = result.css("h3::text").get()
            link = result.css("a::attr(href)").get()
            if title and link:
                # Filter out typical ad or redirect URLs.
                if "google.com" not in link and "/aclk?" not in link and "adurl=" not in link:
                    self.results.append({"title": title, "link": link})


from scrapy.crawler import CrawlerRunner
runner = CrawlerRunner(settings={"LOG_ENABLED": False})

@crochet.wait_for(timeout=60)  # Enforce an explicit 60-second timeout.
@crochet.run_in_reactor
def crawl_google(query):
    """
    Runs the GoogleSearchSpider asynchronously.
    If the crawl doesn't finish within the timeout, a TimeoutError is raised.
    """
    return runner.crawl(GoogleSearchSpider, query=query)

def get_google_search_results(query):
    try:
        print(f"Starting Google search for: {query}")
        # This call is now blocking until the crawl is complete or times out.
        crawl_google(query)
        print("Google search completed successfully.")
    except Exception as e:
        print(f"Google search timed out: {e}")
        return []
    # Once complete, extract the results from the spider.
    for crawler in runner.crawlers:
        spider = crawler.spider
        if isinstance(spider, GoogleSearchSpider):
            return spider.results
    return []
