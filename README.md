# MasterMusic Telegram Bot

A feature-rich Telegram bot for playing music, managing playlists, and enjoying music with friends in group chats.

## Features

### Music Playback
- 🎵 Search and play music from YouTube
- ⏯️ Basic controls: play, pause, resume, stop
- ⏭️ Queue management: skip, previous, view queue
- 🔊 Volume control and audio settings
- 🔄 Loop modes (none, single track, all)
- 🔀 Shuffle mode

### Playlist Management
- 📋 Create and manage personal playlists
- 👀 View, edit, and share playlists
- ➕ Add currently playing songs to playlists
- 📊 Search public playlists

### Spotify Integration
- 🎧 Search and play tracks from Spotify
- 📚 Import Spotify playlists with a single click
- 💿 Support for Spotify albums and tracks

### Enhanced Features
- 🎤 Lyrics display for playing songs
- 🌐 Support for multiple languages
- 📱 User preferences and settings
- 🗣️ Voice message to text conversion

### Admin Features
- 📊 Usage statistics
- 🧹 Automatic cleanup of old files
- 📢 Broadcast messages to all users

## Requirements

- Python 3.7+
- FFmpeg (for audio conversion)
- MongoDB (optional, for persistent storage)
- Spotify API credentials (optional, for Spotify integration)
- Genius API key (optional, for lyrics)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mastermusic-bot.git
cd mastermusic-bot
```

2. Install the requirements:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg (if not already installed):
   - On Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - On macOS with Homebrew: `brew install ffmpeg`
   - On Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

4. Create a `.env` file with your configuration:
```
# Required
TOKEN=your_telegram_bot_token_here

# Optional - Spotify API credentials
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here

# Optional - Genius API key for lyrics
GENIUS_API_KEY=your_genius_api_key_here

# Optional - MongoDB connection
MONGODB_URI=mongodb://localhost:27017/mastermusic

# Optional - Admin user IDs (comma-separated)
ADMIN_IDS=1234567890,0987654321

# Optional - Download path
DOWNLOAD_PATH=./downloads
```

5. Run the bot:
```bash
python bot.py
```

## Command List

### Basic Commands
- `/start` - Start the bot
- `/help` - Show available commands
- `/search [query]` - Search for music
- `/play [query/number]` - Play music
- `/pause` - Pause current playback
- `/resume` - Resume playback
- `/stop` - Stop playback
- `/skip` - Skip to next track
- `/prev` - Play previous track
- `/queue` - Show the current queue
- `/clear` - Clear the queue
- `/current` - Show currently playing track
- `/volume [0-100]` - Set volume

### Playlist Commands
- `/createplaylist [name] [description]` - Create a new playlist
- `/myplaylists` - List your playlists
- `/viewplaylist [name/number]` - View a playlist
- `/playplaylist [name/number]` - Play a playlist
- `/addtoplaylist` - Add the current track to a playlist
- `/searchplaylists [query]` - Search public playlists

### Spotify Commands
- `/spotify [query]` - Search Spotify
- Share a Spotify link to import tracks, playlists, or albums

### Other Commands
- `/lyrics` - Show lyrics for the current song
- `/settings` - Adjust your personal settings

### Admin Commands
- `/stats` - Show bot statistics (admin only)
- `/cleanup [days]` - Remove old downloads (admin only) 
- `/broadcast [message]` - Send message to all users (admin only)

## Project Structure

```
mastermusic-bot/
├── bot.py                 # Main entry point
├── .env                   # Environment configuration
├── requirements.txt       # Python dependencies
├── README.md              # Documentation
├── models/                # Data models
│   ├── user.py            # User model
│   ├── track.py           # Track model
│   └── playlist.py        # Playlist model
├── services/              # Business logic
│   ├── music_service.py   # Music playback and search
│   ├── queue_service.py   # Queue management
│   ├── user_service.py    # User data management
│   ├── playlist_service.py # Playlist management
│   ├── spotify_service.py # Spotify integration
│   ├── lyrics_service.py  # Lyrics fetching
│   └── voice_service.py   # Voice message handling
├── handlers/              # Telegram command handlers
│   ├── basic_commands.py  # Basic commands
│   ├── music_commands.py  # Music playback commands
│   ├── playlist_commands.py # Playlist commands
│   ├── spotify_commands.py  # Spotify integration
│   └── admin_commands.py  # Admin commands
└── utils/                 # Utility functions
    ├── validators.py      # Input validation
    └── formatters.py      # Text formatting
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [spotipy](https://github.com/spotipy-dev/spotipy) - Spotify API client
- [lyricsgenius](https://github.com/johnwmillr/LyricsGenius) - Genius lyrics API client
