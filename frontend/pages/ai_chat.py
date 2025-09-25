"""
AI Chat page for the Travel Advisor app.
"""
import streamlit as st
from utils.api_client import get_api_client
import time


def show():
    """Display the AI chat page."""
    st.header("🤖 AI Travel Assistant")
    st.markdown("Ask me anything about your destinations! I can provide information from your knowledge base and current weather data.")
    
    api_client = get_api_client()
    
    # Get destinations for context selection
    destinations = api_client.get_destinations()
    
    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Destination context selection
    st.subheader("🎯 Context Selection")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        destination_options = {"No specific destination": None}
        if destinations and not isinstance(destinations, dict):
            destination_options.update({dest["name"]: dest["id"] for dest in destinations})
        
        # Check if we came from knowledge base page with a pre-selected destination
        default_destination = "No specific destination"
        if hasattr(st.session_state, 'chat_destination_name'):
            if st.session_state.chat_destination_name in destination_options:
                default_destination = st.session_state.chat_destination_name
            # Clear the session state after using it
            delattr(st.session_state, 'chat_destination_name')
            if hasattr(st.session_state, 'chat_destination_id'):
                delattr(st.session_state, 'chat_destination_id')
        
        selected_destination = st.selectbox(
            "Ask about a specific destination (optional)",
            options=list(destination_options.keys()),
            index=list(destination_options.keys()).index(default_destination),
            help="Select a destination to get context-aware responses"
        )
    
    with col2:
        if selected_destination != "No specific destination":
            destination_id = destination_options[selected_destination]
            if st.button("📊 View Context Info"):
                context_info = api_client.get_destination_context(destination_id)
                if context_info and "knowledge_entries" in context_info:
                    st.info(f"📚 {context_info['knowledge_entries']} knowledge entries available for {selected_destination}")
    
    st.markdown("---")
    
    # Chat interface
    st.subheader("💬 Chat")
    
    # Chat input
    with st.form("chat_form", clear_on_submit=True):
        user_message = st.text_area(
            "Your Question",
            placeholder="Ask me about destinations, travel tips, weather, or anything else!\n\nExamples:\n- What's the best museum to visit in Paris and how's the weather?\n- Tell me about local cuisine in Tokyo\n- What are some hidden gems in New York?",
            height=100,
            key="chat_input"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            submit_button = st.form_submit_button("🚀 Send", type="primary")
        
        with col2:
            if st.form_submit_button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
        
        with col3:
            if selected_destination != "No specific destination":
                st.caption(f"🎯 Context: {selected_destination}")
    
    # Process chat message
    if submit_button and user_message:
        destination_id = destination_options.get(selected_destination)
        
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_message,
            "destination": selected_destination if selected_destination != "No specific destination" else None,
            "timestamp": time.time()
        })
        
        # Show thinking spinner
        with st.spinner("🤔 AI is thinking..."):
            # Send to API
            response = api_client.send_chat_message(user_message, destination_id)
        
        if response and "response" in response:
            # Add AI response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response["response"],
                "sources": response.get("sources", []),
                "weather_data": response.get("weather_data"),
                "timestamp": time.time()
            })
        else:
            # Add error response
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "I apologize, but I encountered an error processing your request. Please try again.",
                "sources": [],
                "weather_data": None,
                "timestamp": time.time()
            })
        
        st.rerun()
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown("---")
        
        for message in reversed(st.session_state.chat_history[-10:]):  # Show last 10 messages
            if message["role"] == "user":
                # User message
                st.markdown(f"""
                <div class="chat-message">
                    <strong>👤 You:</strong><br>
                    {message['content']}
                    {f"<br><small>🎯 Context: {message.get('destination', 'General')}</small>" if message.get('destination') else ""}
                </div>
                """, unsafe_allow_html=True)
            
            else:
                # AI response
                st.markdown(f"""
                <div class="ai-response">
                    <strong>🤖 AI Assistant:</strong><br>
                    {message['content']}
                </div>
                """, unsafe_allow_html=True)
                
                # Show sources if available
                if message.get("sources"):
                    with st.expander("📚 Sources Used"):
                        for source in message["sources"]:
                            st.markdown(f"• {source}")
                
                # Show weather data if available
                if message.get("weather_data"):
                    weather = message["weather_data"]
                    with st.expander("🌤️ Weather Information"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Temperature", f"{weather.get('temperature', 'N/A')}°C")
                        with col2:
                            st.metric("Humidity", f"{weather.get('humidity', 'N/A')}%")
                        with col3:
                            st.metric("Conditions", weather.get('description', 'N/A'))
                        
                        if weather.get('city'):
                            st.caption(f"📍 {weather['city']}, {weather.get('country', '')}")
    
    else:
        # Welcome message when no chat history
        st.info("""
        👋 **Welcome to your AI Travel Assistant!**
        
        I can help you with:
        • **Information from your knowledge base** - Ask about destinations you've added notes for
        • **Current weather data** - Get real-time weather for any destination
        • **Travel advice** - General travel tips and recommendations
        
        **Tips for better responses:**
        • Select a specific destination for context-aware answers
        • Ask specific questions like "What's the weather like in Paris?"
        • Mention weather, museums, restaurants, or other topics in your questions
        
        Start by typing your question above! 💬
        """)
    
    # Quick action buttons
    if destinations and not isinstance(destinations, dict):
        st.markdown("---")
        st.subheader("🚀 Quick Questions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Weather Questions:**")
            for dest in destinations[:3]:  # Show first 3 destinations
                if st.button(f"🌤️ Weather in {dest['name']}", key=f"weather_{dest['id']}"):
                    # Set up the question and trigger it
                    weather_question = f"What's the current weather in {dest['name']}?"
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": weather_question,
                        "destination": dest['name'],
                        "timestamp": time.time()
                    })
                    
                    with st.spinner("Getting weather data..."):
                        response = api_client.send_chat_message(weather_question, dest['id'])
                    
                    if response and "response" in response:
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response["response"],
                            "sources": response.get("sources", []),
                            "weather_data": response.get("weather_data"),
                            "timestamp": time.time()
                        })
                    
                    st.rerun()
        
        with col2:
            st.markdown("**General Questions:**")
            for dest in destinations[:3]:  # Show first 3 destinations
                if st.button(f"📍 Tell me about {dest['name']}", key=f"about_{dest['id']}"):
                    # Set up the question and trigger it
                    general_question = f"Tell me about {dest['name']} based on my knowledge base"
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": general_question,
                        "destination": dest['name'],
                        "timestamp": time.time()
                    })
                    
                    with st.spinner("Gathering information..."):
                        response = api_client.send_chat_message(general_question, dest['id'])
                    
                    if response and "response" in response:
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response["response"],
                            "sources": response.get("sources", []),
                            "weather_data": response.get("weather_data"),
                            "timestamp": time.time()
                        })
                    
                    st.rerun()
    
    # Chat statistics
    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("📊 Chat Statistics")
        
        user_messages = [msg for msg in st.session_state.chat_history if msg["role"] == "user"]
        ai_messages = [msg for msg in st.session_state.chat_history if msg["role"] == "assistant"]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Messages Exchanged", len(st.session_state.chat_history))
        
        with col2:
            st.metric("Your Questions", len(user_messages))
        
        with col3:
            sources_used = sum([len(msg.get("sources", [])) for msg in ai_messages])
            st.metric("Sources Referenced", sources_used)
