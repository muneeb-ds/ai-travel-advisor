"""
Destinations management page with CRUD operations.
"""

import streamlit as st
from utils.api_client import get_api_client
from datetime import datetime


def render_destinations_page():
    """Render the destinations management page."""
    st.markdown('<div class="main-header">🗺️ Destinations</div>', unsafe_allow_html=True)
    st.write("Manage your travel destinations. Create, edit, and organize places you want to visit.")
    
    # Create new destination section
    render_create_destination_form()
    
    st.markdown("---")
    
    # List existing destinations
    render_destinations_list()


def render_create_destination_form():
    """Render the form to create a new destination."""
    with st.expander("➕ Add New Destination", expanded=False):
        st.write("Create a new destination to organize your travel knowledge and plans.")
        
        with st.form("create_destination_form", clear_on_submit=True):
            name = st.text_input(
                "Destination Name",
                placeholder="e.g., Paris, Tokyo, New York",
                help="Enter the name of the destination you want to add"
            )
            
            col1, col2 = st.columns([1, 3])
            with col1:
                submit = st.form_submit_button("✨ Create Destination", use_container_width=True)
            
            if submit:
                if not name.strip():
                    st.error("⚠️ Please enter a destination name.")
                    return
                
                try:
                    with st.spinner("🌍 Creating destination..."):
                        api_client = get_api_client()
                        destination = api_client.create_destination(name.strip())
                        
                        st.success(f"✅ Successfully created destination: **{destination['name']}**")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Failed to create destination: {str(e)}")


def render_destinations_list():
    """Render the list of existing destinations."""
    st.subheader("📍 Your Destinations")
    
    try:
        with st.spinner("🔄 Loading destinations..."):
            api_client = get_api_client()
            destinations = api_client.get_destinations()
        
        if not destinations:
            st.info("🎯 No destinations found. Create your first destination above to get started!")
            return
        
        # Display destinations in a nice grid
        for i, dest in enumerate(destinations):
            render_destination_card(dest, i)
            
    except Exception as e:
        st.error(f"❌ Failed to load destinations: {str(e)}")


def render_destination_card(dest, index):
    """Render a single destination card."""
    with st.container():
        # Create columns for layout
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.markdown(f"### 🌍 {dest['name']}")
            created_date = datetime.fromisoformat(dest['created_at'].replace('Z', '+00:00'))
            st.caption(f"📅 Created: {created_date.strftime('%B %d, %Y')}")
            
            # Show destination ID for reference
            with st.expander("🔍 Details"):
                st.code(f"ID: {dest['id']}")
        
        with col2:
            # View details button
            if st.button("👁️ View", key=f"view_{dest['id']}", use_container_width=True):
                view_destination_details(dest['id'])
        
        with col3:
            # Edit button
            if st.button("✏️ Edit", key=f"edit_{dest['id']}", use_container_width=True):
                st.session_state[f"editing_{dest['id']}"] = True
                st.rerun()
        
        with col4:
            # Delete button
            if st.button("🗑️ Delete", key=f"delete_{dest['id']}", use_container_width=True):
                st.session_state[f"confirm_delete_{dest['id']}"] = True
                st.rerun()
        
        # Edit form (shown when edit button is clicked)
        if st.session_state.get(f"editing_{dest['id']}", False):
            render_edit_destination_form(dest)
        
        # Delete confirmation (shown when delete button is clicked)
        if st.session_state.get(f"confirm_delete_{dest['id']}", False):
            render_delete_confirmation(dest)
        
        st.markdown("---")


def render_edit_destination_form(dest):
    """Render the edit form for a destination."""
    st.markdown(f"#### ✏️ Editing: {dest['name']}")
    
    with st.form(f"edit_form_{dest['id']}"):
        new_name = st.text_input(
            "New Name",
            value=dest['name'],
            placeholder="Enter new destination name"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            save = st.form_submit_button("💾 Save", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if save:
            if not new_name.strip():
                st.error("⚠️ Destination name cannot be empty.")
                return
            
            try:
                with st.spinner("💾 Updating destination..."):
                    api_client = get_api_client()
                    updated_dest = api_client.update_destination(dest['id'], new_name.strip())
                    
                    st.success(f"✅ Successfully updated to: **{updated_dest['name']}**")
                    st.session_state[f"editing_{dest['id']}"] = False
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Failed to update destination: {str(e)}")
        
        if cancel:
            st.session_state[f"editing_{dest['id']}"] = False
            st.rerun()


def render_delete_confirmation(dest):
    """Render delete confirmation dialog."""
    st.warning(f"⚠️ **Confirm Deletion**")
    st.write(f"Are you sure you want to delete **{dest['name']}**?")
    st.caption("⚠️ This action cannot be undone and will also delete all associated knowledge entries.")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🗑️ Delete", key=f"confirm_delete_yes_{dest['id']}", use_container_width=True):
            try:
                with st.spinner("🗑️ Deleting destination..."):
                    api_client = get_api_client()
                    api_client.delete_destination(dest['id'])
                    
                    st.success(f"✅ Successfully deleted: **{dest['name']}**")
                    # Clear the confirmation state
                    if f"confirm_delete_{dest['id']}" in st.session_state:
                        del st.session_state[f"confirm_delete_{dest['id']}"]
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Failed to delete destination: {str(e)}")
    
    with col2:
        if st.button("❌ Cancel", key=f"confirm_delete_no_{dest['id']}", use_container_width=True):
            st.session_state[f"confirm_delete_{dest['id']}"] = False
            st.rerun()


def view_destination_details(destination_id):
    """Show detailed view of a destination."""
    try:
        with st.spinner("🔍 Loading destination details..."):
            api_client = get_api_client()
            dest_details = api_client.get_destination(destination_id)
        
        # Use a modal-like expander
        with st.expander(f"🌍 {dest_details['name']} - Details", expanded=True):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.write("**Basic Information:**")
                st.write(f"📍 **Name:** {dest_details['name']}")
                st.write(f"🆔 **ID:** {dest_details['id']}")
                created_date = datetime.fromisoformat(dest_details['created_at'].replace('Z', '+00:00'))
                st.write(f"📅 **Created:** {created_date.strftime('%B %d, %Y at %I:%M %p')}")
            
            with col2:
                st.write("**Knowledge Entries:**")
                knowledge_entries = dest_details.get('knowledge_entries', [])
                
                if knowledge_entries:
                    st.write(f"📚 **Total Entries:** {len(knowledge_entries)}")
                    
                    for entry in knowledge_entries:
                        st.write(f"• **{entry['title']}** ({entry['scope']})")
                else:
                    st.info("No knowledge entries found for this destination.")
                    st.write("💡 Go to the Knowledge Base page to add some!")
        
    except Exception as e:
        st.error(f"❌ Failed to load destination details: {str(e)}")
