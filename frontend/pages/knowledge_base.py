"""
Knowledge base management page for the Travel Advisor app.
"""
import streamlit as st
from utils.api_client import get_api_client


def show():
    """Display the knowledge base management page."""
    st.header("📚 Knowledge Base")
    st.markdown("Add and manage your travel knowledge. Store information about destinations, tips, experiences, and more.")
    
    api_client = get_api_client()
    
    # Get destinations for the dropdown
    destinations = api_client.get_destinations()
    
    if not destinations or "error" in destinations:
        st.warning("⚠️ No destinations found. Please add destinations first.")
        if st.button("➕ Go to Destinations"):
            st.switch_page("pages/destinations.py")
        return
    
    # Add new knowledge entry section
    st.subheader("➕ Add New Knowledge Entry")
    
    with st.form("add_knowledge_form"):
        # Destination selection
        destination_options = {dest["name"]: dest["id"] for dest in destinations}
        selected_destination_name = st.selectbox(
            "Select Destination",
            options=list(destination_options.keys()),
            index=0 if destination_options else None,
            help="Choose the destination this knowledge is about"
        )
        
        # Content input
        knowledge_content = st.text_area(
            "Knowledge Content",
            placeholder="Share what you know about this destination...\n\nExamples:\n- Best restaurants and local cuisine\n- Tourist attractions and hidden gems\n- Transportation tips\n- Cultural insights\n- Personal experiences",
            height=150,
            help="Add detailed information about the destination"
        )
        
        submitted = st.form_submit_button("Add Knowledge Entry", type="primary")
        
        if submitted and knowledge_content and selected_destination_name:
            destination_id = destination_options[selected_destination_name]
            result = api_client.create_knowledge_entry(destination_id, knowledge_content.strip())
            if result and "id" in result:
                st.success(f"✅ Knowledge entry added for '{selected_destination_name}' successfully!")
                st.rerun()
            elif "error" in result:
                st.error(f"❌ Error: {result['error']}")
        elif submitted:
            if not knowledge_content:
                st.error("❌ Please enter some knowledge content")
            if not selected_destination_name:
                st.error("❌ Please select a destination")
    
    st.markdown("---")
    
    # Filter and display knowledge entries
    st.subheader("📖 Knowledge Entries")
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        filter_destination = st.selectbox(
            "Filter by Destination",
            options=["All Destinations"] + list(destination_options.keys()),
            key="knowledge_filter"
        )
    
    with col2:
        search_term = st.text_input(
            "🔍 Search in content",
            placeholder="Search knowledge entries...",
            key="knowledge_search"
        )
    
    # Get knowledge entries
    filter_destination_id = None
    if filter_destination != "All Destinations":
        filter_destination_id = destination_options[filter_destination]
    
    knowledge_entries = api_client.get_knowledge_entries(filter_destination_id)
    
    if not knowledge_entries or "error" in knowledge_entries:
        st.info("No knowledge entries found. Add your first entry above!")
        return
    
    # Filter by search term
    if search_term:
        filtered_entries = [
            entry for entry in knowledge_entries 
            if search_term.lower() in entry.get("content", "").lower()
        ]
    else:
        filtered_entries = knowledge_entries
    
    # Display knowledge entries
    if filtered_entries:
        st.markdown(f"**Found {len(filtered_entries)} entries**")
        
        for entry in filtered_entries:
            destination_name = entry.get("destination", {}).get("name", "Unknown")
            
            with st.container():
                st.markdown(f"""
                <div class="knowledge-entry">
                    <h4>📍 {destination_name}</h4>
                    <p><small>Added: {entry.get('created_at', '')[:10]}</small></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Content display with read more functionality
                content = entry.get("content", "")
                if len(content) > 300:
                    if st.session_state.get(f"expanded_{entry['id']}", False):
                        st.markdown(content)
                        if st.button(f"📖 Show Less", key=f"collapse_{entry['id']}"):
                            st.session_state[f"expanded_{entry['id']}"] = False
                            st.rerun()
                    else:
                        st.markdown(content[:300] + "...")
                        if st.button(f"📖 Read More", key=f"expand_{entry['id']}"):
                            st.session_state[f"expanded_{entry['id']}"] = True
                            st.rerun()
                else:
                    st.markdown(content)
                
                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    if st.button(
                        "📝 Edit", 
                        key=f"edit_knowledge_{entry['id']}",
                        help="Edit this knowledge entry"
                    ):
                        st.session_state[f"editing_knowledge_{entry['id']}"] = True
                
                with col2:
                    if st.button(
                        "🤖 Ask AI", 
                        key=f"ai_about_{entry['id']}",
                        help="Ask AI about this destination"
                    ):
                        # Set destination for AI chat and switch to chat page
                        st.session_state.chat_destination_id = entry.get("destination", {}).get("id")
                        st.session_state.chat_destination_name = destination_name
                        st.switch_page("pages/ai_chat.py")
                
                with col3:
                    if st.button(
                        "🗑️ Delete", 
                        key=f"delete_knowledge_{entry['id']}",
                        help="Delete this knowledge entry",
                        type="secondary"
                    ):
                        st.session_state[f"confirm_delete_knowledge_{entry['id']}"] = True
                
                # Edit form
                if st.session_state.get(f"editing_knowledge_{entry['id']}", False):
                    with st.form(f"edit_knowledge_form_{entry['id']}"):
                        new_content = st.text_area(
                            "Edit Content",
                            value=content,
                            height=150,
                            key=f"edit_content_{entry['id']}"
                        )
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Save Changes"):
                                if new_content.strip():
                                    result = api_client.update_knowledge_entry(
                                        entry['id'], 
                                        new_content.strip()
                                    )
                                    if result and "id" in result:
                                        st.success("✅ Knowledge entry updated successfully!")
                                        st.session_state[f"editing_knowledge_{entry['id']}"] = False
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to update knowledge entry")
                                else:
                                    st.error("❌ Content cannot be empty")
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Cancel"):
                                st.session_state[f"editing_knowledge_{entry['id']}"] = False
                                st.rerun()
                
                # Delete confirmation
                if st.session_state.get(f"confirm_delete_knowledge_{entry['id']}", False):
                    st.warning("⚠️ Are you sure you want to delete this knowledge entry?")
                    
                    col_confirm, col_cancel = st.columns(2)
                    with col_confirm:
                        if st.button(
                            "🗑️ Confirm Delete", 
                            key=f"confirm_delete_knowledge_btn_{entry['id']}",
                            type="primary"
                        ):
                            success = api_client.delete_knowledge_entry(entry['id'])
                            if success:
                                st.success("✅ Knowledge entry deleted successfully!")
                                st.session_state[f"confirm_delete_knowledge_{entry['id']}"] = False
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete knowledge entry")
                    
                    with col_cancel:
                        if st.button(
                            "❌ Cancel", 
                            key=f"cancel_delete_knowledge_{entry['id']}"
                        ):
                            st.session_state[f"confirm_delete_knowledge_{entry['id']}"] = False
                            st.rerun()
                
                st.markdown("---")
    
    else:
        if search_term:
            st.info(f"No knowledge entries found matching '{search_term}'")
        elif filter_destination != "All Destinations":
            st.info(f"No knowledge entries found for '{filter_destination}'")
        else:
            st.info("No knowledge entries found")
    
    # Statistics
    if knowledge_entries and not isinstance(knowledge_entries, dict):
        st.markdown("---")
        st.subheader("📊 Knowledge Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Entries", len(knowledge_entries))
        
        with col2:
            if filter_destination != "All Destinations":
                destination_entries = len([
                    e for e in knowledge_entries 
                    if e.get("destination", {}).get("name") == filter_destination
                ])
                st.metric(f"Entries for {filter_destination}", destination_entries)
            else:
                unique_destinations = len(set([
                    e.get("destination", {}).get("name") 
                    for e in knowledge_entries
                ]))
                st.metric("Destinations with Knowledge", unique_destinations)
        
        with col3:
            avg_length = sum([len(e.get("content", "")) for e in knowledge_entries]) / len(knowledge_entries)
            st.metric("Avg. Entry Length", f"{int(avg_length)} chars")
