"""
API client for communicating with the backend.
"""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import httpx
import streamlit as st


class APIClient:
    """Client for backend API communication with token management."""
    
    def __init__(self, base_url: str = "http://backend:8000"):
        self.base_url = base_url.rstrip("/")
        # Use very long timeout for AI planning requests which can take several minutes
        self.client = httpx.Client(timeout=httpx.Timeout(
            connect=30.0,  # Connection timeout - time to establish connection
            read=600.0,    # Read timeout - time to receive response (10 minutes for AI planning)
            write=30.0,    # Write timeout - time to send request
            pool=30.0      # Pool timeout - time to get connection from pool
        ))
        
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
        authenticated: bool = True,
        refresh_on_error: bool = True
    ) -> Dict[str, Any]:
        """Make HTTP request with automatic token refresh."""
        url = f"{self.base_url}/api/v1{endpoint}"
        headers = {}
        
        if authenticated:
            access_token = st.session_state.get("access_token")
            if not access_token:
                raise Exception("No access token found. Please login.")
            headers["Authorization"] = f"Bearer {access_token}"
        
        try:
            if method.upper() == "GET":
                response = self.client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                if files:
                    response = self.client.post(url, headers=headers, files=files, data=data)
                else:
                    response = self.client.post(url, headers=headers, json=data, params=params)
            elif method.upper() == "PATCH":
                response = self.client.patch(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = self.client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Handle token expiration
            if response.status_code == 401 and authenticated and refresh_on_error:
                if self._refresh_token():
                    # Retry with new token
                    return self._make_request(
                        method, endpoint, data, files, params, authenticated, False
                    )
                else:
                    # Refresh failed, redirect to login
                    st.session_state.clear()
                    st.rerun()
            
            response.raise_for_status()
            
            if response.status_code == 204:  # No content
                return {}
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 422:
                error_detail = e.response.json().get("detail", "Validation error")
                raise Exception(f"Validation error: {error_detail}")
            else:
                error_detail = e.response.json().get("detail", str(e))
                raise Exception(f"API error: {error_detail}")
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def _refresh_token(self) -> bool:
        """Refresh access token using refresh token."""
        refresh_token = st.session_state.get("refresh_token")
        if not refresh_token:
            return False
        
        try:
            response = self.client.post(
                f"{self.base_url}/api/v1/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            response.raise_for_status()
            token_data = response.json()
            
            # Update session state with new tokens
            st.session_state.access_token = token_data["access_token"]
            st.session_state.refresh_token = token_data["refresh_token"]
            st.session_state.token_expires_at = datetime.now() + timedelta(
                seconds=token_data["expires_in"]
            )
            
            return True
        except:
            return False
    
    # Authentication endpoints
    def signup(self, email: str, password: str, org_name: str) -> Dict[str, Any]:
        """Register a new user."""
        data = {
            "email": email,
            "password": password,
            "org_name": org_name
        }
        return self._make_request("POST", "/auth/signup", data=data, authenticated=False)
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user."""
        # FastAPI OAuth2PasswordRequestForm expects form data
        response = self.client.post(
            f"{self.base_url}/api/v1/auth/login",
            data={"username": email, "password": password}  # OAuth2 uses 'username' field
        )
        response.raise_for_status()
        return response.json()
    
    def logout(self) -> None:
        """Logout user."""
        refresh_token = st.session_state.get("refresh_token")
        if refresh_token:
            self._make_request(
                "POST", "/auth/logout", 
                data={"refresh_token": refresh_token}
            )
    
    def get_me(self) -> Dict[str, Any]:
        """Get current user info."""
        return self._make_request("GET", "/auth/me")
    
    # Destinations endpoints
    def get_destinations(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all destinations."""
        params = {"skip": skip, "limit": limit}
        return self._make_request("GET", "/destinations/", params=params)
    
    def get_destination(self, destination_id: str) -> Dict[str, Any]:
        """Get destination by ID."""
        return self._make_request("GET", f"/destinations/{destination_id}")
    
    def create_destination(self, name: str) -> Dict[str, Any]:
        """Create new destination."""
        data = {"name": name}
        return self._make_request("POST", "/destinations/", data=data)
    
    def update_destination(self, destination_id: str, name: str) -> Dict[str, Any]:
        """Update destination."""
        data = {"name": name}
        return self._make_request("PATCH", f"/destinations/{destination_id}", data=data)
    
    def delete_destination(self, destination_id: str) -> None:
        """Delete destination."""
        self._make_request("DELETE", f"/destinations/{destination_id}")
    
    # Knowledge base endpoints
    def get_knowledge_entries(
        self, 
        destination_id: Optional[str] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get knowledge entries."""
        params = {"skip": skip, "limit": limit}
        if destination_id:
            params["destination_id"] = destination_id
        return self._make_request("GET", "/knowledge/", params=params)
    
    def get_knowledge_entry(self, knowledge_id: str) -> Dict[str, Any]:
        """Get knowledge entry by ID."""
        return self._make_request("GET", f"/knowledge/{knowledge_id}")
    
    def create_knowledge_entry(
        self, 
        title: str, 
        scope: str, 
        destination_id: str
    ) -> Dict[str, Any]:
        """Create new knowledge entry."""
        data = {
            "title": title,
            "scope": scope,
            "destination_id": destination_id
        }
        return self._make_request("POST", "/knowledge/", data=data)
    
    def update_knowledge_entry(
        self, 
        knowledge_id: str, 
        title: Optional[str] = None,
        scope: Optional[str] = None,
        destination_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update knowledge entry."""
        data = {}
        if title is not None:
            data["title"] = title
        if scope is not None:
            data["scope"] = scope
        if destination_id is not None:
            data["destination_id"] = destination_id
        
        return self._make_request("PATCH", f"/knowledge/{knowledge_id}", data=data)
    
    def delete_knowledge_entry(self, knowledge_id: str) -> None:
        """Delete knowledge entry."""
        self._make_request("DELETE", f"/knowledge/{knowledge_id}")
    
    def upload_knowledge_file(self, knowledge_id: str, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Upload file to knowledge entry."""
        files = {"file": (filename, file_content)}
        return self._make_request(
            "POST", 
            f"/knowledge/{knowledge_id}/ingest-file", 
            files=files
        )
    
    # Agent endpoints
    def plan_itinerary(self, query: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Plan itinerary using agent."""
        data = {
            "query": query,
            "thread_id": thread_id or str(uuid.uuid4())
        }
        # Use extended timeout specifically for AI planning
        return self._make_request("POST", "/qa/plan", data=data)
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()


def get_api_client() -> APIClient:
    """Get or create API client instance."""
    # Always create a fresh client to avoid async caching issues
    # In production, you might want to cache this for performance
    return APIClient()


def safe_call(func, *args, **kwargs):
    """Helper to safely call API functions."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        raise e
