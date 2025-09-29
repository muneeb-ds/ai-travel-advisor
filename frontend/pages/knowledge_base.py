"""
Knowledge Base management page with CRUD operations and file upload.
"""

import streamlit as st
from utils.api_client import get_api_client
from datetime import datetime
import io


def render_knowledge_page():
    """Render the knowledge base management page."""
    st.markdown('<div class="main-header">📚 Knowledge Base</div>', unsafe_allow_html=True)
    st.write("Manage your travel knowledge. Upload documents, create entries, and organize information by destination.")
    
    # Check if destinations exist
    destinations = load_destinations()
    if not destinations:
        st.warning("⚠️ **No destinations found!**")
        st.info("💡 Please create at least one destination before adding knowledge entries.")
        if st.button("🗺️ Go to Destinations", use_container_width=True):
            st.session_state.current_page = "Destinations"
            st.rerun()
        return
    
    # Create new knowledge entry section
    render_create_knowledge_form(destinations)
    
    st.markdown("---")
    
    # Filter and list knowledge entries
    render_knowledge_filters(destinations)
    render_knowledge_list(destinations)


def load_destinations():
    """Load available destinations."""
    try:
        api_client = get_api_client()
        return api_client.get_destinations()
    except Exception as e:
        st.error(f"❌ Failed to load destinations: {str(e)}")
        return []


def render_create_knowledge_form(destinations):
    """Render the form to create a new knowledge entry."""
    with st.expander("➕ Add New Knowledge Entry", expanded=False):
        st.write("Create a new knowledge entry and optionally upload a document.")
        
        with st.form("create_knowledge_form", clear_on_submit=True):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                title = st.text_input(
                    "Entry Title",
                    placeholder="e.g., Best Restaurants in Paris",
                    help="A descriptive title for this knowledge entry"
                )
                
                scope = st.text_input(
                    "Scope",
                    placeholder="e.g., restaurants, attractions, hotels",
                    help="Category or type of knowledge (e.g., restaurants, hotels, attractions)"
                )
            
            with col2:
                destination_options = {dest['name']: dest['id'] for dest in destinations}
                selected_destination_name = st.selectbox(
                    "Destination",
                    options=list(destination_options.keys()),
                    help="Select the destination this knowledge belongs to"
                )
                destination_id = destination_options[selected_destination_name]
                
                # File upload option
                uploaded_file = st.file_uploader(
                    "📎 Upload Document (Optional)",
                    type=['txt', 'pdf', 'docx', 'md'],
                    help="Upload a document to be processed and added to this knowledge entry"
                )
            
            col_submit, _ = st.columns([1, 3])
            with col_submit:
                submit = st.form_submit_button("✨ Create Entry", use_container_width=True)
            
            if submit:
                if not title.strip() or not scope.strip():
                    st.error("⚠️ Please fill in both title and scope.")
                    return
                
                try:
                    with st.spinner("📚 Creating knowledge entry..."):
                        api_client = get_api_client()
                        
                        # Create the knowledge entry
                        entry = api_client.create_knowledge_entry(
                            title.strip(), 
                            scope.strip(), 
                            destination_id
                        )
                        
                        entry_created_msg = f"✅ Successfully created knowledge entry: **{entry['title']}**"
                        
                        # If a file was uploaded, process it
                        if uploaded_file is not None:
                            file_content = uploaded_file.read()
                            upload_result = api_client.upload_knowledge_file(
                                entry['id'], 
                                file_content, 
                                uploaded_file.name
                            )
                            
                            st.success(f"{entry_created_msg}\n📎 **File uploaded:** {upload_result.get('message', 'File processed successfully')}")
                        else:
                            st.success(entry_created_msg)
                        
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Failed to create knowledge entry: {str(e)}")


def render_knowledge_filters(destinations):
    """Render filters for knowledge entries."""
    st.subheader("🔍 Filter Knowledge Entries")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Destination filter
        destination_options = {"All Destinations": None}
        destination_options.update({dest['name']: dest['id'] for dest in destinations})
        
        selected_filter = st.selectbox(
            "Filter by Destination",
            options=list(destination_options.keys()),
            key="destination_filter"
        )
        
        st.session_state.filter_destination_id = destination_options[selected_filter]
    
    with col2:
        # Scope filter (you could enhance this to show available scopes)
        st.text_input(
            "Filter by Scope",
            placeholder="e.g., restaurants",
            key="scope_filter",
            help="Enter a scope to filter entries (optional)"
        )
    
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()


def render_knowledge_list(destinations):
    """Render the list of knowledge entries."""
    st.subheader("📋 Your Knowledge Entries")
    
    try:
        with st.spinner("🔄 Loading knowledge entries..."):
            api_client = get_api_client()
            
            # Get filter values
            filter_destination_id = st.session_state.get("filter_destination_id")
            
            # Load knowledge entries with optional filtering
            if filter_destination_id:
                entries = api_client.get_knowledge_entries(destination_id=filter_destination_id)
            else:
                entries = api_client.get_knowledge_entries()
            
            # Apply scope filter if provided
            scope_filter = st.session_state.get("scope_filter", "").strip().lower()
            if scope_filter:
                entries = [entry for entry in entries if scope_filter in entry['scope'].lower()]
        
        if not entries:
            filter_msg = ""
            if st.session_state.get("filter_destination_id") or st.session_state.get("scope_filter"):
                filter_msg = " matching your filters"
            st.info(f"🎯 No knowledge entries found{filter_msg}. Create your first entry above!")
            return
        
        # Display entries
        for entry in entries:
            render_knowledge_entry_card(entry, destinations)
            
    except Exception as e:
        st.error(f"❌ Failed to load knowledge entries: {str(e)}")


def render_knowledge_entry_card(entry, destinations):
    """Render a single knowledge entry card."""
    # Find destination name
    dest_name = "Unknown"
    for dest in destinations:
        if dest['id'] == entry['destination_id']:
            dest_name = dest['name']
            break
    
    with st.container():
        # Header with title and badges
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### 📄 {entry['title']}")
            
            # Badges for scope and destination
            badge_html = f"""
            <div style="margin: 0.5rem 0;">
                <span style="background-color: #e3f2fd; color: #1976d2; padding: 0.25rem 0.5rem; border-radius: 1rem; font-size: 0.75rem; margin-right: 0.5rem;">
                    🏷️ {entry['scope']}
                </span>
                <span style="background-color: #f3e5f5; color: #7b1fa2; padding: 0.25rem 0.5rem; border-radius: 1rem; font-size: 0.75rem;">
                    🌍 {dest_name}
                </span>
            </div>
            """
            st.markdown(badge_html, unsafe_allow_html=True)
            
            created_date = datetime.fromisoformat(entry['created_at'].replace('Z', '+00:00'))
            st.caption(f"📅 Created: {created_date.strftime('%B %d, %Y')}")
        
        with col2:
            # Action buttons
            col_upload, col_edit, col_delete = st.columns(3)
            
            with col_upload:
                if st.button("📎", key=f"upload_{entry['id']}", help="Upload File", use_container_width=True):
                    st.session_state[f"uploading_{entry['id']}"] = True
                    st.rerun()
            
            with col_edit:
                if st.button("✏️", key=f"edit_{entry['id']}", help="Edit Entry", use_container_width=True):
                    st.session_state[f"editing_{entry['id']}"] = True
                    st.rerun()
            
            with col_delete:
                if st.button("🗑️", key=f"delete_{entry['id']}", help="Delete Entry", use_container_width=True):
                    st.session_state[f"confirm_delete_{entry['id']}"] = True
                    st.rerun()
        
        # File upload section (shown when upload button is clicked)
        if st.session_state.get(f"uploading_{entry['id']}", False):
            render_file_upload_section(entry)
        
        # Edit form (shown when edit button is clicked)
        if st.session_state.get(f"editing_{entry['id']}", False):
            render_edit_knowledge_form(entry, destinations)
        
        # Delete confirmation (shown when delete button is clicked)
        if st.session_state.get(f"confirm_delete_{entry['id']}", False):
            render_delete_knowledge_confirmation(entry)
        
        st.markdown("---")


def render_file_upload_section(entry):
    """Render file upload section for a knowledge entry."""
    st.markdown(f"#### 📎 Upload File for: {entry['title']}")
    
    uploaded_file = st.file_uploader(
        "Choose a file to upload",
        type=['txt', 'pdf', 'docx', 'md'],
        key=f"file_upload_{entry['id']}",
        help="Upload a document to add to this knowledge entry"
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📤 Upload", key=f"upload_confirm_{entry['id']}", use_container_width=True):
            if uploaded_file is not None:
                try:
                    with st.spinner("📤 Uploading and processing file..."):
                        api_client = get_api_client()
                        file_content = uploaded_file.read()
                        result = api_client.upload_knowledge_file(
                            entry['id'], 
                            file_content, 
                            uploaded_file.name
                        )
                        
                        st.success(f"✅ **File uploaded successfully!**\n{result.get('message', 'File processed')}")
                        st.session_state[f"uploading_{entry['id']}"] = False
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Failed to upload file: {str(e)}")
            else:
                st.error("⚠️ Please select a file to upload.")
    
    with col2:
        if st.button("❌ Cancel", key=f"upload_cancel_{entry['id']}", use_container_width=True):
            st.session_state[f"uploading_{entry['id']}"] = False
            st.rerun()


def render_edit_knowledge_form(entry, destinations):
    """Render the edit form for a knowledge entry."""
    st.markdown(f"#### ✏️ Editing: {entry['title']}")
    
    with st.form(f"edit_knowledge_form_{entry['id']}"):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            new_title = st.text_input(
                "New Title",
                value=entry['title'],
                placeholder="Enter new title"
            )
            
            new_scope = st.text_input(
                "New Scope",
                value=entry['scope'],
                placeholder="Enter new scope"
            )
        
        with col2:
            # Destination selector
            destination_options = {dest['name']: dest['id'] for dest in destinations}
            current_dest_name = next(
                (dest['name'] for dest in destinations if dest['id'] == entry['destination_id']), 
                "Unknown"
            )
            
            try:
                current_index = list(destination_options.keys()).index(current_dest_name)
            except ValueError:
                current_index = 0
            
            selected_destination_name = st.selectbox(
                "New Destination",
                options=list(destination_options.keys()),
                index=current_index
            )
            new_destination_id = destination_options[selected_destination_name]
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            save = st.form_submit_button("💾 Save", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if save:
            if not new_title.strip() or not new_scope.strip():
                st.error("⚠️ Title and scope cannot be empty.")
                return
            
            try:
                with st.spinner("💾 Updating knowledge entry..."):
                    api_client = get_api_client()
                    updated_entry = api_client.update_knowledge_entry(
                        entry['id'],
                        title=new_title.strip() if new_title.strip() != entry['title'] else None,
                        scope=new_scope.strip() if new_scope.strip() != entry['scope'] else None,
                        destination_id=new_destination_id if new_destination_id != entry['destination_id'] else None
                    )
                    
                    st.success(f"✅ Successfully updated: **{updated_entry['title']}**")
                    st.session_state[f"editing_{entry['id']}"] = False
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Failed to update knowledge entry: {str(e)}")
        
        if cancel:
            st.session_state[f"editing_{entry['id']}"] = False
            st.rerun()


def render_delete_knowledge_confirmation(entry):
    """Render delete confirmation for a knowledge entry."""
    st.warning(f"⚠️ **Confirm Deletion**")
    st.write(f"Are you sure you want to delete **{entry['title']}**?")
    st.caption("⚠️ This action cannot be undone and will permanently remove this knowledge entry and its associated files.")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🗑️ Delete", key=f"confirm_delete_yes_{entry['id']}", use_container_width=True):
            try:
                with st.spinner("🗑️ Deleting knowledge entry..."):
                    api_client = get_api_client()
                    api_client.delete_knowledge_entry(entry['id'])
                    
                    st.success(f"✅ Successfully deleted: **{entry['title']}**")
                    # Clear the confirmation state
                    if f"confirm_delete_{entry['id']}" in st.session_state:
                        del st.session_state[f"confirm_delete_{entry['id']}"]
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Failed to delete knowledge entry: {str(e)}")
    
    with col2:
        if st.button("❌ Cancel", key=f"confirm_delete_no_{entry['id']}", use_container_width=True):
            st.session_state[f"confirm_delete_{entry['id']}"] = False
            st.rerun()
