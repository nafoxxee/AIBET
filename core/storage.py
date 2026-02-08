"""
AIBET Core Storage
Simple in-memory storage for Timeweb deployment
"""

from typing import Dict, Any, Optional
from datetime import datetime


class Storage:
    """Simple in-memory storage"""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._users: Dict[int, Dict[str, Any]] = {}
    
    def set(self, key: str, value: Any) -> None:
        """Set value by key"""
        self._data[key] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key"""
        if key in self._data:
            return self._data[key]["value"]
        return default
    
    def set_user_data(self, user_id: int, key: str, value: Any) -> None:
        """Set user-specific data"""
        if user_id not in self._users:
            self._users[user_id] = {}
        self._users[user_id][key] = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_user_data(self, user_id: int, key: str, default: Any = None) -> Any:
        """Get user-specific data"""
        if user_id in self._users and key in self._users[user_id]:
            return self._users[user_id][key]["value"]
        return default
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        return {
            "total_keys": len(self._data),
            "total_users": len(self._users),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global storage instance
storage = Storage()
