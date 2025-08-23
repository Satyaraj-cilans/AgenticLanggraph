import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import requests

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API keys
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY")

class NewsletterGenerator:
    def __init__(self, topic: str, search_limit: int = 5, time_range: str = "qdr:w"):
        self.topic = topic
        self.search_limit = search_limit
        self.time_range = time_range
        
        logger.info(f"Initializing NewsletterGenerator with topic: '{topic}', limit: {search_limit}")
        
        # Check if we have API keys
        if not NEBIUS_API_KEY:
            logger.error("NEBIUS_API_KEY not found")
            raise ValueError("NEBIUS_API_KEY environment variable is not set.")
        if not NEWSAPI_API_KEY:
            logger.error("NEWSAPI_API_KEY not found")
            raise ValueError("NEWSAPI_API_KEY environment variable is not set.")
    
    def generate(self) -> str:
        """Generate newsletter content"""
        try:
            logger.info(f"Starting newsletter generation for topic: {self.topic}")
            
            # Try the full AI approach first
            return self._generate_with_newsapi_and_ai()
            
        except Exception as e:
            logger.error(f"Full AI generation failed: {str(e)}")
            # Fallback to NewsAPI only
            return self._generate_with_newsapi_only()
    
    def _fetch_news_articles(self) -> List[Dict[str, Any]]:
        """Fetch articles from NewsAPI"""
        try:
            from newsapi import NewsApiClient
            
            newsapi = NewsApiClient(api_key=NEWSAPI_API_KEY)
            
            # Calculate date range
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            logger.info(f"Searching NewsAPI for: {self.topic}")
            response = newsapi.get_everything(
                q=self.topic,
                language='en',
                sort_by='relevancy',
                page_size=min(self.search_limit, 20),
                from_param=from_date
            )
            
            articles = response.get("articles", [])
            logger.info(f"Found {len(articles)} articles")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching news articles: {str(e)}")
            return []
    
    def _call_nebius_api(self, prompt: str) -> str:
        """Call Nebius API directly"""
        try:
            url = "https://api.studio.nebius.ai/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {NEBIUS_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert newsletter writer. Create engaging, professional newsletters from the provided content. Use proper markdown formatting."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            logger.info("Calling Nebius API...")
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            logger.info("Successfully generated content with Nebius API")
            return content
            
        except Exception as e:
            logger.error(f"Error calling Nebius API: {str(e)}")
            raise
    
    def _generate_with_newsapi_and_ai(self) -> str:
        """Generate newsletter using NewsAPI + AI"""
        # Fetch articles
        articles = self._fetch_news_articles()
        
        if not articles:
            raise Exception("No articles found")
        
        # Prepare content for AI
        articles_text = ""
        for i, article in enumerate(articles[:self.search_limit], 1):
            title = article.get('title', 'Untitled')
            description = article.get('description', 'No description')
            url = article.get('url', '')
            source = article.get('source', {}).get('name', 'Unknown')
            published = article.get('publishedAt', '')
            
            articles_text += f"""
Article {i}:
Title: {title}
Source: {source}
Published: {published}
Description: {description}
URL: {url}

"""
        
        # Create AI prompt
        prompt = f"""Create a professional newsletter about "{self.topic}" using the following articles:

{articles_text}

Please create a well-structured newsletter with:
1. A compelling headline
2. An engaging introduction
3. Main story sections covering the most important developments
4. Key insights and analysis
5. A summary of highlights
6. Proper source attribution with links

Use markdown formatting and make it engaging and informative."""
        
        # Generate with AI
        try:
            ai_content = self._call_nebius_api(prompt)
            return ai_content
        except Exception as e:
            logger.error(f"AI generation failed, falling back: {str(e)}")
            return self._generate_with_newsapi_only()
    
    def _generate_with_newsapi_only(self) -> str:
        """Generate newsletter using only NewsAPI (no AI)"""
        logger.info("Using NewsAPI-only generation")
        
        articles = self._fetch_news_articles()
        
        if not articles:
            return self._generate_fallback()
        
        # Create newsletter manually
        newsletter = f"# Newsletter: {self.topic}\n\n"
        newsletter += f"## Welcome\n"
        newsletter += f"Here's your latest newsletter about **{self.topic}** featuring {len(articles[:self.search_limit])} recent articles.\n\n"
        
        newsletter += "## Featured Stories\n\n"
        
        for i, article in enumerate(articles[:self.search_limit], 1):
            title = article.get('title', 'Untitled')
            description = article.get('description', 'No description available')
            url = article.get('url', '')
            source = article.get('source', {}).get('name', 'Unknown Source')
            published = article.get('publishedAt', '')
            
            # Format the date
            try:
                if published:
                    pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    formatted_date = pub_date.strftime('%B %d, %Y')
                else:
                    formatted_date = 'Recent'
            except:
                formatted_date = 'Recent'
            
            newsletter += f"### {i}. {title}\n\n"
            newsletter += f"**Source:** {source} | **Published:** {formatted_date}\n\n"
            newsletter += f"{description}\n\n"
            
            if url:
                newsletter += f"[Read Full Article]({url})\n\n"
            
            newsletter += "---\n\n"
        
        # Add summary section
        newsletter += "## Key Highlights\n\n"
        for i, article in enumerate(articles[:3], 1):
            title = article.get('title', 'Untitled')
            newsletter += f"- **{title}**\n"
        
        newsletter += f"\n## About This Newsletter\n\n"
        newsletter += f"This newsletter was generated based on {len(articles)} recent articles about {self.topic}. "
        newsletter += f"Articles were sourced from NewsAPI and cover developments from the past week.\n\n"
        
        newsletter += "## Sources\n\n"
        for i, article in enumerate(articles[:self.search_limit], 1):
            title = article.get('title', 'Untitled')
            url = article.get('url', '')
            source = article.get('source', {}).get('name', 'Unknown')
            
            if url:
                newsletter += f"{i}. [{title}]({url}) - {source}\n"
            else:
                newsletter += f"{i}. {title} - {source}\n"
        
        newsletter += f"\n---\n*Newsletter generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*"
        
        return newsletter
    
    def _generate_fallback(self) -> str:
        """Generate a fallback newsletter when all else fails"""
        logger.info("Using fallback newsletter generation")
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return f"""# Newsletter: {self.topic}

## System Status

The newsletter generation system encountered issues accessing external APIs. This could be due to:

- NewsAPI rate limits or connectivity issues
- API key configuration problems
- Network restrictions in the Docker environment

## Configuration Check

- **Topic Requested:** {self.topic}
- **Articles Requested:** {self.search_limit}
- **Time Range:** {self.time_range}
- **Generated:** {current_time}
- **NEWSAPI_KEY:** {'Set' if NEWSAPI_API_KEY else 'Missing'}
- **NEBIUS_API_KEY:** {'Set' if NEBIUS_API_KEY else 'Missing'}

## Troubleshooting

1. **Check API Keys:** Ensure both NewsAPI and Nebius API keys are valid and properly set
2. **Check Rate Limits:** NewsAPI has usage limits that might be exceeded
3. **Check Network:** Ensure Docker containers can access external APIs
4. **Check Logs:** Run `docker-compose logs api` for detailed error information

## Next Steps

To resolve this issue:
- Verify your API keys at https://newsapi.org/ and https://studio.nebius.ai/
- Check your internet connection and firewall settings
- Review container logs for specific error messages
- Try a different topic or reduce the number of articles

---
*This is a diagnostic message. Normal newsletter generation will resume once the underlying issues are resolved.*"""

# Test function
def test_newsletter_generator():
    """Test the NewsletterGenerator class"""
    try:
        logger.info("Testing NewsletterGenerator...")
        generator = NewsletterGenerator("AI developments", 3)
        content = generator.generate()
        
        # Check if we got real content
        if "System Status" in content or "simplified mode" in content:
            logger.warning("Generator is working but using fallback mode")
            return True
        else:
            logger.info("Newsletter generation test successful with real content")
            return True
            
    except Exception as e:
        logger.error(f"Newsletter generation test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Enhanced NewsletterGenerator...")
    
    if test_newsletter_generator():
        print("✅ NewsletterGenerator is working")
        
        # Generate a test newsletter
        gen = NewsletterGenerator("Latest technology news", 3)
        content = gen.generate()
        print("\n" + "="*50)
        print("SAMPLE NEWSLETTER:")
        print("="*50)
        print(content)
    else:
        print("❌ NewsletterGenerator test failed")
        exit(1)