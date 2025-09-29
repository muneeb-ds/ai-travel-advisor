"""
Authentication page with login and signup functionality.
"""

import streamlit as st
from datetime import datetime, timedelta
from utils.api_client import get_api_client


def render_auth_page():
    """Render the authentication page with login/signup tabs."""
    st.markdown('<div class="main-header">🔐 Authentication</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
    
    with tab1:
        render_login_form()
    
    with tab2:
        render_signup_form()


def render_login_form():
    """Render the login form."""
    st.subheader("Welcome Back!")
    st.write("Please sign in to continue to your travel planning dashboard.")
    
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "Email Address",
            placeholder="your.email@example.com",
            help="Enter your registered email address"
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            help="Enter your account password"
        )
        
        col1, col2 = st.columns([1, 2])
        with col1:
            submit = st.form_submit_button("🚀 Login", use_container_width=True)
        
        if submit:
            if not email or not password:
                st.error("⚠️ Please fill in all fields.")
                return
            
            try:
                with st.spinner("🔐 Authenticating..."):
                    api_client = get_api_client()
                    token_data = api_client.login(email, password)
                    
                    # Store authentication data
                    st.session_state.access_token = token_data["access_token"]
                    st.session_state.refresh_token = token_data["refresh_token"]
                    st.session_state.token_expires_at = datetime.now() + timedelta(
                        seconds=token_data["expires_in"]
                    )
                    st.session_state.authenticated = True
                    
                    # Get user info
                    user_info = api_client.get_me()
                    st.session_state.user_info = user_info
                    
                    # Redirect to destinations page
                    st.session_state.current_page = "Destinations"
                    st.success("✅ Login successful! Redirecting...")
                    # Force immediate rerun to trigger navigation
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Login failed: {str(e)}")


def render_signup_form():
    """Render the signup form."""
    st.subheader("Create Your Account")
    st.write("Join AI Travel Advisor to start planning amazing trips!")
    
    with st.form("signup_form", clear_on_submit=False):
        email = st.text_input(
            "Email Address",
            placeholder="your.email@example.com",
            help="We'll use this to send you travel recommendations"
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Choose a strong password",
            help="Minimum 8 characters required"
        )
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter your password"
        )
        org_name = st.text_input(
            "Organization Name",
            placeholder="Your Company or Personal",
            help="This helps organize your travel plans"
        )
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            submit = st.form_submit_button("🎯 Create Account", use_container_width=True)
        
        if submit:
            # Validation
            errors = []
            
            if not email or not password or not org_name:
                errors.append("⚠️ Please fill in all fields.")
            
            if len(password) < 8:
                errors.append("⚠️ Password must be at least 8 characters long.")
            
            if password != confirm_password:
                errors.append("⚠️ Passwords do not match.")
            
            if "@" not in email or "." not in email.split("@")[1]:
                errors.append("⚠️ Please enter a valid email address.")
            
            if errors:
                for error in errors:
                    st.error(error)
                return
            
            try:
                with st.spinner("🎯 Creating your account..."):
                    api_client = get_api_client()
                    auth_data = api_client.signup(email, password, org_name)
                    
                    # Store authentication data
                    tokens = auth_data["tokens"]
                    st.session_state.access_token = tokens["access_token"]
                    st.session_state.refresh_token = tokens["refresh_token"]
                    st.session_state.token_expires_at = datetime.now() + timedelta(
                        seconds=tokens["expires_in"]
                    )
                    st.session_state.authenticated = True
                    st.session_state.user_info = auth_data["user"]
                    
                    # Redirect to destinations page
                    st.session_state.current_page = "Destinations"
                    st.success("✅ Account created successfully! Welcome aboard!")
                    # Force immediate rerun to trigger navigation
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Account creation failed: {str(e)}")


def logout_user():
    """Handle user logout."""
    try:
        api_client = get_api_client()
        api_client.logout()
    except:
        pass  # Ignore logout errors
    
    # Clear session state
    keys_to_keep = ["current_page"]  # Keep navigation state
    keys_to_clear = [key for key in st.session_state.keys() if key not in keys_to_keep]
    
    for key in keys_to_clear:
        del st.session_state[key]
    
    st.session_state.authenticated = False
    st.session_state.current_page = "Auth"
    st.success("👋 You have been logged out successfully!")
    st.rerun()
