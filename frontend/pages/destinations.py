"""
Destinations management page for the Travel Advisor app.
"""
import streamlit as st
from utils.api_client import get_api_client


def show():
    """Display the destinations management page."""
    st.header("🏠 Destination Management")
    st.markdown("Manage your travel destinations here. Add new places you want to visit or have visited.")
    
    api_client = get_api_client()
    
    # Add new destination section
    st.subheader("➕ Add New Destination")
    
    with st.form("add_destination_form"):
        new_destination_name = st.text_input(
            "Destination Name",
            placeholder="e.g., Paris, Tokyo, New York",
            help="Enter the name of a city or destination"
        )
        
        submitted = st.form_submit_button("Add Destination", type="primary")
        
        if submitted and new_destination_name:
            result = api_client.create_destination(new_destination_name.strip())
            if result and "id" in result:
                st.success(f"✅ Added '{new_destination_name}' successfully!")
                st.rerun()
            elif "error" in result:
                st.error(f"❌ Error: {result['error']}")
        elif submitted and not new_destination_name:
            st.error("❌ Please enter a destination name")
    
    st.markdown("---")
    
    # Display existing destinations
    st.subheader("📍 Your Destinations")
    
    destinations = api_client.get_destinations()
    
    if not destinations or "error" in destinations:
        st.info("No destinations found. Add your first destination above!")
        return
    
    # Search and filter
    search_term = st.text_input(
        "🔍 Search destinations",
        placeholder="Search by name...",
        key="destination_search"
    )
    
    # Filter destinations based on search
    if search_term:
        filtered_destinations = [
            dest for dest in destinations 
            if search_term.lower() in dest.get("name", "").lower()
        ]
    else:
        filtered_destinations = destinations
    
    # Display destinations in a grid
    if filtered_destinations:
        # Create columns for responsive layout
        col1, col2 = st.columns(2)
        
        for idx, destination in enumerate(filtered_destinations):
            with col1 if idx % 2 == 0 else col2:
                with st.container():
                    st.markdown(f"""
                    <div class="destination-card">
                        <h4>📍 {destination.get('name', 'Unknown')}</h4>
                        <p><small>Added: {destination.get('created_at', '')[:10]}</small></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Action buttons
                    btn_col1, btn_col2, btn_col3 = st.columns(3)
                    
                    with btn_col1:
                        if st.button(
                            "📝 Edit", 
                            key=f"edit_{destination['id']}",
                            help="Edit destination name"
                        ):
                            st.session_state[f"editing_{destination['id']}"] = True
                    
                    with btn_col2:
                        if st.button(
                            "📚 Knowledge", 
                            key=f"knowledge_{destination['id']}",
                            help="View knowledge entries"
                        ):
                            st.session_state.selected_destination = destination['id']
                            st.switch_page("pages/knowledge_base.py")
                    
                    with btn_col3:
                        if st.button(
                            "🗑️ Delete", 
                            key=f"delete_{destination['id']}",
                            help="Delete destination",
                            type="secondary"
                        ):
                            st.session_state[f"confirm_delete_{destination['id']}"] = True
                    
                    # Edit form (appears when edit button is clicked)
                    if st.session_state.get(f"editing_{destination['id']}", False):
                        with st.form(f"edit_form_{destination['id']}"):
                            new_name = st.text_input(
                                "New name",
                                value=destination.get('name', ''),
                                key=f"new_name_{destination['id']}"
                            )
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("💾 Save"):
                                    if new_name.strip():
                                        result = api_client.update_destination(
                                            destination['id'], 
                                            new_name.strip()
                                        )
                                        if result and "id" in result:
                                            st.success("✅ Updated successfully!")
                                            st.session_state[f"editing_{destination['id']}"] = False
                                            st.rerun()
                                        else:
                                            st.error("❌ Failed to update destination")
                                    else:
                                        st.error("❌ Name cannot be empty")
                            
                            with col_cancel:
                                if st.form_submit_button("❌ Cancel"):
                                    st.session_state[f"editing_{destination['id']}"] = False
                                    st.rerun()
                    
                    # Delete confirmation (appears when delete button is clicked)
                    if st.session_state.get(f"confirm_delete_{destination['id']}", False):
                        st.warning("⚠️ Are you sure you want to delete this destination? This will also delete all associated knowledge entries.")
                        
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button(
                                "🗑️ Confirm Delete", 
                                key=f"confirm_delete_btn_{destination['id']}",
                                type="primary"
                            ):
                                success = api_client.delete_destination(destination['id'])
                                if success:
                                    st.success("✅ Destination deleted successfully!")
                                    st.session_state[f"confirm_delete_{destination['id']}"] = False
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to delete destination")
                        
                        with col_cancel:
                            if st.button(
                                "❌ Cancel", 
                                key=f"cancel_delete_{destination['id']}"
                            ):
                                st.session_state[f"confirm_delete_{destination['id']}"] = False
                                st.rerun()
                    
                    st.markdown("---")
    
    else:
        st.info(f"No destinations found matching '{search_term}'")
    
    # Statistics
    if destinations and not isinstance(destinations, dict):
        st.markdown("---")
        st.subheader("📊 Statistics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Destinations", len(destinations))
        with col2:
            if search_term:
                st.metric("Filtered Results", len(filtered_destinations))
        with col3:
            # This could be expanded to show knowledge entries count
            st.metric("Active Searches", 1 if search_term else 0)
