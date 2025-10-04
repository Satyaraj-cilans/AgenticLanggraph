from firecrawl import Firecrawl
firecrawl = Firecrawl(api_key="fc-e2e12538f22d4136893bb83944bbdb18")
result = firecrawl.scrape('https://www.pragnakalp.com/making-rag-work-for-pdfs-with-images-and-visual-guides/', formats=['markdown', 'html'])
print(result)  # Contains scraped content and metadata

crawl_data = firecrawl.crawl(url="https://www.pragnakalp.com/making-rag-work-for-pdfs-with-images-and-visual-guides/", limit=100)
print(crawl_data)  # Aggregated results in chosen formats
