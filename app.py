import streamlit as st
import os
from dotenv import load_dotenv
import nest_asyncio
import asyncio
from main import NewsletterGenerator

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables (local dev fallback)
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
    .main { padding: 2rem; }
    .stButton>button { width: 100%; }
    .newsletter-content { background-color: #f8f9fa; padding: 2rem; border-radius: 10px; margin-top: 2rem; }
    .topic-input { margin-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("📰 AI Newsletter Generator with NewsAPI 🔥")
st.markdown("""
Generate professional newsletters on any topic using Nebius AI, Agno, and NewsAPI.
""")

# Example topics
example_topics = [
    "What happened in the world of AI this week?",
    "What are the latest trends in AI?",
    "Tell the Recent Model Releases",
    "Recap of Google I/O 2025",
]

# Sidebar for settings (no API keys)
with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown("### 📚 Example Topics")
    for topic in example_topics:
        if st.button(topic, key=topic):
            st.session_state.topic = topic

# Main content area
topic = st.text_input(
    "What would you like to generate a newsletter about?",
    value=st.session_state.get("topic", ""),
    placeholder="Enter a topic or select from examples",
    key="topic_input"
)

col1, col2 = st.columns(2)
with col1:
    search_limit = st.number_input(
        "Number of Articles",
        min_value=1,
        max_value=10,
        value=5,
        help="Maximum number of articles to search and analyze"
    )
with col2:
    time_range = st.selectbox(
        "Time Range",
        options=[
            ("Past hour", "qdr:h"),
            ("Past 24 hours", "qdr:d"),
            ("Past week", "qdr:w"),
            ("Past month", "qdr:m"),
            ("Past year", "qdr:y")
        ],
        format_func=lambda x: x[0],
        index=2,  # Default to "Past week"
        help="Time range for article search"
    )

# Generate button
async def generate_newsletter_async(topic, search_limit, time_range):
    if not topic:
        st.error("Please enter a topic or select one from the examples.")
        return None
    if not os.getenv("NEBIUS_API_KEY") or not os.getenv("NEWSAPI_API_KEY"):
        st.error("API keys are not configured. Please set them in Streamlit secrets.")
        return None
    
    with st.spinner("Generating your newsletter..."):
        try:
            # Call NewsletterGenerator directly, no need for .run() here
            response = NewsletterGenerator(topic=topic, search_limit=search_limit, time_range=time_range[1])
            return response  # Return the RunResponse object
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            return None

def generate_newsletter():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(generate_newsletter_async(topic, search_limit, time_range))
    if response:
        url_safe_topic = topic.lower().replace(" ", "-")
        st.markdown("### 📝 Generated Newsletter")
        st.markdown(response.content)  # Access content directly
        st.download_button(
            label="📥 Download Newsletter",
            data=response.content,
            file_name=f"newsletter-{url_safe_topic}.md",
            mime="text/markdown"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with ❤️ using Streamlit and Nebius AI</p>
</div>
""", unsafe_allow_html=True)

if st.button("Generate Newsletter", type="primary"):
    generate_newsletter()   