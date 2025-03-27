import os
import logging
import asyncio
import yt_dlp
from pytube import Search, YouTube
from typing import List, Dict, Optional, Any, Tuple
import uuid
import re
import random
from pydub import AudioSegment
from urllib.parse import urlparse, parse_qs
import aiohttp

from models.track import Track
from utils.validators import validate_youtube_url, validate_url
from utils.formatters import clean_filename

logger = logging.getLogger(__name__)

class MusicService:
    def __init__(self, download_path="./downloads"):
        self.download_path = download_path
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        
        # Current playback state
        self.current_track = None
        self.queue = []
        self.history = []
        self.is_playing = False
        self.is_paused = False
        self.volume = 100
        self.loop_mode = "none"  # none, single, all
        self.shuffle_mode = False
        
        # YT-DLP options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }

    async def search(self, query: str, max_results: int = 10) -> List[Track]:
        """Search for videos on Youtube using yt-dlp"""
        try:
            # Check if the query is a URL
            if validate_url(query):
                is_youtube, video_id = validate_youtube_url(query)
                if is_youtube:
                    # Direct YouTube URL
                    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                        info = ydl.extract_info(query, download=False)
                        track = Track(
                            id=info['id'],
                            title=info['title'],
                            artist=info.get('uploader', 'Unknown'),
                            url=query,
                            thumbnail=info.get('thumbnail'),
                            duration=info.get('duration'),
                            source="youtube"
                        )
                        return [track]
            
            # Regular search query using yt-dlp instead of pytube
            search_url = f"ytsearch{max_results}:{query}"
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(search_url, download=False)
                formatted_results = []
                
                if 'entries' in info:
                    for entry in info['entries']:
                        # Get thumbnail for better UI
                        try:
                            thumbnail = f"https://i.ytimg.com/vi/{entry['id']}/hqdefault.jpg"
                        except:
                            thumbnail = None
                        
                        track = Track(
                            id=entry['id'],
                            title=entry['title'],
                            artist=entry.get('uploader', 'Unknown'),
                            url=f"https://youtube.com/watch?v={entry['id']}",
                            thumbnail=thumbnail,
                            duration=entry.get('duration'),
                            source="youtube"
                        )
                        formatted_results.append(track)
                
                return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching for '{query}': {str(e)}")
            return []
    
    async def download(self, track: Track) -> Optional[str]:
        """Stream a track and return the file path"""
        try:
            # Check if already downloaded
            title_safe = clean_filename(f"{track.title}")
            possible_paths = [
                f"{self.download_path}/{title_safe}.mp3",
                f"{self.download_path}/{title_safe}.ogg",
                f"{self.download_path}/{title_safe}.m4a",
                f"{self.download_path}/{track.id}.mp3"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    logger.info(f"Track already downloaded: {path}")
                    return path
            
            # Download the track
            logger.info(f"Downloading track: {track.title} ({track.url})")
            
            # Custom output template based on track ID for consistency
            custom_opts = self.ydl_opts.copy()
            custom_opts['outtmpl'] = f'{self.download_path}/{track.id}.%(ext)s'
            custom_opts['format'] = 'bestaudio/best'
            custom_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            
            try:
                with yt_dlp.YoutubeDL(custom_opts) as ydl:
                    info = ydl.extract_info(track.url, download=True)
                    # The file should be in the format {track.id}.mp3 after extraction
                    expected_path = f"{self.download_path}/{track.id}.mp3"
                    
                    if os.path.exists(expected_path):
                        logger.info(f"Successfully downloaded to {expected_path}")
                        return expected_path
            except Exception as e:
                logger.error(f"Error with yt-dlp download: {str(e)}")
                
                # Fallback: try a simpler approach with different options
                fallback_opts = {
                    'format': 'mp3/bestaudio/best',
                    'outtmpl': f'{self.download_path}/{track.id}.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '128',
                    }],
                    'quiet': True,
                }
                
                try:
                    with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                        ydl.download([track.url])
                        expected_path = f"{self.download_path}/{track.id}.mp3"
                        if os.path.exists(expected_path):
                            logger.info(f"Fallback download succeeded: {expected_path}")
                            return expected_path
                except Exception as fallback_error:
                    logger.error(f"Fallback download also failed: {str(fallback_error)}")
                
            # Last resort: check if any file in the download directory contains the track ID
            for filename in os.listdir(self.download_path):
                if filename.endswith(('.mp3', '.ogg', '.m4a')) and (track.id in filename or clean_filename(track.title) in filename.lower()):
                    full_path = f"{self.download_path}/{filename}" 
                    logger.info(f"Found matching file: {full_path}")
                    return full_path
            
            logger.error(f"Could not find downloaded file for {track.title}")
            return None
        
        except Exception as e:
            logger.error(f"Error downloading '{track.title}': {str(e)}")
            return None
    
    async def play_music(self, query: str) -> Optional[Track]:
        """Search and play music"""
        # Search for the track
        logger.info(f"Searching for: {query}")
        results = await self.search(query)
        if not results:
            logger.warning(f"No results found for '{query}'")
            return None
        
        logger.info(f"Found {len(results)} results, selecting first: {results[0].title}")
        track = results[0]
        await self.add_to_queue(track)
        
        # If nothing is currently playing, start playing
        if not self.is_playing and not self.is_paused:
            return await self.play_next()
        
        return track
    
    async def play_next(self) -> Optional[Track]:
        """Play the next track in the queue"""
        if not self.queue:
            self.is_playing = False
            self.current_track = None
            return None
        
        # Get the next track
        track = self.queue.pop(0)
        self.current_track = track
        
        # Add to history
        if self.current_track:
            self.history.insert(0, self.current_track)
            # Keep history limited to 50 items
            if len(self.history) > 50:
                self.history = self.history[:50]
        
        # Simulate playing (in a real implementation, this would use a media player)
        self.is_playing = True
        self.is_paused = False
        
        return track
    
    async def pause_music(self) -> bool:
        """Pause the current track"""
        if self.is_playing and not self.is_paused:
            self.is_paused = True
            return True
        return False
    
    async def resume_music(self) -> bool:
        """Resume the paused track"""
        if self.is_paused:
            self.is_paused = False
            return True
        return False
    
    async def stop_music(self) -> bool:
        """Stop the current playback"""
        if self.is_playing or self.is_paused:
            self.is_playing = False
            self.is_paused = False
            return True
        return False
    
    async def skip_music(self) -> Optional[Track]:
        """Skip to the next track"""
        if self.loop_mode == "single" and self.current_track:
            # When looping a single track, add it back to the queue
            self.queue.insert(0, self.current_track)
        
        return await self.play_next()
    
    async def previous_music(self) -> Optional[Track]:
        """Go back to the previous track"""
        if len(self.history) < 2:  # Need at least 2 (current + previous)
            return None
        
        # Current track is already in history[0], so we want history[1]
        prev_track = self.history[1]
        
        # Add current track back to the beginning of the queue
        if self.current_track:
            self.queue.insert(0, self.current_track)
        
        # Set the previous track as current
        self.current_track = prev_track
        
        # Remove from history (it will be added back on next play)
        self.history.remove(prev_track)
        
        self.is_playing = True
        self.is_paused = False
        
        return prev_track
    
    async def add_to_queue(self, track: Track) -> bool:
        """Add a track to the queue"""
        self.queue.append(track)
        return True
    
    async def clear_queue(self) -> bool:
        """Clear the playback queue"""
        self.queue = []
        return True
    
    async def get_queue(self) -> List[Track]:
        """Get the current queue"""
        return self.queue
    
    async def get_history(self) -> List[Track]:
        """Get the playback history"""
        return self.history
    
    async def current_music(self) -> Optional[Track]:
        """Get the currently playing track"""
        return self.current_track
    
    async def set_volume(self, volume: int) -> int:
        """Set the playback volume (0-100)"""
        self.volume = max(0, min(100, volume))
        return self.volume
    
    async def get_volume(self) -> int:
        """Get the current volume"""
        return self.volume
    
    async def toggle_loop(self) -> str:
        """Toggle loop mode (none -> single -> all -> none)"""
        if self.loop_mode == "none":
            self.loop_mode = "single"
        elif self.loop_mode == "single":
            self.loop_mode = "all"
        else:
            self.loop_mode = "none"
        
        return self.loop_mode
    
    async def toggle_shuffle(self) -> bool:
        """Toggle shuffle mode"""
        self.shuffle_mode = not self.shuffle_mode
        
        if self.shuffle_mode:
            # Shuffle the current queue
            random.shuffle(self.queue)
        
        return self.shuffle_mode
    
    async def get_lyrics(self, track: Optional[Track] = None) -> Optional[str]:
        """Get lyrics for a track (placeholder - implemented in LyricsService)"""
        return None
    
    async def get_track_info(self, track_id: str) -> Optional[Track]:
        """Get detailed info about a track by ID"""
        try:
            url = f"https://www.youtube.com/watch?v={track_id}"
            
            # Try to get info without downloading
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    
                    # Get thumbnail for better UI
                    try:
                        thumbnail = f"https://i.ytimg.com/vi/{track_id}/hqdefault.jpg"
                    except:
                        thumbnail = info.get('thumbnail')
                    
                    track = Track(
                        id=info['id'],
                        title=info['title'],
                        artist=info.get('uploader', 'Unknown'),
                        url=url,
                        thumbnail=thumbnail,
                        duration=info.get('duration'),
                        source="youtube"
                    )
                    return track
                except Exception as e:
                    logger.error(f"Error getting track info for '{track_id}': {str(e)}")
                    
                    # Fallback: Create a minimal track with just the ID and URL
                    track = Track(
                        id=track_id,
                        title=f"YouTube Video {track_id}",
                        artist="Unknown",
                        url=url,
                        thumbnail=f"https://i.ytimg.com/vi/{track_id}/hqdefault.jpg",
                        duration=0,
                        source="youtube"
                    )
                    return track
                
        except Exception as e:
            logger.error(f"Error getting track info for '{track_id}': {str(e)}")
            return None
    
    def cleanup_downloads(self, max_age_days: int = 7) -> int:
        """
        Clean up old downloads to save disk space
        Returns the number of files removed
        """
        import time
        from datetime import datetime, timedelta
        
        now = time.time()
        count = 0
        
        # Calculate the cutoff time
        cutoff = now - (max_age_days * 24 * 60 * 60)
        
        try:
            for filename in os.listdir(self.download_path):
                file_path = os.path.join(self.download_path, filename)
                
                # Skip directories and non-audio files
                if os.path.isdir(file_path) or not filename.endswith(('.mp3', '.ogg', '.m4a')):
                    continue
                
                # Check file age
                if os.path.getmtime(file_path) < cutoff:
                    os.remove(file_path)
                    count += 1
                    logger.info(f"Removed old file: {filename}")
            
            return count
        
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0
