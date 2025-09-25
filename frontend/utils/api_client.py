"""
API client utilities for communicating with the FastAPI backend.
"""
import os
import requests
import streamlit as st
from typing import List, Dict, Any, Optional
from uuid import UUID


class APIClient:
    """Client for communicating with the FastAPI backend."""
    
    def __init__(self):
        self.base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.api_base = f"{self.base_url}/api/v1"
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors."""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            st.error(f"API Error: {e}")
            if response.status_code == 404:
                return {"error": "Resource not found"}
            elif response.status_code == 400:
                return {"error": "Bad request"}
            else:
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            st.error(f"Network Error: {e}")
            return {"error": str(e)}
    
    # Destination endpoints
    def get_destinations(self) -> List[Dict[str, Any]]:
        """Get all destinations."""
        try:
            response = requests.get(f"{self.api_base}/destinations/")
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to fetch destinations: {e}")
            return []
    
    def get_destination(self, destination_id: int) -> Dict[str, Any]:
        """Get a specific destination by ID."""
        try:
            response = requests.get(f"{self.api_base}/destinations/{destination_id}")
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to fetch destination: {e}")
            return {}
    
    def create_destination(self, name: str) -> Dict[str, Any]:
        """Create a new destination."""
        try:
            response = requests.post(
                f"{self.api_base}/destinations/",
                json={"name": name}
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to create destination: {e}")
            return {}
    
    def update_destination(self, destination_id: int, name: str) -> Dict[str, Any]:
        """Update a destination."""
        try:
            response = requests.put(
                f"{self.api_base}/destinations/{destination_id}",
                json={"name": name}
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to update destination: {e}")
            return {}
    
    def delete_destination(self, destination_id: int) -> bool:
        """Delete a destination."""
        try:
            response = requests.delete(f"{self.api_base}/destinations/{destination_id}")
            return response.status_code == 204
        except Exception as e:
            st.error(f"Failed to delete destination: {e}")
            return False
    
    # Knowledge base endpoints
    def get_knowledge_entries(self, destination_id: Optional[UUID] = None) -> List[Dict[str, Any]]:
        """Get knowledge base entries."""
        try:
            params = {}
            if destination_id:
                params["destination_id"] = destination_id
            
            response = requests.get(f"{self.api_base}/knowledge/", params=params)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to fetch knowledge entries: {e}")
            return []
    
    def get_knowledge_entry(self, knowledge_id: UUID) -> Dict[str, Any]:
        """Get a specific knowledge entry by ID."""
        try:
            response = requests.get(f"{self.api_base}/knowledge/{knowledge_id}")
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to fetch knowledge entry: {e}")
            return {}
    
    def create_knowledge_entry(self, destination_id: UUID, content: str) -> Dict[str, Any]:
        """Create a new knowledge base entry."""
        try:
            response = requests.post(
                f"{self.api_base}/knowledge/",
                json={"destination_id": destination_id, "content": content}
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to create knowledge entry: {e}")
            return {}
    
    def update_knowledge_entry(self, knowledge_id: int, content: str) -> Dict[str, Any]:
        """Update a knowledge base entry."""
        try:
            response = requests.put(
                f"{self.api_base}/knowledge/{knowledge_id}",
                json={"content": content}
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to update knowledge entry: {e}")
            return {}
    
    def delete_knowledge_entry(self, knowledge_id: int) -> bool:
        """Delete a knowledge base entry."""
        try:
            response = requests.delete(f"{self.api_base}/knowledge/{knowledge_id}")
            return response.status_code == 204
        except Exception as e:
            st.error(f"Failed to delete knowledge entry: {e}")
            return False
    
    # AI Chat endpoints
    def send_chat_message(
        self, 
        message: str, 
        destination_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Send a message to the AI chat."""
        try:
            payload = {"message": message}
            if destination_id:
                payload["destination_id"] = destination_id
            
            response = requests.post(
                f"{self.api_base}/chat/",
                json=payload
            )
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to send chat message: {e}")
            return {}
    
    def get_destination_context(self, destination_id: int) -> Dict[str, Any]:
        """Get context information for a destination."""
        try:
            response = requests.get(f"{self.api_base}/chat/destinations/{destination_id}/context")
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Failed to get destination context: {e}")
            return {}


# Global API client instance
@st.cache_resource
def get_api_client():
    """Get a cached API client instance."""
    return APIClient()
