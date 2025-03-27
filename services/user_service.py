import logging
import os
import json
import pymongo
from typing import Dict, List, Optional, Any
from datetime import datetime
from models.user import User
from models.track import Track

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, mongodb_uri: Optional[str] = None):
        """Initialize the user service with optional MongoDB connection"""
        self.users: Dict[int, User] = {}  # In-memory users cache
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI")
        self.db = None
        
        # Try to connect to MongoDB if URI is provided
        if self.mongodb_uri:
            try:
                self.client = pymongo.MongoClient(self.mongodb_uri)
                self.db = self.client.mastermusic
                logger.info("Connected to MongoDB")
            except Exception as e:
                logger.error(f"Error connecting to MongoDB: {str(e)}")
    
    def get_user(self, user_id: int) -> User:
        """Get or create a user by ID"""
        # First check the in-memory cache
        if user_id in self.users:
            return self.users[user_id]
        
        # Then try to load from the database
        if self.db:
            user_data = self.db.users.find_one({"id": user_id})
            if user_data:
                # Convert MongoDB ObjectId to string
                if "_id" in user_data:
                    user_data["_id"] = str(user_data["_id"])
                
                user = User.from_dict(user_data)
                self.users[user_id] = user
                return user
        
        # Create a new user if not found
        user = User(id=user_id)
        self.users[user_id] = user
        
        # Save to database
        self._save_user(user)
        
        return user
    
    def update_user(self, user: User) -> bool:
        """Update a user in the database"""
        self.users[user.id] = user
        return self._save_user(user)
    
    def _save_user(self, user: User) -> bool:
        """Save a user to MongoDB"""
        if not self.db:
            return False
        
        try:
            user_dict = user.to_dict()
            
            # Ensure datetime objects are serialized properly
            for key, value in user_dict.items():
                if isinstance(value, datetime):
                    user_dict[key] = value.isoformat()
            
            self.db.users.update_one(
                {"id": user.id},
                {"$set": user_dict},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving user {user.id}: {str(e)}")
            return False
    
    def add_favorite(self, user_id: int, track_id: str) -> bool:
        """Add a track to user's favorites"""
        user = self.get_user(user_id)
        user.add_to_favorites(track_id)
        return self.update_user(user)
    
    def remove_favorite(self, user_id: int, track_id: str) -> bool:
        """Remove a track from user's favorites"""
        user = self.get_user(user_id)
        user.remove_from_favorites(track_id)
        return self.update_user(user)
    
    def get_favorites(self, user_id: int) -> List[str]:
        """Get a user's favorite tracks"""
        user = self.get_user(user_id)
        return user.favorite_tracks
    
    def add_to_history(self, user_id: int, track_id: str) -> bool:
        """Add a track to user's history"""
        user = self.get_user(user_id)
        user.add_to_history(track_id)
        return self.update_user(user)
    
    def get_history(self, user_id: int, limit: int = 10) -> List[str]:
        """Get a user's listening history"""
        user = self.get_user(user_id)
        return user.history[:limit]
    
    def set_preference(self, user_id: int, key: str, value: Any) -> bool:
        """Set a user preference"""
        user = self.get_user(user_id)
        if not hasattr(user, "settings"):
            user.settings = {}
        
        user.settings[key] = value
        return self.update_user(user)
    
    def get_preference(self, user_id: int, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        user = self.get_user(user_id)
        if not hasattr(user, "settings") or key not in user.settings:
            return default
        
        return user.settings.get(key, default)
    
    def update_last_active(self, user_id: int) -> bool:
        """Update a user's last active timestamp"""
        user = self.get_user(user_id)
        user.update_last_active()
        return self.update_user(user)
    
    def set_volume(self, user_id: int, volume: int) -> int:
        """Set a user's preferred volume"""
        volume = max(0, min(100, volume))
        user = self.get_user(user_id)
        user.volume = volume
        self.update_user(user)
        return volume
    
    def get_volume(self, user_id: int) -> int:
        """Get a user's preferred volume"""
        user = self.get_user(user_id)
        return user.volume
    
    def get_all_users(self) -> List[User]:
        """Get all users (admin function)"""
        if not self.db:
            return list(self.users.values())
        
        try:
            user_data = list(self.db.users.find())
            users = []
            
            for data in user_data:
                # Convert MongoDB ObjectId to string
                if "_id" in data:
                    data["_id"] = str(data["_id"])
                
                user = User.from_dict(data)
                # Update cache
                self.users[user.id] = user
                users.append(user)
            
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            return list(self.users.values()) 