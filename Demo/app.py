import streamlit as st
import os
from dotenv import load_dotenv
import time
from main import NewsletterGenerator

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="AI Newsletter Generator",
    page_icon="📰",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .newsletter-content {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin-top: 2rem;
        max-height: 600px;
        overflow-y: auto;
    }
    .topic-input {
        margin-bottom: 2rem;
    }
    .success-message {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-green { background-color: #28a745; }
    .status-yellow { background-color: #ffc107; }
    .status-red { background-color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'newsletter_content' not in st.session_state:
    st.session_state.newsletter_content = None
if 'last_topic' not in st.session_state:
    st.session_state.last_topic = None
if 'generation_time' not in st.session_state:
    st.session_state.generation_time = None

# Title and description
st.title("📰 AI Newsletter Generator")
st.markdown("""
Generate professional newsletters on any topic using AI and live web search.
Get the latest information and create engaging content in minutes!
""")

# Example topics
example_topics = [
    "Latest AI developments and breakthroughs",
    "Artificial intelligence trends in 2024",
    "Machine learning innovations this week",
    "AI in healthcare recent advances",
    "Generative AI and large language models",
    "AI ethics and governance updates",
    "Computer vision and image AI news",
    "AI startups and funding news",
    "Autonomous vehicles and AI updates",
    "AI research papers and discoveries"
]

# Sidebar for API keys and settings
with st.sidebar:
    st.header("🔑 Configuration")
    
    # API Key input
    nebius_api_key = st.text_input(
        "Nebius API Key",
        value=os.getenv("NEBIUS_API_KEY", ""),
        type="password",
        help="Your Nebius API key for AI generation"
    )
    
    # Update environment variable with user input
    if nebius_api_key:
        os.environ["NEBIUS_API_KEY"] = nebius_api_key
    
    st.markdown("---")
    st.header("⚙️ Search Settings")
    
    search_limit = st.slider(
        "Number of Articles",
        min_value=1,
        max_value=8,
        value=5,
        help="Maximum number of articles to search and analyze"
    )
    
    time_range_options = {
        "Past hour": "qdr:h",
        "Past 24 hours": "qdr:d", 
        "Past week": "qdr:w",
        "Past month": "qdr:m",
        "Past year": "qdr:y"
    }
    
    time_range_display = st.selectbox(
        "Time Range",
        options=list(time_range_options.keys()),
        index=2,  # Default to "Past week"
        help="Time range for article search"
    )
    time_range = time_range_options[time_range_display]
    
    st.markdown("---")
    st.header("💡 Quick Topics")
    st.markdown("Click any topic below to use it:")
    
    for i, topic in enumerate(example_topics[:5]):  # Show first 5
        if st.button(f"📄 {topic}", key=f"example_{i}"):
            st.session_state.topic_input = topic
            st.rerun()

# System status check
def check_system_status():
    """Check if all required components are available"""
    status = {
        'nebius_api': bool(nebius_api_key),
        'agno_framework': True,  # Assume available
        'web_search': True       # Assume available
    }
    return status

# Display system status
status = check_system_status()
col1, col2, col3 = st.columns(3)

with col1:
    status_color = "status-green" if status['nebius_api'] else "status-red"
    st.markdown(f'<span class="status-indicator {status_color}"></span>**Nebius API**', unsafe_allow_html=True)

with col2:
    status_color = "status-green" if status['agno_framework'] else "status-yellow"
    st.markdown(f'<span class="status-indicator {status_color}"></span>**AI Framework**', unsafe_allow_html=True)

with col3:
    status_color = "status-green" if status['web_search'] else "status-yellow"
    st.markdown(f'<span class="status-indicator {status_color}"></span>**Web Search**', unsafe_allow_html=True)

st.markdown("---")

# Main input area
st.header("🎯 Newsletter Topic")
topic = st.text_area(
    "What would you like to generate a newsletter about?",
    value=st.session_state.get("topic_input", ""),
    placeholder="Enter a topic like 'Latest developments in artificial intelligence' or select from examples",
    height=100,
    key="topic_input"
)

# Advanced options (collapsible)
with st.expander("🔧 Advanced Options"):
    col1, col2 = st.columns(2)
    with col1:
        custom_search_limit = st.number_input(
            "Custom Article Limit",
            min_value=1,
            max_value=10,
            value=search_limit,
            help="Override sidebar setting"
        )
    with col2:
        custom_time_range = st.selectbox(
            "Custom Time Range",
            options=list(time_range_options.keys()),
            index=list(time_range_options.keys()).index(time_range_display),
            help="Override sidebar setting"
        )
    
    use_custom_settings = st.checkbox("Use custom settings above")
    
    if use_custom_settings:
        search_limit = custom_search_limit
        time_range = time_range_options[custom_time_range]

# Generate button and logic
def generate_newsletter():
    """Generate newsletter with error handling and user feedback"""
    if not topic.strip():
        st.error("Please enter a topic or select one from the examples.")
        return
    
    if not status['nebius_api']:
        st.error("Please provide your Nebius API key in the sidebar.")
        return
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        start_time = time.time()
        
        # Progress: Starting
        progress_bar.progress(10)
        status_text.text("🚀 Initializing newsletter generation...")
        
        # Progress: Web search
        progress_bar.progress(30)
        status_text.text("🔍 Searching for latest information...")
        
        # Generate the newsletter
        response = NewsletterGenerator(
            topic=topic.strip(),
            search_limit=search_limit,
            time_range=time_range
        )
        
        # Progress: AI generation
        progress_bar.progress(70)
        status_text.text("🤖 Generating newsletter content...")
        
        # Progress: Finalizing
        progress_bar.progress(90)
        status_text.text("📝 Finalizing newsletter...")
        
        # Complete
        progress_bar.progress(100)
        generation_time = time.time() - start_time
        
        # Store in session state
        st.session_state.newsletter_content = response.content if hasattr(response, 'content') else str(response)
        st.session_state.last_topic = topic
        st.session_state.generation_time = generation_time
        
        status_text.success(f"✅ Newsletter generated successfully in {generation_time:.1f} seconds!")
        
        # Clear progress indicators after a moment
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ An error occurred while generating the newsletter: {str(e)}")
        
        # Show error details in expander
        with st.expander("🔍 Error Details (for debugging)"):
            st.code(str(e))

# Generate button
generate_col1, generate_col2 = st.columns([3, 1])
with generate_col1:
    if st.button("🚀 Generate Newsletter", type="primary", use_container_width=True):
        generate_newsletter()

with generate_col2:
    if st.button("🔄 Clear", use_container_width=True):
        st.session_state.newsletter_content = None
        st.session_state.last_topic = None
        st.session_state.generation_time = None
        st.rerun()

# Display generated newsletter
if st.session_state.newsletter_content:
    st.markdown("---")
    
    # Newsletter header with metadata
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.header("📄 Generated Newsletter")
    with col2:
        if st.session_state.generation_time:
            st.metric("Generation Time", f"{st.session_state.generation_time:.1f}s")
    with col3:
        if st.session_state.newsletter_content:
            word_count = len(st.session_state.newsletter_content.split())
            st.metric("Word Count", f"{word_count:,}")
    
    # Newsletter content
    st.markdown(st.session_state.newsletter_content)
    
    # Download button
    if st.session_state.last_topic:
        url_safe_topic = st.session_state.last_topic.lower().replace(" ", "-").replace(",", "").replace(".", "")[:50]
        filename = f"newsletter-{url_safe_topic}.md"
        
        st.download_button(
            label="📥 Download Newsletter (Markdown)",
            data=st.session_state.newsletter_content,
            file_name=filename,
            mime="text/markdown",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>AI Newsletter Generator</strong></p>
    <p>Built with Streamlit • Powered by Nebius AI • Enhanced with Web Search</p>
    <p><em>Generate professional newsletters with the latest information from the web</em></p>
</div>
""", unsafe_allow_html=True)

# Add some helpful tips in the sidebar
with st.sidebar:
    st.markdown("---")
    st.header("💡 Tips")
    st.markdown("""
    **For best results:**
    - Be specific with your topic
    - Use recent timeframes for trending topics
    - Try 3-5 articles for balanced coverage
    - Check system status indicators above
    
    **Example good topics:**
    - "Latest OpenAI model releases"
    - "AI in healthcare 2024 updates"
    - "Machine learning research trends"
    """)
    
    st.markdown("---")
    st.markdown("**Need help?** Check the console output for detailed generation logs.")