from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


class User(BaseModel):
    """Model representing a bot user"""
    id: int  # Telegram user ID
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    preferred_quality: str = "192k"
    volume: int = 100
    favorite_tracks: List[str] = Field(default_factory=list)  # List of track IDs
    history: List[str] = Field(default_factory=list)  # List of track IDs
    registered_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)
    settings: Dict = Field(default_factory=dict)  # User settings

    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "language_code": self.language_code,
            "preferred_quality": self.preferred_quality,
            "volume": self.volume,
            "favorite_tracks": self.favorite_tracks,
            "history": self.history,
            "registered_at": self.registered_at,
            "last_active": self.last_active,
            "settings": self.settings
        }
    
    @staticmethod
    def from_dict(data: dict):
        """Create User from dictionary"""
        return User(**data)
    
    def add_to_history(self, track_id: str, max_history: int = 50):
        """Add track to user history"""
        # Remove if already in history (to move it to the top)
        if track_id in self.history:
            self.history.remove(track_id)
        
        # Add to the beginning of the list
        self.history.insert(0, track_id)
        
        # Trim to max size
        if len(self.history) > max_history:
            self.history = self.history[:max_history]
    
    def add_to_favorites(self, track_id: str):
        """Add track to favorites"""
        if track_id not in self.favorite_tracks:
            self.favorite_tracks.append(track_id)
    
    def remove_from_favorites(self, track_id: str):
        """Remove track from favorites"""
        if track_id in self.favorite_tracks:
            self.favorite_tracks.remove(track_id)
    
    def update_last_active(self):
        """Update last active timestamp"""
        self.last_active = datetime.now()
