import logging
import os
import sys
from dotenv import load_dotenv
from telegram.ext import Application

# Add FFmpeg to PATH (specific to this installation)
ffmpeg_path = r"C:\Users\gyan4\Downloads\Compressed\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin"
if os.path.exists(ffmpeg_path):
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")
    print(f"Added FFmpeg to PATH: {ffmpeg_path}")
else:
    print(f"FFmpeg path not found: {ffmpeg_path}")

# Import handlers
from handlers.basic_commands import register_basic_commands
from handlers.music_commands import register_music_commands
from handlers.playlist_commands import register_playlist_commands
from handlers.spotify_commands import register_spotify_commands
from handlers.admin_commands import register_admin_commands

# Import services
from services.music_service import MusicService
from services.queue_service import QueueService
from services.user_service import UserService
from services.playlist_service import PlaylistService
from services.spotify_service import SpotifyService
from services.lyrics_service import LyricsService
from services.voice_service import VoiceService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    # Get token from environment
    token = os.getenv("TOKEN")
    if not token:
        logger.error("No token provided. Set it in .env file")
        return
    
    # Get download path from environment or use default
    download_path = os.getenv("DOWNLOAD_PATH", "./downloads")
    
    # Initialize services
    music_service = MusicService(download_path=download_path)
    queue_service = QueueService()
    user_service = UserService(os.getenv("MONGODB_URI"))
    playlist_service = PlaylistService(os.getenv("MONGODB_URI"))
    spotify_service = SpotifyService(
        os.getenv("SPOTIFY_CLIENT_ID"),
        os.getenv("SPOTIFY_CLIENT_SECRET")
    )
    lyrics_service = LyricsService(os.getenv("GENIUS_API_KEY"))
    voice_service = VoiceService(downloads_path=download_path)
    
    # Build the application
    app = Application.builder().token(token).build()
    
    # Register command handlers with their required service instances
    register_basic_commands(app, (music_service, queue_service, user_service, lyrics_service))
    register_music_commands(app, (music_service, queue_service, user_service))
    register_playlist_commands(app, (playlist_service, music_service, queue_service, user_service))
    register_spotify_commands(app, (spotify_service, queue_service, music_service))
    register_admin_commands(app, (music_service, user_service))
    
    # Start the bot
    logger.info("Starting MasterMusic bot")
    app.run_polling()

if __name__ == "__main__":
    main()

