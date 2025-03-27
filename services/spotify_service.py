import logging
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Dict, Optional, Any, Tuple
import asyncio
import re

from models.track import Track
from utils.validators import validate_spotify_url

logger = logging.getLogger(__name__)

class SpotifyService:
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """Initialize the Spotify service with client credentials"""
        self.client_id = client_id or os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")
        self.spotify = None
        
        # Initialize Spotify client if credentials are available
        if self.client_id and self.client_secret:
            try:
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=self.client_id, 
                    client_secret=self.client_secret
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
                logger.info("Initialized Spotify API client")
            except Exception as e:
                logger.error(f"Error initializing Spotify API: {str(e)}")
    
    async def search_track(self, query: str, limit: int = 10) -> List[Track]:
        """Search for tracks on Spotify"""
        if not self.spotify:
            logger.warning("Spotify API not initialized")
            return []
        
        try:
            # Execute in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                lambda: self.spotify.search(q=query, type='track', limit=limit)
            )
            
            tracks = []
            for item in results['tracks']['items']:
                # Format artist names
                artists = [artist['name'] for artist in item['artists']]
                artist_str = ', '.join(artists)
                
                track = Track(
                    id=item['id'],
                    title=item['name'],
                    artist=artist_str,
                    url=item['external_urls']['spotify'],
                    thumbnail=item['album']['images'][0]['url'] if item['album']['images'] else None,
                    duration=item['duration_ms'] // 1000,  # Convert ms to seconds
                    source="spotify"
                )
                tracks.append(track)
            
            return tracks
        
        except Exception as e:
            logger.error(f"Error searching Spotify for '{query}': {str(e)}")
            return []
    
    async def get_track_by_url(self, url: str) -> Optional[Track]:
        """Get track info from a Spotify URL"""
        if not self.spotify:
            logger.warning("Spotify API not initialized")
            return None
        
        try:
            # Validate and extract track ID from URL
            is_valid, content_type, content_id = validate_spotify_url(url)
            
            if not is_valid or content_type != 'track' or not content_id:
                logger.warning(f"Invalid Spotify track URL: {url}")
                return None
            
            # Get track info
            loop = asyncio.get_event_loop()
            track_info = await loop.run_in_executor(
                None,
                lambda: self.spotify.track(content_id)
            )
            
            # Format artist names
            artists = [artist['name'] for artist in track_info['artists']]
            artist_str = ', '.join(artists)
            
            track = Track(
                id=track_info['id'],
                title=track_info['name'],
                artist=artist_str,
                url=track_info['external_urls']['spotify'],
                thumbnail=track_info['album']['images'][0]['url'] if track_info['album']['images'] else None,
                duration=track_info['duration_ms'] // 1000,  # Convert ms to seconds
                source="spotify"
            )
            
            return track
        
        except Exception as e:
            logger.error(f"Error getting Spotify track from URL '{url}': {str(e)}")
            return None
    
    async def get_playlist_tracks(self, playlist_url: str) -> List[Track]:
        """Get all tracks from a Spotify playlist"""
        if not self.spotify:
            logger.warning("Spotify API not initialized")
            return []
        
        try:
            # Extract playlist ID from URL
            is_valid, content_type, content_id = validate_spotify_url(playlist_url)
            
            if not is_valid or content_type != 'playlist' or not content_id:
                logger.warning(f"Invalid Spotify playlist URL: {playlist_url}")
                return []
            
            # Get playlist tracks
            tracks = []
            offset = 0
            limit = 100  # Spotify API limit
            
            loop = asyncio.get_event_loop()
            
            while True:
                # Get a batch of tracks
                results = await loop.run_in_executor(
                    None,
                    lambda: self.spotify.playlist_items(
                        content_id,
                        offset=offset,
                        limit=limit,
                        fields='items.track.id,items.track.name,items.track.artists,items.track.album,items.track.external_urls,items.track.duration_ms,total'
                    )
                )
                
                # Process tracks
                for item in results['items']:
                    if not item['track']:
                        continue
                    
                    track_info = item['track']
                    
                    # Format artist names
                    artists = [artist['name'] for artist in track_info['artists']]
                    artist_str = ', '.join(artists)
                    
                    # Get album image if available
                    thumbnail = None
                    if track_info['album'] and track_info['album']['images']:
                        thumbnail = track_info['album']['images'][0]['url']
                    
                    track = Track(
                        id=track_info['id'],
                        title=track_info['name'],
                        artist=artist_str,
                        url=track_info['external_urls']['spotify'],
                        thumbnail=thumbnail,
                        duration=track_info['duration_ms'] // 1000,  # Convert ms to seconds
                        source="spotify"
                    )
                    tracks.append(track)
                
                # Check if we need to fetch more
                offset += limit
                if offset >= results['total']:
                    break
            
            return tracks
        
        except Exception as e:
            logger.error(f"Error getting tracks from Spotify playlist '{playlist_url}': {str(e)}")
            return []
    
    async def get_album_tracks(self, album_url: str) -> List[Track]:
        """Get all tracks from a Spotify album"""
        if not self.spotify:
            logger.warning("Spotify API not initialized")
            return []
        
        try:
            # Extract album ID from URL
            is_valid, content_type, content_id = validate_spotify_url(album_url)
            
            if not is_valid or content_type != 'album' or not content_id:
                logger.warning(f"Invalid Spotify album URL: {album_url}")
                return []
            
            # Get album info (to get thumbnail)
            loop = asyncio.get_event_loop()
            album_info = await loop.run_in_executor(
                None,
                lambda: self.spotify.album(content_id)
            )
            
            thumbnail = album_info['images'][0]['url'] if album_info['images'] else None
            album_name = album_info['name']
            
            # Get album tracks
            tracks = []
            offset = 0
            limit = 50  # Spotify API limit
            
            while True:
                # Get a batch of tracks
                results = await loop.run_in_executor(
                    None,
                    lambda: self.spotify.album_tracks(
                        content_id,
                        offset=offset,
                        limit=limit
                    )
                )
                
                # Process tracks
                for track_info in results['items']:
                    # Format artist names
                    artists = [artist['name'] for artist in track_info['artists']]
                    artist_str = ', '.join(artists)
                    
                    track = Track(
                        id=track_info['id'],
                        title=track_info['name'],
                        artist=artist_str,
                        url=f"https://open.spotify.com/track/{track_info['id']}",
                        thumbnail=thumbnail,
                        duration=track_info['duration_ms'] // 1000,  # Convert ms to seconds
                        source="spotify"
                    )
                    tracks.append(track)
                
                # Check if we need to fetch more
                offset += limit
                if offset >= results['total']:
                    break
            
            return tracks
        
        except Exception as e:
            logger.error(f"Error getting tracks from Spotify album '{album_url}': {str(e)}")
            return [] 