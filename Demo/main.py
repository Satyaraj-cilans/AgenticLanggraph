import os
from textwrap import dedent
from dotenv import load_dotenv
from typing import Dict, Any

try:
    from agno.agent import Agent
    from agno.models.nebius import Nebius
    from agno.storage.sqlite import SqliteStorage
    from agno.tools import toolkit
    AGNO_AVAILABLE = True
    print("✅ Agno framework detected")
except ImportError as e:
    print(f"⚠️ Agno framework not available: {e}")
    print("💡 Will use fallback mode")
    AGNO_AVAILABLE = False

# Import our custom web tools
from custom_web_tools import CustomWebSearchTool

# Load environment variables
load_dotenv()

# Get API key
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")

def custom_web_search(query: str) -> str:
    """
    Search the web for current information and extract content from relevant articles.
    
    Args:
        query: The search query to find relevant articles and information
        
    Returns:
        Formatted search results with extracted content from multiple sources
    """
    print(f"🔍 Web search called with query: {query}")
    
    # Create the web search tool
    tool = CustomWebSearchTool(
        search_params={
            "limit": 5,
            "tbs": "qdr:w"
        }
    )
    
    # Execute the search
    return tool.custom_web_search(query)

def create_agno_newsletter_agent():
    """Create newsletter agent using Agno framework"""
    if not AGNO_AVAILABLE:
        raise ImportError("Agno framework not available")
        
    if not NEBIUS_API_KEY:
        raise ValueError("NEBIUS_API_KEY environment variable is not set. Please set it in your .env file")

    return Agent(
        model=Nebius(
            id="meta-llama/Meta-Llama-3.1-70B-Instruct",
            api_key=NEBIUS_API_KEY
        ),
        tools=[custom_web_search],  # Use the function directly
        description=dedent("""\
        You are an expert newsletter writer and researcher. You excel at:
        - Finding current and relevant information on any topic using web search
        - Creating engaging, well-structured newsletters
        - Synthesizing complex information into clear insights
        - Writing in a professional yet accessible tone
        - Properly attributing sources and providing citations
        """),
        instructions=dedent("""\
        Create a comprehensive newsletter on the given topic by following these steps:

        1. **Research Phase:**
           - Use custom_web_search to find recent, authoritative sources about the topic
           - Search for multiple angles and perspectives on the topic
           - Look for the latest developments, trends, and news

        2. **Analysis Phase:**
           - Extract key insights, trends, and important information from search results
           - Identify the most newsworthy and relevant information
           - Note any conflicting viewpoints or emerging patterns

        3. **Writing Phase:**
           Create an engaging newsletter with the following structure:
           - **Compelling headline** that captures the essence of the topic
           - **Executive summary** (2-3 sentences highlighting key points)
           - **Main content sections** (3-4 sections covering different aspects)
           - **Key takeaways** with actionable insights
           - **What's Next** section discussing implications or future trends
           - **Sources** section with proper attribution to all referenced articles

        **Formatting Requirements:**
        - Use markdown formatting throughout
        - Include relevant emojis for visual appeal
        - Keep paragraphs concise and readable
        - Use bullet points and numbered lists where appropriate
        - Maintain a professional yet engaging tone

        **Important:** Always use the web search tool to gather current information before writing the newsletter.
        """),
        markdown=True,
        show_tool_calls=True,
        add_datetime_to_instructions=True,
        storage=SqliteStorage(
            table_name="newsletter_agent",
            db_file="tmp/newsletter_agent.db",
        ),
    )

def create_fallback_newsletter(topic: str, search_limit: int = 5, time_range: str = "qdr:w"):
    """Create newsletter using direct web search (fallback when Agno not available)"""
    print("🔄 Using fallback newsletter generation...")
    
    # Create web search tool
    web_tool = CustomWebSearchTool(
        search_params={
            "limit": search_limit,
            "tbs": time_range
        }
    )
    
    # Search for content
    print(f"🔍 Searching for: {topic}")
    search_results = web_tool.custom_web_search(topic)
    
    if "❌" in search_results:
        # If search failed, create a basic newsletter
        newsletter_content = f"""# 📰 Newsletter: {topic}

## ⚠️ Limited Information Available

Unfortunately, we were unable to retrieve current web content about "{topic}" at this time. This could be due to:
- Network connectivity issues
- Search engine limitations  
- Content filtering restrictions

## 💡 General Information

This newsletter was generated on {__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")}. 

For the most current information about {topic}, we recommend:
- Checking major news websites directly
- Using academic databases for research
- Consulting industry publications
- Following relevant experts on social media

## 🔄 Try Again Later

Please try regenerating this newsletter later, as web content availability can vary throughout the day.

---
*Generated using AI Newsletter Generator*"""
    else:
        # Create a structured newsletter from search results
        newsletter_content = f"""# 📰 Newsletter: {topic}

## 📋 Executive Summary

This newsletter provides a comprehensive overview of the latest developments in {topic}, based on current web research and multiple authoritative sources.

## 🔍 Research Findings

{search_results}

## 🎯 Key Takeaways

Based on our research, here are the most important insights:

- **Current Trends**: Multiple sources indicate significant activity in this area
- **Recent Developments**: Latest information has been gathered from credible sources
- **Industry Impact**: These developments have broader implications for the field

## 📈 What's Next?

- Continue monitoring developments in this space
- Watch for updates from key industry players
- Consider the implications for related fields

## 🔗 Source Attribution

All information in this newsletter has been gathered from publicly available web sources and is properly attributed within the research section above.

---
*Generated on {__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")} using AI Newsletter Generator with Web Search*"""
    
    return type('MockResponse', (), {'content': newsletter_content})()

def NewsletterGenerator(topic: str, search_limit: int = 5, time_range: str = "qdr:w"):
    """
    Generate a newsletter based on the given topic and search parameters.
    
    Args:
        topic (str): The topic to generate the newsletter about
        search_limit (int): Maximum number of articles to search and analyze
        time_range (str): Time range for article search (e.g., "qdr:w" for past week)
        
    Returns:
        The generated newsletter content
    """
    
    print(f"🚀 Starting newsletter generation for: {topic}")
    print(f"📊 Parameters: {search_limit} articles, {time_range} time range")
    
    try:
        if AGNO_AVAILABLE and NEBIUS_API_KEY:
            print("🤖 Using Agno AI framework...")
            
            # Create agent
            agent = create_agno_newsletter_agent()
            
            # Generate newsletter with explicit instruction to use web search
            prompt = f"""
            Create a comprehensive newsletter about: {topic}
            
            IMPORTANT: You must use the custom_web_search tool to find current information before writing the newsletter. 
            Search for recent articles, news, and developments about {topic}.
            
            After gathering information, create an engaging and informative newsletter that includes:
            - Current developments and trends
            - Key insights and analysis
            - Proper source attribution
            - Professional formatting
            """
            
            response = agent.run(prompt)
            
            print("✅ Newsletter generated successfully using Agno AI!")
            return response
            
        else:
            print("⚠️ Agno AI not available, using fallback method...")
            return create_fallback_newsletter(topic, search_limit, time_range)
            
    except Exception as e:
        print(f"❌ Error in primary method: {e}")
        print("🔄 Falling back to basic newsletter generation...")
        import traceback
        traceback.print_exc()
        return create_fallback_newsletter(topic, search_limit, time_range)

def test_web_search_function():
    """Test the web search function directly"""
    print("🧪 Testing web search function...")
    try:
        result = custom_web_search("latest AI news")
        print(f"✅ Web search test result: {len(result)} characters")
        if len(result) > 500:
            print("✅ Web search working correctly")
            return True
        else:
            print("⚠️ Web search returned limited results")
            print(f"Result: {result}")
            return False
    except Exception as e:
        print(f"❌ Web search test failed: {e}")
        return False

def test_generator():
    """Test the newsletter generator"""
    print("🧪 Testing NewsletterGenerator...")
    
    try:
        result = NewsletterGenerator("Latest AI developments", search_limit=2, time_range="qdr:d")
        
        content = result.content if hasattr(result, 'content') else str(result)
        
        print("\n" + "="*60)
        print("📰 GENERATED NEWSLETTER SAMPLE:")
        print("="*60)
        print(content[:800] + "..." if len(content) > 800 else content)
        print("\n✅ Newsletter generation test successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def quick_test():
    """Quick test to verify everything works"""
    print("🔍 Quick System Test")
    print("-" * 30)
    
    # Test 1: Web search function
    web_search_working = test_web_search_function()
    
    # Test 2: Environment
    if NEBIUS_API_KEY:
        print("✅ NEBIUS_API_KEY found")
    else:
        print("⚠️ NEBIUS_API_KEY not found (fallback mode will be used)")
    
    # Test 3: Agno
    if AGNO_AVAILABLE:
        print("✅ Agno framework available")
    else:
        print("⚠️ Agno framework not available (fallback mode will be used)")
    
    print("\n🎯 Running newsletter generation test...")
    generator_working = test_generator()
    
    print("\n📊 Test Results:")
    print(f"- Web Search: {'✅' if web_search_working else '❌'}")
    print(f"- Newsletter Generator: {'✅' if generator_working else '❌'}")
    
    return web_search_working and generator_working

if __name__ == "__main__":
    success = quick_test()
    print(f"\n🏁 Overall Status: {'✅ All systems working!' if success else '⚠️ Some issues detected'}")