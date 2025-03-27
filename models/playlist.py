from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class Playlist(BaseModel):
    """Model representing a music playlist"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    user_id: int  # Owner's Telegram ID
    tracks: List[str] = Field(default_factory=list)  # List of track IDs
    is_public: bool = False
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    thumbnail: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "tracks": self.tracks,
            "is_public": self.is_public,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "thumbnail": self.thumbnail
        }
    
    @staticmethod
    def from_dict(data: dict):
        """Create Playlist from dictionary"""
        return Playlist(**data)
    
    def add_track(self, track_id: str):
        """Add track to playlist"""
        if track_id not in self.tracks:
            self.tracks.append(track_id)
            self.updated_at = datetime.now()
            return True
        return False
    
    def remove_track(self, track_id: str):
        """Remove track from playlist"""
        if track_id in self.tracks:
            self.tracks.remove(track_id)
            self.updated_at = datetime.now()
            return True
        return False
    
    def clear(self):
        """Clear all tracks from playlist"""
        self.tracks = []
        self.updated_at = datetime.now()
    
    def reorder_track(self, old_position: int, new_position: int):
        """Move a track from one position to another"""
        if 0 <= old_position < len(self.tracks) and 0 <= new_position < len(self.tracks):
            track = self.tracks.pop(old_position)
            self.tracks.insert(new_position, track)
            self.updated_at = datetime.now()
            return True
        return False
