"""
AI Planning page with chat interface and sidebar for tools, citations, constraints and decisions.
"""

import streamlit as st
import uuid
from datetime import datetime
from utils.api_client import get_api_client


def render_plan_page():
    """Render the AI planning page with chat interface."""
    st.markdown('<div class="main-header">🤖 AI Travel Planner</div>', unsafe_allow_html=True)
    st.write("Chat with our AI travel advisor to plan your perfect trip. Ask questions, get recommendations, and build detailed itineraries.")
    
    # Add helpful tips and API info
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.expander("💡 Tips for Better Planning Results", expanded=False):
            st.write("**For faster, more accurate responses:**")
            st.write("• Be specific about dates, budget, and preferences")
            st.write("• Start with one destination at a time")
            st.write("• Ask focused questions rather than very broad requests")
            st.write("• Include constraints like budget, time, or special interests")
            st.write("")
            st.write("**Example good requests:**")
            st.code("Plan a 3-day Tokyo itinerary for $1000 with focus on traditional culture")
            st.code("What are the best restaurants in Paris for a romantic dinner under €100?")
            st.code("Create a family-friendly London itinerary for 5 days in December")
    
    with col2:
        with st.expander("🔍 Expected API Response Structure", expanded=False):
            st.write("**The API should return:**")
            st.code("""{
  "answer_markdown": "Detailed markdown response",
  "itinerary": {
    "days": [
      {
        "date": "2024-01-01",
        "items": [
          {
            "start": "09:00",
            "end": "12:00", 
            "title": "Activity title",
            "location": "Location name",
            "notes": "Additional notes"
          }
        ]
      }
    ],
    "total_cost_usd": 1500.0
  },
  "citations": [
    {
      "title": "Source title",
      "source": "url|manual|file|tool",
      "ref": "reference_id"
    }
  ],
  "tools_used": [
    {
      "name": "tool_name",
      "count": 3,
      "total_ms": 1500
    }
  ],
  "decisions": [
    "Chose option A over B because...",
    "Selected hotel X due to budget constraints"
  ],
  "thread_id": "conversation_uuid"
}""", language="json")
    
    # Initialize chat session
    initialize_chat_session()
    
    # Main layout: Chat area + Sidebar
    col_chat, col_sidebar = st.columns([2, 1])
    
    with col_chat:
        render_chat_interface()
    
    with col_sidebar:
        render_planning_sidebar()


def initialize_chat_session():
    """Initialize chat session variables."""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    
    if 'current_planning_data' not in st.session_state:
        st.session_state.current_planning_data = {
            'tools_used': [],
            'citations': [],
            'decisions': [],
            'constraints': {},
            'itinerary': {}
        }


def render_chat_interface():
    """Render the main chat interface."""
    st.subheader("💬 Chat with AI Planner")
    
    # Chat history container
    chat_container = st.container()
    
    with chat_container:
        render_chat_history()
    
    # Chat input
    render_chat_input()
    
    # Chat controls
    render_chat_controls()


def render_chat_history():
    """Render the chat message history."""
    if not st.session_state.chat_history:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: white; padding: 2rem; border-radius: 1rem; margin: 1rem 0; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h3 style="margin: 0 0 1rem 0; color: white;">👋 Welcome to the AI Travel Planner!</h3>
            <p style="margin: 0 0 1rem 0; color: #e0e7ff;">Start by asking me about your travel plans. Here are some examples:</p>
            <div style="background: rgba(255, 255, 255, 0.1); padding: 1rem; border-radius: 0.5rem; text-align: left; margin-top: 1rem;">
                <div style="margin: 0.5rem 0;">💡 'Plan a 5-day trip to Paris with a budget of $2000'</div>
                <div style="margin: 0.5rem 0;">🍜 'What are the best restaurants in Tokyo?'</div>
                <div style="margin: 0.5rem 0;">🏛️ 'Help me create an itinerary for Rome'</div>
                <div style="margin: 0.5rem 0;">🏖️ 'Plan a family vacation to Bali for 7 days'</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    for i, message in enumerate(st.session_state.chat_history):
        render_chat_message(message, i)


def render_chat_message(message, index):
    """Render a single chat message."""
    timestamp = datetime.fromisoformat(message['timestamp']).strftime('%I:%M %p')
    
    if message['role'] == 'user':
        # User message with improved styling
        st.markdown(f"""
        <div class="user-message">
            <strong>🧑 You</strong> <small style="color: #e0e7ff; opacity: 0.8;">({timestamp})</small><br>
            <div style="margin-top: 0.5rem; font-size: 1rem;">
                {message['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # AI message header with improved styling
        st.markdown(f"""
        <div class="ai-message">
            <strong>🤖 AI Travel Advisor</strong> <small style="color: #e0e7ff; opacity: 0.8;">({timestamp})</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Display AI response content in a container with good contrast
        with st.container():
            st.markdown(f"""
            <div style="background-color: #1f2937; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; border: 1px solid #374151; color: white;">
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
        
        # If this is the latest AI message, update sidebar data
        if index == len(st.session_state.chat_history) - 1 and 'metadata' in message:
            st.session_state.current_planning_data = message['metadata']
        
        # Show itinerary if available
        if 'metadata' in message and message['metadata'].get('itinerary'):
            render_itinerary_preview(message['metadata']['itinerary'])


def render_itinerary_preview(itinerary):
    """Render a compact itinerary preview in the chat."""
    if not itinerary or not itinerary.get('days'):
        return
    
    with st.expander("🗓️ **Generated Itinerary Preview**", expanded=False):
        # Create a styled container for the itinerary
        st.markdown("""
        <div style="background-color: #1f2937; border: 1px solid #374151; border-radius: 0.75rem; padding: 1rem; margin: 0.5rem 0;">
        """, unsafe_allow_html=True)
        
        total_cost = itinerary.get('total_cost_usd', 0)
        if total_cost > 0:
            st.markdown(f"<div style='color: #10b981; font-weight: bold; margin-bottom: 1rem;'>💰 **Estimated Total Cost:** ${total_cost:,.2f}</div>", unsafe_allow_html=True)
        
        for day in itinerary['days']:
            st.markdown(f"<div style='color: #60a5fa; font-weight: bold; margin: 1rem 0 0.5rem 0;'>📅 {day['date']}</div>", unsafe_allow_html=True)
            
            for item in day['items']:
                location_text = f" at {item['location']}" if item.get('location') else ""
                time_text = ""
                if item.get('start') and item.get('end'):
                    time_text = f" ({item['start']} - {item['end']})"
                elif item.get('start'):
                    time_text = f" (from {item['start']})"
                
                st.markdown(f"<div style='color: #e5e7eb; margin-left: 1rem; margin: 0.25rem 0;'>• {item['title']}{location_text}{time_text}</div>", unsafe_allow_html=True)
                
                if item.get('notes'):
                    st.markdown(f"<div style='color: #9ca3af; font-style: italic; margin-left: 2rem; font-size: 0.9rem;'>💡 {item['notes']}</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)


def render_chat_input():
    """Render the chat input area."""
    st.markdown("---")
    
    # Chat input form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Your message:",
            placeholder="Ask me about your travel plans... e.g., 'Plan a weekend trip to Barcelona'",
            height=100,
            help="Describe your travel needs, ask questions, or request specific recommendations"
        )
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            submit = st.form_submit_button("🚀 Send", use_container_width=True)
        
        if submit and user_input.strip():
            handle_user_message(user_input.strip())


def handle_user_message(user_input):
    """Handle a new user message."""
    # Add user message to history
    st.session_state.chat_history.append({
        'role': 'user',
        'content': user_input,
        'timestamp': datetime.now().isoformat()
    })
    
    try:
        # Create a progress container
        progress_container = st.empty()
        
        with progress_container.container():
            st.info("🤖 **AI Travel Planner is working on your request...**")
            st.write("⏱️ *This may take 2-5 minutes for complex itineraries*")
            st.write("🔍 The AI is:")
            st.write("• Searching knowledge base for relevant information")
            st.write("• Analyzing travel constraints and preferences") 
            st.write("• Planning optimal routes and activities")
            st.write("• Generating detailed recommendations")
            
            # # Show a progress bar
            # progress_bar = st.progress(0)
            # status_text = st.empty()
            
            # import time
            # import threading
            
            # # Simulate progress updates (since we can't get real progress from backend)
            # def update_progress():
            #     for i in range(101):
            #         progress_bar.progress(i)
            #         if i < 20:
            #             status_text.text("🔍 Searching knowledge base...")
            #         elif i < 40:
            #             status_text.text("🧠 AI is analyzing your request...")
            #         elif i < 60:
            #             status_text.text("🗺️ Planning routes and activities...")
            #         elif i < 80:
            #             status_text.text("📋 Generating detailed itinerary...")
            #         else:
            #             status_text.text("✨ Finalizing recommendations...")
            #         time.sleep(0.1)  # Very fast updates for smooth animation
            
            # # Start progress animation in background
            # progress_thread = threading.Thread(target=update_progress, daemon=True)
            # progress_thread.start()
        
        # Make the actual API call
        api_client = get_api_client()
        response = api_client.plan_itinerary(
            query=user_input,
            thread_id=st.session_state.thread_id
        )
        
        # Clear the progress display
        progress_container.empty()
        
        # Process response
        ai_response = {
            'role': 'assistant',
            'content': response.get('answer_markdown', 'I apologize, but I could not generate a response.'),
            'timestamp': datetime.now().isoformat(),
            'metadata': {
                'itinerary': response.get('itinerary', {}),
                'citations': response.get('citations', []),
                'tools_used': response.get('tools_used', []),
                'decisions': response.get('decisions', []),
                'thread_id': response.get('thread_id', st.session_state.thread_id),
                'constraints': response.get('constraints', {})
            }
        }
        
        # Update thread_id if provided
        if response.get('thread_id'):
            st.session_state.thread_id = response['thread_id']
        
        # Add AI response to history
        st.session_state.chat_history.append(ai_response)
        
        # Debug: Show raw API response
        with st.expander("🔍 **Debug: Raw API Response**", expanded=False):
            st.json(response)
        
        st.rerun()
            
    except Exception as e:
        # Clear progress display on error
        if 'progress_container' in locals():
            progress_container.empty()
        
        error_msg = str(e)
        if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            st.error("⏱️ **Request Timeout**")
            st.write("The AI planning request took longer than expected. This can happen with:")
            st.write("• Complex multi-destination itineraries")
            st.write("• Detailed constraint requirements")
            st.write("• High server load")
            st.write("")
            st.info("💡 **Try again with:**")
            st.write("• A simpler, more focused request")
            st.write("• Fewer destinations or days") 
            st.write("• Break complex requests into smaller parts")
        else:
            st.error(f"❌ **Failed to get AI response**")
            st.write(f"Error details: {error_msg}")
            st.write("")
            st.info("💡 **Troubleshooting:**")
            st.write("• Check your internet connection")
            st.write("• Try refreshing the page")
            st.write("• Contact support if the problem persists")


def render_chat_controls():
    """Render chat control buttons."""
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.thread_id = str(uuid.uuid4())
            st.session_state.current_planning_data = {
                'tools_used': [],
                'citations': [],
                'decisions': [],
                'constraints': {},
                'itinerary': {}
            }
            st.rerun()
    
    with col2:
        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.thread_id = str(uuid.uuid4())
            st.info("🔄 Started a new planning session!")


def render_planning_sidebar():
    """Render the planning details sidebar."""
    st.markdown('<h3 style="color: white !important;">📊 Planning Details</h3>', unsafe_allow_html=True)
    
    data = st.session_state.current_planning_data
    
    # Thread ID info with better styling
    with st.expander("🧵 Session Info", expanded=False):
        st.write(f"**Thread ID:** {st.session_state.thread_id}")
        st.write("This ID links your conversation for follow-up questions")

    # Tools Used
    render_tools_used_section(data.get('tools_used', []))
    
    # Decisions Made
    render_decisions_section(data.get('decisions', []))

    # Constraints
    render_constraints_section(data.get('constraints', {}))
    
    # Citations
    render_citations_section(data.get('citations', []))
    
    # Detailed Itinerary
    render_detailed_itinerary_section(data.get('itinerary', {}))


def render_tools_used_section(tools_used):
    """Render the tools used section."""
    with st.expander("🛠️ Tools Used", expanded=True):
        if tools_used:
            for tool in tools_used:
                st.write(f"**{tool['name']}:** {tool['count']}x")
                # # Show timing if available
                # if tool.get('total_ms'):
                #     time_seconds = tool['total_ms'] / 1000
                #     st.write(f"**{time_seconds:.1f}s total**")
        else:
            st.info("No tools used yet. Ask a planning question to see tools in action!")


def render_decisions_section(decisions):
    """Render the decisions made section."""
    with st.expander("🎯 Decisions", expanded=True):
        if decisions:
            for i, decision in enumerate(decisions, 1):
                st.write(f"**{i}.** {decision}")
        else:
            st.info("No decisions recorded yet. The AI will track its reasoning as you chat.")


def render_constraints_section(constraints):
    """Render the constraints section."""
    with st.expander("🔒 Constraints", expanded=True):
        if constraints:
            st.write(f"**{constraints}**")
            # for constraint in constraints:
            st.write(f"**Budget:** {constraints['budget_usd']}")
            st.write(f"**Start Date:** {constraints['dates']['start']}")
            st.write(f"**End Date:** {constraints['dates']['end']}")
            st.write(f"**Airports:** {constraints['airports']}")
            for preference in constraints['preferences']:
                st.write(f"**{preference}:** {constraints['preferences'][preference]}")
        else:
            st.info("No constraints recorded yet. The AI will track its reasoning as you chat.")


def render_citations_section(citations):
    """Render the citations section."""
    with st.expander("📚 Sources & Citations", expanded=True):
        if citations:
            for citation in citations:
                # Determine icon based on source type
                icon = {
                    'url': '🌐',
                    'manual': '✍️',
                    'file': '📄',
                    'tool': '🔧'
                }.get(citation.get('source', '').lower(), '📋')
                
                st.write(f"{icon} **{citation['title']}**")
                st.caption(f"Source: {citation['source']} | Ref: {citation['ref']}")
                st.markdown("---")
        else:
            st.info("No citations available. Sources will appear here when the AI references your knowledge base.")


def render_detailed_itinerary_section(itinerary):
    """Render the detailed itinerary section."""
    with st.expander("🗓️ Detailed Itinerary", expanded=True):
        if itinerary and itinerary.get('days'):
            # Summary
            total_cost = itinerary.get('total_cost_usd', 0)
            if total_cost > 0:
                st.metric("💰 Estimated Total Cost", f"${total_cost:,.2f}")
            
            st.write(f"📅 **{len(itinerary['days'])} days planned**")
            st.markdown("---")
            
            # Day by day breakdown
            for day in itinerary['days']:
                st.write(f"### 📅 {day['date']}")
                
                if not day.get('items'):
                    st.info("No activities planned for this day.")
                    continue
                
                for i, item in enumerate(day['items'], 1):
                    # Time information
                    time_info = ""
                    if item.get('start') and item.get('end'):
                        time_info = f"🕐 {item['start']} - {item['end']}"
                    elif item.get('start'):
                        time_info = f"🕐 From {item['start']}"
                    
                    # Location information
                    location_info = ""
                    if item.get('location'):
                        location_info = f"📍 {item['location']}"
                    
                    # Main item
                    st.write(f"**{i}. {item['title']}**")
                    
                    # Details
                    if time_info or location_info:
                        details = " | ".join(filter(None, [time_info, location_info]))
                        st.caption(details)
                    
                    # Notes
                    if item.get('notes'):
                        st.info(f"💡 {item['notes']}")
                    
                    if i < len(day['items']):  # Don't add divider after last item
                        st.markdown("---")
                
                st.markdown("---")
        
        else:
            st.info("No itinerary generated yet. Ask the AI to plan a trip to see a detailed schedule here!")
            
            # Show example prompts
            st.markdown("**Try asking:**")
            st.markdown("- 'Plan a 3-day trip to London'")
            st.markdown("- 'Create an itinerary for Paris with a $1500 budget'")
            st.markdown("- 'Plan activities for a weekend in Tokyo'")
