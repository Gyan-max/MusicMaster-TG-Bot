from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Track(BaseModel):
    """Model representing a music track"""
    id: str
    title: str
    artist: str
    url: str
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    source: str = "youtube"  # youtube, spotify, etc
    added_at: datetime = Field(default_factory=datetime.now)
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "url": self.url,
            "thumbnail": self.thumbnail,
            "duration": self.duration,
            "source": self.source,
            "added_at": self.added_at
        }
    
    @staticmethod
    def from_dict(data: dict):
        """Create Track from dictionary"""
        return Track(**data)
    
    def display_info(self):
        """Return formatted track info for display"""
        duration_str = ""
        if self.duration:
            minutes = self.duration // 60
            seconds = self.duration % 60
            duration_str = f" [{minutes}:{seconds:02d}]"
            
        return f"{self.title} - {self.artist}{duration_str}" 