"""
Main Streamlit application for AI Travel Advisor.
"""
import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Travel Advisor",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .destination-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
    
    .knowledge-entry {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 0.5rem 0;
    }
    
    .chat-message {
        background: #f5f5f5;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .ai-response {
        background: #e8f5e8;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4caf50;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>✈️ AI Travel Advisor</h1>
    <p>Discover, Learn, and Explore with AI-Powered Travel Insights</p>
</div>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["🏠 Destinations", "📚 Knowledge Base", "🤖 AI Chat"]
)

# Import pages
from pages import destinations, knowledge_base, ai_chat

# Page routing
if page == "🏠 Destinations":
    destinations.show()
elif page == "📚 Knowledge Base":
    knowledge_base.show()
elif page == "🤖 AI Chat":
    ai_chat.show()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**AI Travel Advisor v1.0**")
st.sidebar.markdown("Built with Streamlit & FastAPI")
