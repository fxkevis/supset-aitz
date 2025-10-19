"""Session manager for persistent browser sessions and profile management."""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from loguru import logger

from ..interfaces.base_interfaces import BaseManager
from ..models.config import BrowserConfig


@dataclass
class BrowserSession:
    """Represents a browser session with profile information."""
    session_id: str
    profile_name: str
    profile_path: str
    created_at: datetime
    last_accessed: datetime
    domain_cookies: Dict[str, List[Dict[str, Any]]]
    local_storage: Dict[str, Dict[str, str]]
    session_storage: Dict[str, Dict[str, str]]
    is_active: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "profile_name": self.profile_name,
            "profile_path": self.profile_path,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "domain_cookies": self.domain_cookies,
            "local_storage": self.local_storage,
            "session_storage": self.session_storage,
            "is_active": self.is_active,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrowserSession':
        """Create session from dictionary."""
        return cls(
            session_id=data["session_id"],
            profile_name=data["profile_name"],
            profile_path=data["profile_path"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            domain_cookies=data.get("domain_cookies", {}),
            local_storage=data.get("local_storage", {}),
            session_storage=data.get("session_storage", {}),
            is_active=data.get("is_active", False),
        )


class SessionManager(BaseManager):
    """Manages persistent browser sessions and profiles."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the session manager.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.sessions_dir = Path(self.config.get("sessions_dir", "data/sessions"))
        self.profiles_dir = Path(self.config.get("profiles_dir", "data/profiles"))
        self.sessions_file = self.sessions_dir / "sessions.json"
        self.active_sessions: Dict[str, BrowserSession] = {}
        self.max_sessions = self.config.get("max_sessions", 10)
        self.session_timeout_days = self.config.get("session_timeout_days", 30)
        
        # Ensure directories exist
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def start(self) -> None:
        """Start managing sessions by loading existing sessions."""
        try:
            self._load_sessions()
            self._cleanup_expired_sessions()
            logger.info("Session manager started successfully")
        except Exception as e:
            logger.error(f"Failed to start session manager: {e}")
            raise
    
    def stop(self) -> None:
        """Stop managing sessions and save current state."""
        try:
            self._save_sessions()
            self.active_sessions.clear()
            logger.info("Session manager stopped")
        except Exception as e:
            logger.error(f"Error stopping session manager: {e}")
    
    def create_session(self, profile_name: str, session_id: Optional[str] = None) -> BrowserSession:
        """Create a new browser session with a dedicated profile.
        
        Args:
            profile_name: Name for the browser profile
            session_id: Optional custom session ID
            
        Returns:
            Created BrowserSession object
        """
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create profile directory
        profile_path = self.profiles_dir / f"{profile_name}_{session_id}"
        profile_path.mkdir(parents=True, exist_ok=True)
        
        # Create session object
        session = BrowserSession(
            session_id=session_id,
            profile_name=profile_name,
            profile_path=str(profile_path),
            created_at=datetime.now(),
            last_accessed=datetime.now(),
            domain_cookies={},
            local_storage={},
            session_storage={},
            is_active=True
        )
        
        # Store session
        self.active_sessions[session_id] = session
        self._save_sessions()
        
        logger.info(f"Created new session: {session_id} with profile: {profile_name}")
        return session
    
    def get_session(self, session_id: str) -> Optional[BrowserSession]:
        """Get an existing session by ID.
        
        Args:
            session_id: The session identifier
            
        Returns:
            BrowserSession if found, None otherwise
        """
        session = self.active_sessions.get(session_id)
        if session:
            session.last_accessed = datetime.now()
            self._save_sessions()
        return session
    
    def get_session_by_profile(self, profile_name: str) -> Optional[BrowserSession]:
        """Get the most recent session for a profile.
        
        Args:
            profile_name: The profile name to search for
            
        Returns:
            Most recent BrowserSession for the profile, None if not found
        """
        matching_sessions = [
            session for session in self.active_sessions.values()
            if session.profile_name == profile_name
        ]
        
        if not matching_sessions:
            return None
        
        # Return the most recently accessed session
        latest_session = max(matching_sessions, key=lambda s: s.last_accessed)
        latest_session.last_accessed = datetime.now()
        self._save_sessions()
        return latest_session
    
    def list_sessions(self) -> List[BrowserSession]:
        """Get list of all active sessions.
        
        Returns:
            List of BrowserSession objects
        """
        return list(self.active_sessions.values())
    
    def list_profiles(self) -> List[str]:
        """Get list of all profile names.
        
        Returns:
            List of profile names
        """
        profiles = set()
        for session in self.active_sessions.values():
            profiles.add(session.profile_name)
        return sorted(list(profiles))
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its associated profile.
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if deletion was successful, False otherwise
        """
        session = self.active_sessions.get(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return False
        
        try:
            # Remove profile directory
            profile_path = Path(session.profile_path)
            if profile_path.exists():
                shutil.rmtree(profile_path)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            self._save_sessions()
            
            logger.info(f"Deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions based on timeout configuration.
        
        Returns:
            Number of sessions cleaned up
        """
        return self._cleanup_expired_sessions()
    
    def save_session_data(self, session_id: str, cookies: Optional[List[Dict[str, Any]]] = None,
                         local_storage: Optional[Dict[str, str]] = None,
                         session_storage: Optional[Dict[str, str]] = None,
                         current_domain: Optional[str] = None) -> bool:
        """Save session data (cookies, storage) for persistence.
        
        Args:
            session_id: The session identifier
            cookies: List of cookie dictionaries
            local_storage: Local storage data
            session_storage: Session storage data
            current_domain: Current domain for cookie storage
            
        Returns:
            True if save was successful, False otherwise
        """
        session = self.active_sessions.get(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return False
        
        try:
            # Update cookies for the current domain
            if cookies and current_domain:
                session.domain_cookies[current_domain] = cookies
            
            # Update local storage for the current domain
            if local_storage and current_domain:
                session.local_storage[current_domain] = local_storage
            
            # Update session storage for the current domain
            if session_storage and current_domain:
                session.session_storage[current_domain] = session_storage
            
            # Update last accessed time
            session.last_accessed = datetime.now()
            
            # Save to file
            self._save_sessions()
            
            logger.debug(f"Saved session data for: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session data for {session_id}: {e}")
            return False
    
    def restore_session_data(self, session_id: str, domain: str) -> Dict[str, Any]:
        """Restore session data for a specific domain.
        
        Args:
            session_id: The session identifier
            domain: The domain to restore data for
            
        Returns:
            Dictionary with cookies, local_storage, and session_storage
        """
        session = self.active_sessions.get(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return {"cookies": [], "local_storage": {}, "session_storage": {}}
        
        return {
            "cookies": session.domain_cookies.get(domain, []),
            "local_storage": session.local_storage.get(domain, {}),
            "session_storage": session.session_storage.get(domain, {}),
        }
    
    def get_browser_config_for_session(self, session_id: str) -> BrowserConfig:
        """Get browser configuration with session profile path.
        
        Args:
            session_id: The session identifier
            
        Returns:
            BrowserConfig with profile path set
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        config = BrowserConfig()
        config.profile_path = session.profile_path
        return config
    
    def _load_sessions(self) -> None:
        """Load sessions from the sessions file."""
        if not self.sessions_file.exists():
            logger.info("No existing sessions file found")
            return
        
        try:
            with open(self.sessions_file, 'r') as f:
                sessions_data = json.load(f)
            
            for session_data in sessions_data:
                session = BrowserSession.from_dict(session_data)
                self.active_sessions[session.session_id] = session
            
            logger.info(f"Loaded {len(self.active_sessions)} sessions")
            
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            # Create backup of corrupted file
            backup_file = self.sessions_file.with_suffix('.json.backup')
            if self.sessions_file.exists():
                shutil.copy2(self.sessions_file, backup_file)
            self.active_sessions = {}
    
    def _save_sessions(self) -> None:
        """Save sessions to the sessions file."""
        try:
            sessions_data = [session.to_dict() for session in self.active_sessions.values()]
            
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
            
            logger.debug(f"Saved {len(sessions_data)} sessions")
            
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    def _cleanup_expired_sessions(self) -> int:
        """Remove expired sessions based on timeout."""
        if self.session_timeout_days <= 0:
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=self.session_timeout_days)
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if session.last_accessed < cutoff_date:
                expired_sessions.append(session_id)
        
        # Delete expired sessions
        deleted_count = 0
        for session_id in expired_sessions:
            if self.delete_session(session_id):
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired sessions")
        
        return deleted_count
    
    def _enforce_session_limit(self) -> None:
        """Enforce maximum number of sessions by removing oldest ones."""
        if len(self.active_sessions) <= self.max_sessions:
            return
        
        # Sort sessions by last accessed time (oldest first)
        sorted_sessions = sorted(
            self.active_sessions.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Remove oldest sessions to get under the limit
        sessions_to_remove = len(self.active_sessions) - self.max_sessions
        for i in range(sessions_to_remove):
            session_id = sorted_sessions[i][0]
            self.delete_session(session_id)
        
        logger.info(f"Removed {sessions_to_remove} sessions to enforce limit")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about current sessions.
        
        Returns:
            Dictionary with session statistics
        """
        total_sessions = len(self.active_sessions)
        active_sessions = sum(1 for s in self.active_sessions.values() if s.is_active)
        profiles = len(self.list_profiles())
        
        # Calculate storage usage
        total_cookies = sum(
            len(cookies) for session in self.active_sessions.values()
            for cookies in session.domain_cookies.values()
        )
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "unique_profiles": profiles,
            "total_cookies": total_cookies,
            "max_sessions": self.max_sessions,
            "timeout_days": self.session_timeout_days,
        }