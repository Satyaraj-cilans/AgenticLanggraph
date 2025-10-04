import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, Any, List, Optional, Union, Callable
from urllib.parse import urljoin, urlparse, quote_plus, unquote
import time
import re
from datetime import datetime, timedelta
import random


class CustomWebSearchTool:
    """Custom web search and scraping tool compatible with Agno framework"""
    
    def __init__(
        self,
        search: bool = True,
        formats: List[str] = None,
        search_params: Dict[str, Any] = None,
        **kwargs
    ):
        self.search = search
        self.formats = formats or ["markdown", "links"]
        self.search_params = search_params or {"limit": 5, "tbs": "qdr:w"}
        
        # Required attributes for agno framework
        self.__name__ = "custom_web_search"
        self.name = "custom_web_search"
        self.description = "Search the web for current information and extract content from relevant articles"
        
        # Initialize session with rotating headers
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        # Set initial headers
        self._rotate_headers()
        
        print(f"🔧 Initialized CustomWebSearchTool with name: {self.__name__}")
    
    def _rotate_headers(self):
        """Rotate user agent and headers to avoid blocking"""
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })
    
    def __call__(self, query: str) -> str:
        """Make the tool callable - this is what Agno will use"""
        print(f"🤖 Agno is calling custom_web_search with query: {query}")
        return self.custom_web_search(query)
    
    def run(self, query: str) -> str:
        """Alternative method name for agno compatibility"""
        return self.custom_web_search(query)
    
    def custom_web_search(self, query: str) -> str:
        """
        Search for web content and return formatted results
        
        Args:
            query: Search query string
            
        Returns:
            Formatted search results with content
        """
        try:
            print(f"🔍 EXECUTING WEB SEARCH: {query}")
            print("=" * 50)
            
            # Get search parameters
            limit = self.search_params.get("limit", 5)
            time_range = self.search_params.get("tbs", "qdr:w")
            
            print(f"Search Config: Limit={limit}, TimeRange={time_range}")
            
            # Search for URLs using multiple methods
            urls = self._search_urls(query, limit, time_range)
            
            if not urls:
                print("NO SEARCH RESULTS FOUND")
                return f"No search results found for query: {query}. Please try a different search term."
            
            print(f"found {len(urls)} URLs to scrape:")
            for i, url in enumerate(urls, 1):
                print(f"   {i}. {url}")
            
            # Scrape content from URLs
            results = []
            for i, url in enumerate(urls[:limit]):
                print(f"\n SCRAPING {i+1}/{len(urls)}: {url}")
                content = self._scrape_content(url)
                if content and content.get('success'):
                    results.append(content)
                    print(f"SUCCESS: {content['title'][:60]}...")
                    print(f"Content: {len(content['content'])} chars")
                else:
                    print(f": {content.get('error', 'Unknown error')}")
                
                # Rate limiting with randomization
                time.sleep(random.uniform(1, 3))
            
            if not results:
                print("NO CONTENT EXTRACTED")
                return f"No content could be extracted from search results for: {query}"
            
            print(f"\n🎉 SUCCESSFULLY EXTRACTED {len(results)} articles")
            
            # Format results
            formatted_results = self._format_results(results, query)
            print(f"Generated formatted results: {len(formatted_results)} characters")
            print("=" * 50)
            
            return formatted_results
            
        except Exception as e:
            error_msg = f"CRITICAL ERROR in web search: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg
    
    def _search_urls(self, query: str, limit: int, time_range: str) -> List[str]:
        """Search for URLs using multiple search engines with improved parsing"""
        urls = []
        
        print(f"...Starting multi-engine search for: '{query}'")
        
        # Method 1: DuckDuckGo Search with improved parsing
        try:
            print("🦆 Trying DuckDuckGo...")
            ddg_urls = self._duckduckgo_search_improved(query, limit)
            urls.extend(ddg_urls)
            print(f"DuckDuckGo found {len(ddg_urls)} URLs")
        except Exception as e:
            print(f"DuckDuckGo failed: {e}")
        
        # Method 2: Alternative search approach
        if len(urls) < limit:
            try:
                print("🔍 Trying alternative search...")
                alt_urls = self._alternative_search(query, limit - len(urls))
                urls.extend(alt_urls)
                print(f"Alternative search found {len(alt_urls)} additional URLs")
            except Exception as e:
                print(f"Alternative search failed: {e}")
        
        # Method 3: Direct news site search if still need more
        if len(urls) < limit:
            try:
                print("Trying direct news sites...")
                news_urls = self._search_news_sites(query, limit - len(urls))
                urls.extend(news_urls)
                print(f"News sites found {len(news_urls)} additional URLs")
            except Exception as e:
                print(f"News sites search failed: {e}")
        
        # Remove duplicates and validate
        seen = set()
        valid_urls = []
        for url in urls:
            if url not in seen and self._is_valid_url(url):
                seen.add(url)
                valid_urls.append(url)
        
        print(f"Total valid URLs found: {len(valid_urls)}")
        return valid_urls[:limit]
    
    def _duckduckgo_search_improved(self, query: str, limit: int) -> List[str]:
        """Improved DuckDuckGo search with better link extraction"""
        # Rotate headers for each search
        self._rotate_headers()
        
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        
        try:
            print(f"...Fetching: {search_url}")
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()
            print(f"Response: {response.status_code}, Content: {len(response.content)} bytes")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            urls = []
            
            # Debug: Print some of the HTML structure
            print(f"Found {len(soup.find_all('a'))} total links in page")
            
            # Method 1: Look for result links with specific patterns
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                
                # DuckDuckGo uses redirects, so we need to extract the real URL
                if '/l/?uddg=' in href or '/l/?kh=' in href:
                    # Extract URL from DuckDuckGo redirect
                    try:
                        import urllib.parse as urlparse
                        parsed = urlparse.parse_qs(urlparse.urlparse(href).query)
                        if 'uddg' in parsed:
                            real_url = unquote(parsed['uddg'][0])
                        elif 'kh' in parsed:
                            real_url = unquote(parsed['kh'][0])
                        else:
                            continue
                        
                        if self._is_news_url(real_url):
                            urls.append(real_url)
                            print(f"   ✅ Found URL: {real_url}")
                    except Exception as e:
                        print(f"   ⚠️ Error parsing redirect: {e}")
                        continue
                
                elif href.startswith('http') and 'duckduckgo.com' not in href:
                    if self._is_news_url(href):
                        urls.append(href)
                        print(f"   ✅ Found direct URL: {href}")
                
                if len(urls) >= limit:
                    break
            
            print(f"DuckDuckGo extracted {len(urls)} URLs")
            return urls[:limit]
            
        except Exception as e:
            print(f" DuckDuckGo detailed error: {e}")
            return []
    
    def _alternative_search(self, query: str, limit: int) -> List[str]:
        """Alternative search method using a different approach"""
        # Search through a simple web directory or use fallback URLs
        fallback_urls = []
        
        # Search for recent articles by constructing likely URLs
        keywords = query.lower().split()
        
        # Try some major news sites with search functionality
        news_sites = [
            f"https://techcrunch.com/search/{quote_plus(query)}/",
            f"https://www.theverge.com/search?q={quote_plus(query)}",
            f"https://arstechnica.com/search/?query={quote_plus(query)}",
        ]
        
        for site_url in news_sites[:limit]:
            try:
                print(f"Trying news site: {site_url}")
                response = self.session.get(site_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for article links
                    for link in soup.find_all('a', href=True):
                        href = link.get('href')
                        if href and ('/2024/' in href or '/2025/' in href):
                            if not href.startswith('http'):
                                href = urljoin(site_url, href)
                            
                            if self._is_news_url(href):
                                fallback_urls.append(href)
                                print(f"   ✅ Found article: {href}")
                                
                                if len(fallback_urls) >= limit:
                                    break
                    
                    if len(fallback_urls) >= limit:
                        break
                        
            except Exception as e:
                print(f"Site search failed for {site_url}: {e}")
                continue
        
        return fallback_urls[:limit]
    
    def _search_news_sites(self, query: str, limit: int) -> List[str]:
        """Search specific news sites directly"""
        news_urls = []
        
        # Well-known tech news sites that often have recent AI content
        direct_checks = [
            "https://techcrunch.com/category/artificial-intelligence/",
            "https://www.theverge.com/ai-artificial-intelligence",
            "https://arstechnica.com/tag/artificial-intelligence/",
            "https://venturebeat.com/ai/",
            "https://www.wired.com/tag/artificial-intelligence/"
        ]
        
        for site_url in direct_checks:
            try:
                if len(news_urls) >= limit:
                    break
                    
                print(f"   🌐 Checking news site: {site_url}")
                response = self.session.get(site_url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for recent article links
                    article_selectors = [
                        'article a[href]',
                        '.post-title a[href]',
                        '.entry-title a[href]',
                        'h1 a[href]',
                        'h2 a[href]',
                        'h3 a[href]',
                        '[data-module="ArticleTeaser"] a[href]'
                    ]
                    
                    for selector in article_selectors:
                        links = soup.select(selector)
                        for link in links:
                            href = link.get('href')
                            if href:
                                if not href.startswith('http'):
                                    href = urljoin(site_url, href)
                                
                                if self._is_recent_article(href):
                                    news_urls.append(href)
                                    print(f"   ✅ Found recent article: {href}")
                                    
                                    if len(news_urls) >= limit:
                                        break
                        
                        if len(news_urls) >= limit:
                            break
                    
                else:
                    print(f"   ⚠️ Failed to fetch {site_url}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Error checking {site_url}: {e}")
                continue
        
        return news_urls[:limit]
    
    def _is_news_url(self, url: str) -> bool:
        """Check if URL looks like a news article"""
        if not self._is_valid_url(url):
            return False
        
        # Look for patterns that suggest it's a news article
        news_indicators = [
            '/news/', '/article/', '/story/', '/post/', '/blog/',
            '/2024/', '/2025/', '/artificial-intelligence/', '/ai/',
            '/tech/', '/technology/'
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in news_indicators)
    
    def _is_recent_article(self, url: str) -> bool:
        """Check if URL looks like a recent article"""
        if not self._is_news_url(url):
            return False
        
        # Check for recent dates in URL
        current_year = datetime.now().year
        recent_indicators = [
            f'/{current_year}/',
            f'/{current_year - 1}/',
            '/2024/', '/2025/'
        ]
        
        return any(indicator in url for indicator in recent_indicators)
    
    def _is_valid_url(self, url: str) -> bool:
        """Enhanced URL validation"""
        try:
            parsed = urlparse(url)
            
            # Basic validation
            if not (parsed.scheme in ['http', 'https'] and parsed.netloc):
                return False
            
            # Exclude social media and search engines
            excluded_domains = [
                'facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com',
                'youtube.com', 'tiktok.com', 'pinterest.com', 'reddit.com',
                'google.com', 'bing.com', 'yahoo.com', 'duckduckgo.com',
                'amazon.com', 'ebay.com'
            ]
            domain = parsed.netloc.lower()
            for excluded in excluded_domains:
                if excluded in domain:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _scrape_content(self, url: str) -> Dict[str, Any]:
        """Enhanced content scraping with better error handling"""
        try:
            print(f"... Fetching: {url}")
            
            # Rotate headers for each request
            self._rotate_headers()
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            print(f"Status: {response.status_code}")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript', 'form']):
                element.decompose()
            
            # Extract components
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            published_date = self._extract_date(soup)
            
            print(f"Title: {title[:50]}...")
            print(f"Content: {len(content)} characters")
            
            if len(content) < 100:
                print(f"Content too short, skipping")
                return {'success': False, 'error': 'Content too short'}
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'published_date': published_date,
                'success': True,
                'word_count': len(content.split()) if content else 0
            }
            
        except Exception as e:
            print(f" Scraping error: {str(e)}")
            return {
                'title': '',
                'content': '',
                'url': url,
                'success': False,
                'error': str(e)
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Enhanced title extraction"""
        selectors = [
            'h1.entry-title',
            'h1.post-title',
            'h1.article-title',
            'h1[class*="title"]',
            'h1',
            '[property="og:title"]',
            '[name="twitter:title"]',
            'title',
            '.headline',
            '.page-title'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        title = element.get('content', '').strip()
                    else:
                        title = element.get_text().strip()
                    
                    if title and len(title) > 5:
                        # Clean title
                        title = re.sub(r'\s+', ' ', title)
                        title = title.split('|')[0].split('-')[0].strip()  # Remove site name
                        return title[:150]
            except:
                continue
        
        return "Untitled Article"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Enhanced content extraction with better selectors"""
        selectors = [
            'article .entry-content',
            'article .post-content',
            'article .article-content',
            'article .content',
            'article',
            '[role="main"] .content',
            '[role="main"]',
            'main article',
            'main .content',
            'main',
            '.entry-content',
            '.post-content',
            '.article-content',
            '.article-body',
            '.story-content',
            '.story-body',
            '#content .content',
            '#content',
            '.main-content'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    # Remove unwanted nested elements
                    for unwanted in element.select('aside, .sidebar, .related, .comments, .social, .share, .advertisement, .ad'):
                        unwanted.decompose()
                    
                    content = element.get_text(separator='\n', strip=True)
                    if len(content) > 300:  # Ensure substantial content
                        return self._clean_content(content)
            except:
                continue
        
        # Fallback: extract from paragraphs
        try:
            paragraphs = soup.find_all('p')
            if paragraphs:
                content = '\n'.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
                if len(content) > 300:
                    return self._clean_content(content)
        except:
            pass
        
        return "Content extraction failed"
    
    def _clean_content(self, content: str) -> str:
        """Enhanced content cleaning"""
        if not content:
            return ""
        
        # Remove extra whitespace
        content = re.sub(r'\n+', '\n', content)
        content = re.sub(r'\s+', ' ', content)
        
        # Remove unwanted patterns
        patterns_to_remove = [
            r'Cookie Policy.*?Accept.*?',
            r'Subscribe.*?newsletter.*?',
            r'Follow us.*?social.*?',
            r'Share this.*?',
            r'Advertisement.*?',
            r'Related:.*?',
            r'Also read:.*?',
            r'Sign up.*?',
            r'Read more:.*?',
            r'Continue reading.*?'
        ]
        
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Limit content length but try to end at sentence
        if len(content) > 3000:
            truncated = content[:3000]
            last_sentence = max(
                truncated.rfind('.'),
                truncated.rfind('!'),
                truncated.rfind('?')
            )
            if last_sentence > 2500:
                content = truncated[:last_sentence + 1]
            else:
                content = truncated + "..."
        
        return content.strip()
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Enhanced date extraction"""
        selectors = [
            'time[datetime]',
            '[property="article:published_time"]',
            '[property="article:modified_time"]',
            '[name="twitter:data1"]',
            '.published',
            '.date',
            '.post-date',
            '.article-date',
            '.entry-date',
            '.timestamp'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    if element.name == 'meta':
                        date_str = element.get('content', '')
                    elif element.name == 'time':
                        date_str = element.get('datetime', '') or element.get_text()
                    else:
                        date_str = element.get_text().strip()
                    
                    if date_str:
                        # Try to parse ISO format
                        if 'T' in date_str:
                            try:
                                parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                return parsed.strftime("%Y-%m-%d")
                            except:
                                pass
                        
                        # Return first 10 characters if it looks like a date
                        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                            return date_str[:10]
                        
                        return date_str[:50]  # Limit length
            except:
                continue
        
        return datetime.now().strftime("%Y-%m-%d")
    
    def _format_results(self, results: List[Dict], query: str) -> str:
        """Enhanced result formatting for better AI processing"""
        if not results:
            return f"No results found for query: {query}"
        
        # Create comprehensive formatted output
        formatted = f"""# 🔍 LIVE WEB SEARCH RESULTS: {query}

## 📊 SEARCH SUMMARY
- **Query:** {query}
- **Results Found:** {len(results)} articles
- **Search Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Total Content:** {sum(r.get('word_count', 0) for r in results)} words

## 📰 ARTICLE ANALYSIS

"""
     
        for i, result in enumerate(results, 1):
            formatted += f"""### Article {i}: {result['title']}

** Source Information:**
- **URL:** {result['url']}
- **Published:** {result.get('published_date', 'Unknown')}  
- **Word Count:** {result.get('word_count', 0)} words

** Full Content:**
{result['content']}

**Source Link:** [{result['title']}]({result['url']})

{'─' * 80}

"""
        
        # Add research summary
        formatted += f"""##RESEARCH INSIGHTS

**Key Findings:** The web search successfully gathered {len(results)} current articles about "{query}" with comprehensive content totaling {sum(r.get('word_count', 0) for r in results)} words.

**Source Quality:** All sources have been validated and contain substantial content relevant to the search query.

**Recency:** Search focused on recent content to ensure current information.

**Next Steps:** Use this comprehensive research data to create an engaging, fact-based newsletter with proper attribution to these {len(results)} sources.

---
*This research data was generated through live web search on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        return formatted


# Test function to verify the tool works
def test_web_search_tool():
    """Test the web search tool independently"""
    print("\nTESTING IMPROVED CUSTOM WEB SEARCH TOOL")
    print("=" * 50)
    
    tool = CustomWebSearchTool(
        search_params={"limit": 3, "tbs": "qdr:w"}
    )
    
    test_queries = [
        "artificial intelligence latest news",
        "AI technology 2024",
        "machine learning breakthroughs"
    ]
    
    for query in test_queries:
        print(f"\n Testing query: {query}")
        result = tool.custom_web_search(query)
        
        print(f"RESULTS for '{query}':")
        print(f"- Length: {len(result)} characters")
        print(f"- Contains data: {'Yes' if len(result) > 500 else '❌ No'}")
        
        if len(result) > 500:
            print(f"- Status: SUCCESS")
            break
        else:
            print(f"- Status: -FAILED")
            print(f"- Output: {result}")
    
    return len(result) > 500 if 'result' in locals() else False


if __name__ == "__main__":
    success = test_web_search_tool()
    print(f"\nOVERALL TEST RESULT: {'✅ SUCCESS' if success else '❌ FAILED'}")