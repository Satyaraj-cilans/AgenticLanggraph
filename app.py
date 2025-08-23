import streamlit as st
import os
from dotenv import load_dotenv
import requests
import json

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
    }
    .topic-input {
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("📰 AI Newsletter Generator with NewsAPI!! 🔥")
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

# Initialize session state
if 'topic' not in st.session_state:
    st.session_state.topic = ""

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    st.markdown("### 📚 Example Topics")
    for topic in example_topics:
        if st.button(topic, key=f"example_{topic}"):
            st.session_state.topic = topic
            st.rerun()

# Main content area
topic = st.text_input(
    "What would you like to generate a newsletter about?",
    value=st.session_state.topic,
    placeholder="Enter a topic or select from examples",
    key="topic_input"
)

# Update session state when topic changes
if topic != st.session_state.topic:
    st.session_state.topic = topic

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
    time_range_options = [
        ("Past hour", "qdr:h"),
        ("Past 24 hours", "qdr:d"),
        ("Past week", "qdr:w"),
        ("Past month", "qdr:m"),
        ("Past year", "qdr:y")
    ]
    
    time_range_selection = st.selectbox(
        "Time Range",
        options=time_range_options,
        format_func=lambda x: x[0],
        index=2,  # Default to "Past week"
        help="Time range for article search"
    )

# FastAPI endpoint URL - Use different URLs for Docker vs local development
import platform
import socket

# def get_api_url():
#     """Determine the correct API URL based on the environment"""
#     # Check if we're running in Docker
#     try:
#         # Try to resolve 'api' hostname (Docker Compose service name)
#         socket.gethostbyname('api')
#         return "http://api:8000/generate_newsletter"
#     except socket.gaierror:
#         # Not in Docker or Docker Compose, try localhost
#         return "http://localhost:8000/generate_newsletter"

def get_api_url():
    """Get API URL from environment variable or fallback"""
    return os.getenv("API_URL", "http://localhost:8000/generate_newsletter")

API_URL = get_api_url()
st.write(f"Using API URL: {API_URL}")  # Debug info

def generate_newsletter():
    """Generate newsletter by calling FastAPI endpoint"""
    current_topic = st.session_state.topic or topic
    
    if not current_topic.strip():
        st.error("Please enter a topic or select one from the examples.")
        return
    
    # Show loading spinner
    with st.spinner("Generating your newsletter..."):
        try:
            # Prepare payload
            payload = {
                "topic": current_topic.strip(),
                "search_limit": search_limit,
                "time_range": time_range_selection[1]
            }
            
            # Debug: Show what we're sending
            with st.expander("Debug: Request Details", expanded=False):
                st.json(payload)
                st.write(f"API URL: {API_URL}")
            
            # Try multiple API URLs in case of connection issues
            api_urls = [
                API_URL,
                "http://localhost:8000/generate_newsletter",
                "http://127.0.0.1:8000/generate_newsletter",
                "http://host.docker.internal:8000/generate_newsletter"  # For Docker Desktop
            ]
            
            response = None
            last_error = None
            
            for url in api_urls:
                try:
                    st.write(f"Trying {url}...")
                    response = requests.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=120
                    )
                    response.raise_for_status()
                    st.success(f"✅ Connected to API at {url}")
                    break
                except Exception as e:
                    last_error = e
                    # st.warning(f"❌ Failed to connect to {url}: {str(e)}")
                    continue
            
            if not response:
                raise last_error or Exception("Could not connect to any API endpoint")
            
            # Parse response
            data = response.json()
            newsletter_content = data.get("newsletter")
            
            if newsletter_content:
                # Display the newsletter
                st.markdown("### 📝 Generated Newsletter")
                st.markdown(newsletter_content)
                
                # Create download button
                url_safe_topic = current_topic.lower().replace(" ", "-").replace("?", "").replace("!", "")
                st.download_button(
                    label="📥 Download Newsletter",
                    data=newsletter_content,
                    file_name=f"newsletter-{url_safe_topic}.md",
                    mime="text/markdown"
                )
                
                # Success message
                st.success("Newsletter generated successfully!")
            else:
                st.error("No newsletter content received from the API.")
                
        except requests.exceptions.Timeout:
            st.error("Request timed out. The newsletter generation is taking too long. Please try again.")
            
        except requests.exceptions.ConnectionError as e:
            st.error(f"""
            **Connection Error:** Could not connect to the API server.
            
            **Troubleshooting steps:**
            1. Make sure the FastAPI server is running
            2. Check if you can access http://localhost:8000/health in your browser
            3. If using Docker, make sure both containers are running
            4. Try restarting the API server
            
            **Error details:** {str(e)}
            """)
            
        except requests.exceptions.HTTPError as e:
            st.error(f"API request failed with status {e.response.status_code}: {e.response.text}")
            
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            st.write("Please check the debug information above and try again.")

# Generate button
if st.button("🚀 Generate Newsletter", type="primary"):
    generate_newsletter()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with ❤️ using Streamlit and Nebius AI</p>
    <p><small>Make sure your FastAPI server is running on port 8000</small></p>
</div>
""", unsafe_allow_html=True)