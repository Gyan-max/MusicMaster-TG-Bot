import logging
import os
import pymongo
from typing import List, Dict, Optional, Any
from datetime import datetime

from models.playlist import Playlist
from models.track import Track

logger = logging.getLogger(__name__)

class PlaylistService:
    def __init__(self, mongodb_uri: Optional[str] = None):
        """Initialize the playlist service with optional MongoDB connection"""
        self.playlists: Dict[str, Playlist] = {}  # In-memory playlists cache
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI")
        self.db = None
        
        # Try to connect to MongoDB if URI is provided
        if self.mongodb_uri:
            try:
                self.client = pymongo.MongoClient(self.mongodb_uri)
                self.db = self.client.mastermusic
                logger.info("Connected to MongoDB for playlists")
            except Exception as e:
                logger.error(f"Error connecting to MongoDB: {str(e)}")
    
    def create_playlist(self, name: str, user_id: int, description: Optional[str] = None,
                         is_public: bool = False) -> Playlist:
        """Create a new playlist"""
        playlist = Playlist(
            name=name,
            user_id=user_id,
            description=description,
            is_public=is_public
        )
        
        # Save to memory cache
        self.playlists[playlist.id] = playlist
        
        # Save to database
        self._save_playlist(playlist)
        
        return playlist
    
    def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """Get a playlist by ID"""
        # First check the in-memory cache
        if playlist_id in self.playlists:
            return self.playlists[playlist_id]
        
        # Then try to load from the database
        if self.db:
            playlist_data = self.db.playlists.find_one({"id": playlist_id})
            if playlist_data:
                # Convert MongoDB ObjectId to string
                if "_id" in playlist_data:
                    playlist_data["_id"] = str(playlist_data["_id"])
                
                playlist = Playlist.from_dict(playlist_data)
                self.playlists[playlist_id] = playlist
                return playlist
        
        return None
    
    def update_playlist(self, playlist: Playlist) -> bool:
        """Update a playlist in the database"""
        self.playlists[playlist.id] = playlist
        return self._save_playlist(playlist)
    
    def _save_playlist(self, playlist: Playlist) -> bool:
        """Save a playlist to MongoDB"""
        if not self.db:
            return False
        
        try:
            playlist_dict = playlist.to_dict()
            
            # Ensure datetime objects are serialized properly
            for key, value in playlist_dict.items():
                if isinstance(value, datetime):
                    playlist_dict[key] = value.isoformat()
            
            self.db.playlists.update_one(
                {"id": playlist.id},
                {"$set": playlist_dict},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving playlist {playlist.id}: {str(e)}")
            return False
    
    def get_user_playlists(self, user_id: int) -> List[Playlist]:
        """Get all playlists owned by a user"""
        if not self.db:
            # If no database, filter in-memory playlists
            return [p for p in self.playlists.values() if p.user_id == user_id]
        
        try:
            playlists_data = list(self.db.playlists.find({"user_id": user_id}))
            playlists = []
            
            for data in playlists_data:
                # Convert MongoDB ObjectId to string
                if "_id" in data:
                    data["_id"] = str(data["_id"])
                
                playlist = Playlist.from_dict(data)
                # Update cache
                self.playlists[playlist.id] = playlist
                playlists.append(playlist)
            
            return playlists
        except Exception as e:
            logger.error(f"Error getting playlists for user {user_id}: {str(e)}")
            # Fall back to in-memory playlists
            return [p for p in self.playlists.values() if p.user_id == user_id]
    
    def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist"""
        # Remove from memory cache
        if playlist_id in self.playlists:
            del self.playlists[playlist_id]
        
        # Remove from database
        if self.db:
            try:
                self.db.playlists.delete_one({"id": playlist_id})
                return True
            except Exception as e:
                logger.error(f"Error deleting playlist {playlist_id}: {str(e)}")
                return False
        
        return True
    
    def add_track_to_playlist(self, playlist_id: str, track_id: str) -> bool:
        """Add a track to a playlist"""
        playlist = self.get_playlist(playlist_id)
        if not playlist:
            return False
        
        success = playlist.add_track(track_id)
        if success:
            return self.update_playlist(playlist)
        
        return False
    
    def remove_track_from_playlist(self, playlist_id: str, track_id: str) -> bool:
        """Remove a track from a playlist"""
        playlist = self.get_playlist(playlist_id)
        if not playlist:
            return False
        
        success = playlist.remove_track(track_id)
        if success:
            return self.update_playlist(playlist)
        
        return False
    
    def get_playlist_tracks(self, playlist_id: str) -> List[str]:
        """Get all track IDs in a playlist"""
        playlist = self.get_playlist(playlist_id)
        if not playlist:
            return []
        
        return playlist.tracks
    
    def clear_playlist(self, playlist_id: str) -> bool:
        """Clear all tracks from a playlist"""
        playlist = self.get_playlist(playlist_id)
        if not playlist:
            return False
        
        playlist.clear()
        return self.update_playlist(playlist)
    
    def search_playlists(self, query: str, limit: int = 10) -> List[Playlist]:
        """Search public playlists by name"""
        if not self.db:
            # If no database, search in-memory playlists
            return [p for p in self.playlists.values() 
                   if p.is_public and query.lower() in p.name.lower()][:limit]
        
        try:
            # Create text index if it doesn't exist
            try:
                self.db.playlists.create_index([("name", "text")])
            except:
                pass
            
            # Search using text index
            playlists_data = list(self.db.playlists.find(
                {"$and": [
                    {"is_public": True},
                    {"$text": {"$search": query}}
                ]}
            ).limit(limit))
            
            # If no results with text search, use regex
            if not playlists_data:
                playlists_data = list(self.db.playlists.find(
                    {"$and": [
                        {"is_public": True},
                        {"name": {"$regex": query, "$options": "i"}}
                    ]}
                ).limit(limit))
            
            playlists = []
            for data in playlists_data:
                # Convert MongoDB ObjectId to string
                if "_id" in data:
                    data["_id"] = str(data["_id"])
                
                playlist = Playlist.from_dict(data)
                # Update cache
                self.playlists[playlist.id] = playlist
                playlists.append(playlist)
            
            return playlists
        except Exception as e:
            logger.error(f"Error searching playlists for '{query}': {str(e)}")
            # Fall back to in-memory playlists
            return [p for p in self.playlists.values() 
                   if p.is_public and query.lower() in p.name.lower()][:limit] 