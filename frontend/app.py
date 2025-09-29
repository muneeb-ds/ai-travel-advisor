"""
AI Travel Advisor - Streamlit Frontend
"""

import streamlit as st
from datetime import datetime, timedelta
from utils.api_client import get_api_client


# Page configuration
st.set_page_config(
    page_title="AI Travel Advisor",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better visibility and color scheme
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        color: #1e40af;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Navigation styling */
    .nav-link {
        padding: 0.5rem 1rem;
        margin: 0.25rem 0;
        border-radius: 0.5rem;
        text-decoration: none;
        transition: background-color 0.3s;
    }
    .nav-link:hover {
        background-color: #e0e7ff;
    }
    
    /* User info box with better contrast */
    .user-info {
        padding: 1rem;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Chat message styling */
    .user-message {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1d4ed8;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .ai-message {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white;
        padding: 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #3730a3;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Better contrast for text elements */
    .stMarkdown {
        color: #1f2937;
    }
    
    /* Sidebar styling improvements */
    .css-1d391kg {
        background-color: #f8fafc;
    }
    
    /* Navigation and sidebar text improvements */
    .css-1d391kg .stMarkdown {
        color: #1f2937;
    }
    
    /* Make sure sidebar text is visible */
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
        color: #1f2937;
    }
    
    /* Main content area text */
    .main .stMarkdown {
        color: #1f2937;
    }
    
    /* Button improvements */
    .stButton button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Success/Error message improvements */
    .stSuccess {
        background-color: #dcfce7;
        border-left: 4px solid #16a34a;
        color: #166534;
    }
    
    .stError {
        background-color: #fef2f2;
        border-left: 4px solid #dc2626;
        color: #991b1b;
    }
    
    /* Info message improvements */
    .stInfo {
        background-color: #dbeafe;
        border-left: 4px solid #2563eb;
        color: #1e40af;
    }
    
    /* Expander improvements */
    .streamlit-expanderHeader {
        background-color: #f1f5f9;
        border-radius: 0.5rem;
    }
    
    /* Form improvements */
    .stTextInput > div > div > input {
        border: 2px solid #e2e8f0;
        border-radius: 0.5rem;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Progress bar styling */
    .stProgress .st-bo {
        background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
    }
    
    /* SIMPLE FIX - MAKE ALL TEXT WHITE */
    
    /* Force ALL text elements to be WHITE */
    * {
        color: white !important;
    }
    
    /* All text elements white */
    .main .stMarkdown, 
    .main .stMarkdown *,
    .css-1d391kg,
    .css-1d391kg *,
    .sidebar *,
    h1, h2, h3, h4, h5, h6,
    p, div, span, text, label,
    .stMarkdown,
    .stText,
    .stCaption,
    .stSubheader,
    .stTitle,
    .element-container,
    .element-container * {
        color: white !important;
    }
    
    /* All Streamlit containers - white text */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] *,
    [data-testid="stMain"],
    [data-testid="stMain"] * {
        color: white !important;
    }
    
    /* Buttons - white text on colored backgrounds */
    .stButton button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Auth"


def check_authentication():
    """Check if user is authenticated and token is valid."""
    if not st.session_state.get("authenticated"):
        return False
    
    # Check if token exists
    if not st.session_state.get("access_token"):
        st.session_state.authenticated = False
        return False

    # Check if token is expired (with 5 min buffer)
    if "token_expires_at" in st.session_state:
        expires_at = st.session_state.token_expires_at
        if isinstance(expires_at, str):
            # Handle string datetime
            expires_at = datetime.fromisoformat(expires_at)
        
        if datetime.now() + timedelta(minutes=5) > expires_at:
            # Token will expire soon, try refresh
            api_client = get_api_client()
            try:
                success = api_client._refresh_token()
                if not success:
                    st.session_state.authenticated = False
                    return False
            except:
                st.session_state.authenticated = False
                return False
    
    return True


def handle_logout():
    """Handle user logout."""
    api_client = get_api_client()
    try:
        api_client.logout()
    except:
        pass  # Ignore logout errors
    
    # Clear session state
    for key in list(st.session_state.keys()):
        if key not in ["current_page"]:  # Keep page state
            del st.session_state[key]

        st.session_state.authenticated = False
    st.session_state.current_page = "Auth"
    st.rerun()


def render_sidebar():
    """Render the sidebar navigation."""
    with st.sidebar:
        st.markdown('<div class="main-header" style="color: white !important;">✈️ Travel Advisor</div>', unsafe_allow_html=True)
        
        if check_authentication():
            # Show user info
            if st.session_state.user_info:
                user = st.session_state.user_info
                st.markdown(f"""
                <div class="user-info" style="padding: 1rem; background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white !important; border-radius: 0.75rem; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <strong style="color: white !important;">👤 {user.get('email', 'User')}</strong><br>
                    <small style="color: #e0e7ff !important;">Role: {user.get('role', 'Unknown')}</small>
                </div>
                """, unsafe_allow_html=True)
            
            # Navigation menu
            st.markdown('<h3 style="color: white !important;">📋 Navigation</h3>', unsafe_allow_html=True)
            
            pages = [
                ("🏠 Destinations", "Destinations"),
                ("📚 Knowledge Base", "Knowledge"),
                ("🤖 AI Planner", "Plan"),
            ]
            
            for label, page_key in pages:
                if st.button(label, key=f"nav_{page_key}", use_container_width=True):
                    st.session_state.current_page = page_key
                    st.rerun()

            st.markdown("---")

            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                handle_logout()

        else:
            st.markdown('<h3 style="color: white !important;">🔐 Please login to continue</h3>', unsafe_allow_html=True)
            if st.button("Go to Login", use_container_width=True):
                st.session_state.current_page = "Auth"
                st.rerun()


def main():
    """Main application entry point."""
    init_session_state()

    # Render sidebar
    render_sidebar()
    
    # Main content area
    is_authenticated = check_authentication()
    
    # If not authenticated, force to Auth page
    if not is_authenticated:
        st.session_state.current_page = "Auth"
    
    # Import and render pages
    current_page = st.session_state.get("current_page", "Auth")
    
    if current_page == "Auth":
        from pages.auth import render_auth_page
        render_auth_page()
    elif current_page == "Destinations":
        from pages.destinations import render_destinations_page
        render_destinations_page()
    elif current_page == "Knowledge":
        from pages.knowledge_base import render_knowledge_page
        render_knowledge_page()
    elif current_page == "Plan":
        from pages.plan import render_plan_page
        render_plan_page()
    else:
        st.error("Page not found!")


if __name__ == "__main__":
    main()