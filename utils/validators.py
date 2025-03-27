import re
from typing import Union, Optional, Tuple


def validate_url(url: str) -> bool:
    """Check if a string is a valid URL"""
    url_pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


def validate_youtube_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a URL is a valid YouTube URL and extract the video ID
    Returns (is_valid, video_id)
    """
    patterns = [
        r'^https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})(?:&.*)?$',  # Regular YouTube URL
        r'^https?://youtu\.be/([a-zA-Z0-9_-]{11})(?:\?.*)?$',  # Short YouTube URL
        r'^https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})(?:\?.*)?$',  # Embed URL
        r'^https?://(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})(?:\?.*)?$',  # YouTube Shorts
    ]
    
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            return True, match.group(1)
    
    return False, None


def validate_spotify_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if a URL is a valid Spotify URL and extract the track/album/playlist ID
    Returns (is_valid, content_type, content_id)
    """
    patterns = {
        'track': r'^https?://open\.spotify\.com/track/([a-zA-Z0-9]{22})(?:\?.*)?$',
        'album': r'^https?://open\.spotify\.com/album/([a-zA-Z0-9]{22})(?:\?.*)?$',
        'playlist': r'^https?://open\.spotify\.com/playlist/([a-zA-Z0-9]{22})(?:\?.*)?$',
        'artist': r'^https?://open\.spotify\.com/artist/([a-zA-Z0-9]{22})(?:\?.*)?$',
    }
    
    for content_type, pattern in patterns.items():
        match = re.match(pattern, url)
        if match:
            return True, content_type, match.group(1)
    
    return False, None, None


def validate_youtube_playlist_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a URL is a valid YouTube playlist URL and extract the playlist ID
    Returns (is_valid, playlist_id)
    """
    patterns = [
        r'^https?://(?:www\.)?youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)(?:&.*)?$',  # Regular playlist URL
        r'^https?://(?:www\.)?youtube\.com/watch\?v=[a-zA-Z0-9_-]{11}&list=([a-zA-Z0-9_-]+)(?:&.*)?$',  # Video in playlist
    ]
    
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            return True, match.group(1)
    
    return False, None
