import logging
import os
import aiohttp
import lyricsgenius
import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import json
import asyncio

from models.track import Track
from utils.formatters import format_message

logger = logging.getLogger(__name__)

class LyricsService:
    def __init__(self, genius_token: Optional[str] = None):
        """Initialize the lyrics service with optional Genius API token"""
        self.genius_token = genius_token or os.getenv("GENIUS_API_KEY")
        self.genius = None
        self.cache = {}  # Simple in-memory cache
        
        # Initialize Genius client if token is available
        if self.genius_token:
            try:
                self.genius = lyricsgenius.Genius(self.genius_token)
                self.genius.verbose = False  # Disable status messages
                logger.info("Initialized Genius API client")
            except Exception as e:
                logger.error(f"Error initializing Genius API: {str(e)}")
    
    async def get_lyrics(self, track: Track) -> Optional[str]:
        """Get lyrics for a track"""
        # Check cache first
        cache_key = f"{track.title}_{track.artist}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Try different methods to get lyrics
        lyrics = None
        
        # Method 1: Try using Genius API if available
        if self.genius:
            try:
                song = self.genius.search_song(track.title, track.artist)
                if song:
                    lyrics = song.lyrics
            except Exception as e:
                logger.error(f"Error fetching lyrics from Genius API: {str(e)}")
        
        # Method 2: Try web scraping if API failed
        if not lyrics:
            lyrics = await self._web_scrape_lyrics(track.title, track.artist)
        
        # Cache the result, even if None
        if lyrics:
            # Clean up the lyrics
            lyrics = self._clean_lyrics(lyrics)
            self.cache[cache_key] = lyrics
        
        return lyrics
    
    async def _web_scrape_lyrics(self, title: str, artist: str) -> Optional[str]:
        """Scrape lyrics from the web"""
        # Try multiple sources for lyrics
        sources = [
            self._scrape_lyrics_from_genius,
            self._scrape_lyrics_from_azlyrics,
            self._scrape_lyrics_from_musixmatch
        ]
        
        for source in sources:
            try:
                lyrics = await source(title, artist)
                if lyrics:
                    return lyrics
            except Exception as e:
                logger.error(f"Error scraping lyrics from {source.__name__}: {str(e)}")
        
        return None
    
    async def _scrape_lyrics_from_genius(self, title: str, artist: str) -> Optional[str]:
        """Scrape lyrics from Genius"""
        search_term = f"{artist} {title}"
        search_url = f"https://genius.com/api/search/song?q={search_term.replace(' ', '%20')}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                hits = data.get("response", {}).get("sections", [{}])[0].get("hits", [])
                
                if not hits:
                    return None
                
                song_url = hits[0].get("result", {}).get("url")
                if not song_url:
                    return None
                
                async with session.get(song_url) as song_response:
                    if song_response.status != 200:
                        return None
                    
                    html = await song_response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # Find the lyrics div
                    lyrics_div = soup.find("div", class_="lyrics") or soup.find("div", class_="Lyrics__Container-sc-1ynbvzw-6")
                    
                    if lyrics_div:
                        lyrics = lyrics_div.get_text()
                        return lyrics
        
        return None
    
    async def _scrape_lyrics_from_azlyrics(self, title: str, artist: str) -> Optional[str]:
        """Scrape lyrics from AZLyrics"""
        # Format the artist and title for the URL
        artist = artist.lower().replace(" ", "")
        title = title.lower().replace(" ", "")
        
        # Remove special characters
        artist = re.sub(r'[^\w\s]', '', artist)
        title = re.sub(r'[^\w\s]', '', title)
        
        url = f"https://www.azlyrics.com/lyrics/{artist}/{title}.html"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                
                # Find the lyrics div (AZLyrics has no class for the lyrics div)
                lyrics_div = soup.find("div", class_=None, id=None)
                
                if lyrics_div:
                    lyrics = lyrics_div.get_text().strip()
                    return lyrics
        
        return None
    
    async def _scrape_lyrics_from_musixmatch(self, title: str, artist: str) -> Optional[str]:
        """Scrape lyrics from Musixmatch"""
        search_term = f"{artist} {title}"
        search_url = f"https://www.musixmatch.com/search/{search_term.replace(' ', '%20')}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(search_url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                
                # Find the first search result
                result = soup.find("a", class_="title")
                if not result:
                    return None
                
                song_url = "https://www.musixmatch.com" + result.get("href")
                
                async with session.get(song_url) as song_response:
                    if song_response.status != 200:
                        return None
                    
                    song_html = await song_response.text()
                    song_soup = BeautifulSoup(song_html, "html.parser")
                    
                    # Find the lyrics divs
                    lyrics_divs = song_soup.find_all("p", class_="mxm-lyrics__content")
                    
                    if lyrics_divs:
                        lyrics = "\n".join([div.get_text() for div in lyrics_divs])
                        return lyrics
        
        return None
    
    def _clean_lyrics(self, lyrics: str) -> str:
        """Clean up lyrics text"""
        if not lyrics:
            return ""
        
        # Remove common headers and footers
        lyrics = re.sub(r'^\[.*?\]', '', lyrics)  # Remove [Verse], [Chorus], etc.
        lyrics = re.sub(r'\d+Embed$', '', lyrics)  # Remove Genius embed numbers
        lyrics = re.sub(r'You might also like', '', lyrics)  # Remove Genius suggestions
        
        # Remove extra whitespace
        lyrics = re.sub(r'\n{3,}', '\n\n', lyrics)
        lyrics = lyrics.strip()
        
        return lyrics
    
    async def search_song(self, query: str) -> Optional[Dict[str, Any]]:
        """Search for a song in Genius"""
        if not self.genius:
            return None
        
        try:
            result = self.genius.search_song(query)
            if result:
                return {
                    "title": result.title,
                    "artist": result.artist,
                    "lyrics": self._clean_lyrics(result.lyrics),
                    "url": result.url,
                    "album": result.album,
                    "featured_artists": result.featured_artists,
                    "release_date": result.release_date
                }
        except Exception as e:
            logger.error(f"Error searching song '{query}': {str(e)}")
        
        return None 