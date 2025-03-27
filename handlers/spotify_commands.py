import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from typing import List, Dict

from services.spotify_service import SpotifyService
from services.queue_service import QueueService
from services.music_service import MusicService
from utils.validators import validate_spotify_url
from models.track import Track

logger = logging.getLogger(__name__)

# Initialize services
spotify_service = None
queue_service = None
music_service = None

def init_services(ss, qs, ms):
    global spotify_service, queue_service, music_service
    spotify_service = ss
    queue_service = qs
    music_service = ms

async def spotify_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for tracks on Spotify"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Please provide a search query.\nUsage: /spotify [search query]")
        return
    
    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 Searching Spotify for '{query}'...")
    
    tracks = await spotify_service.search_track(query)
    
    if not tracks:
        await update.message.reply_text(f"No results found for '{query}' on Spotify.")
        return
    
    # Display search results with buttons
    response = f"🎵 Spotify search results for '{query}':\n\n"
    keyboard = []
    
    for i, track in enumerate(tracks, 1):
        response += f"{i}. {track.title} - {track.artist}\n"
        keyboard.append([InlineKeyboardButton(
            f"Play {i}: {track.title[:30]}", callback_data=f"spotify_play:{track.id}"
        )])
    
    keyboard.append([InlineKeyboardButton(
        "Add all to queue", callback_data=f"spotify_add_all:{','.join([t.id for t in tracks])}"
    )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, reply_markup=reply_markup)

async def spotify_url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Spotify URLs shared in the chat"""
    url = update.message.text
    
    # Validate if it's a Spotify URL
    is_valid, content_type, content_id = validate_spotify_url(url)
    
    if not is_valid:
        return  # Not a Spotify URL, ignore
    
    await update.message.reply_text(f"📥 Processing Spotify {content_type}...")
    
    if content_type == "track":
        track = await spotify_service.get_track_by_url(url)
        if not track:
            await update.message.reply_text("❌ Failed to get track information from Spotify.")
            return
        
        # Add to queue
        chat_id = update.effective_chat.id
        queue_service.add_to_queue(chat_id, track)
        
        # If nothing is playing, start playback
        if not queue_service.get_current_track(chat_id):
            next_track = queue_service.get_next_track(chat_id)
            await update.message.reply_text(f"🎵 Now playing: {next_track.title} - {next_track.artist}")
        else:
            await update.message.reply_text(f"➕ Added to queue: {track.title} - {track.artist}")
    
    elif content_type == "playlist":
        await update.message.reply_text("🔄 Fetching playlist tracks from Spotify... This may take a moment.")
        tracks = await spotify_service.get_playlist_tracks(url)
        
        if not tracks:
            await update.message.reply_text("❌ Failed to get playlist tracks from Spotify or the playlist is empty.")
            return
        
        # Display playlist info
        chat_id = update.effective_chat.id
        
        keyboard = [
            [
                InlineKeyboardButton("Play Now", callback_data=f"spotify_play_list:{content_id}"),
                InlineKeyboardButton("Add to Queue", callback_data=f"spotify_queue_list:{content_id}")
            ],
            [
                InlineKeyboardButton("Shuffle Play", callback_data=f"spotify_shuffle_list:{content_id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"📋 Spotify Playlist: Found {len(tracks)} tracks\n\n"
            f"Select an action:",
            reply_markup=reply_markup
        )
    
    elif content_type == "album":
        await update.message.reply_text("🔄 Fetching album tracks from Spotify... This may take a moment.")
        tracks = await spotify_service.get_album_tracks(url)
        
        if not tracks:
            await update.message.reply_text("❌ Failed to get album tracks from Spotify or the album is empty.")
            return
        
        # Display album info
        chat_id = update.effective_chat.id
        
        keyboard = [
            [
                InlineKeyboardButton("Play Now", callback_data=f"spotify_play_album:{content_id}"),
                InlineKeyboardButton("Add to Queue", callback_data=f"spotify_queue_album:{content_id}")
            ],
            [
                InlineKeyboardButton("Shuffle Play", callback_data=f"spotify_shuffle_album:{content_id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"💿 Spotify Album: Found {len(tracks)} tracks\n\n"
            f"Select an action:",
            reply_markup=reply_markup
        )
    
    else:
        await update.message.reply_text(f"❌ Unsupported Spotify content type: {content_type}")

async def handle_spotify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Spotify-related callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")
    action = data[0]
    
    if action == "spotify_play":
        track_id = data[1]
        chat_id = update.effective_chat.id
        
        # Get track info
        track = await spotify_service.get_track_by_url(f"https://open.spotify.com/track/{track_id}")
        if not track:
            await query.edit_message_text("❌ Failed to get track information from Spotify.")
            return
        
        # Clear queue and add track
        queue_service.clear_queue(chat_id)
        queue_service.add_to_queue(chat_id, track)
        next_track = queue_service.get_next_track(chat_id)
        
        await query.edit_message_text(f"🎵 Now playing: {next_track.title} - {next_track.artist}")
    
    elif action == "spotify_add_all":
        track_ids = data[1].split(",")
        chat_id = update.effective_chat.id
        tracks_added = 0
        
        for track_id in track_ids:
            track = await spotify_service.get_track_by_url(f"https://open.spotify.com/track/{track_id}")
            if track:
                queue_service.add_to_queue(chat_id, track)
                tracks_added += 1
        
        # If nothing is playing, start playback
        if not queue_service.get_current_track(chat_id):
            next_track = queue_service.get_next_track(chat_id)
            await query.edit_message_text(
                f"➕ Added {tracks_added} tracks to queue\n"
                f"🎵 Now playing: {next_track.title} - {next_track.artist}"
            )
        else:
            await query.edit_message_text(f"➕ Added {tracks_added} tracks to queue")
    
    elif action == "spotify_play_list" or action == "spotify_play_album":
        content_id = data[1]
        content_type = "playlist" if action == "spotify_play_list" else "album"
        chat_id = update.effective_chat.id
        
        # Clear current queue
        queue_service.clear_queue(chat_id)
        
        # Get tracks
        if content_type == "playlist":
            tracks = await spotify_service.get_playlist_tracks(f"https://open.spotify.com/playlist/{content_id}")
        else:
            tracks = await spotify_service.get_album_tracks(f"https://open.spotify.com/album/{content_id}")
        
        if not tracks:
            await query.edit_message_text(f"❌ Failed to get tracks from Spotify {content_type}.")
            return
        
        # Add tracks to queue
        for track in tracks:
            queue_service.add_to_queue(chat_id, track)
        
        # Start playback
        next_track = queue_service.get_next_track(chat_id)
        await query.edit_message_text(
            f"📥 Added {len(tracks)} tracks from Spotify {content_type}\n"
            f"🎵 Now playing: {next_track.title} - {next_track.artist}"
        )
    
    elif action == "spotify_queue_list" or action == "spotify_queue_album":
        content_id = data[1]
        content_type = "playlist" if action == "spotify_queue_list" else "album"
        chat_id = update.effective_chat.id
        
        # Get tracks
        if content_type == "playlist":
            tracks = await spotify_service.get_playlist_tracks(f"https://open.spotify.com/playlist/{content_id}")
        else:
            tracks = await spotify_service.get_album_tracks(f"https://open.spotify.com/album/{content_id}")
        
        if not tracks:
            await query.edit_message_text(f"❌ Failed to get tracks from Spotify {content_type}.")
            return
        
        # Add tracks to queue
        for track in tracks:
            queue_service.add_to_queue(chat_id, track)
        
        # If nothing is playing, start playback
        if not queue_service.get_current_track(chat_id):
            next_track = queue_service.get_next_track(chat_id)
            await query.edit_message_text(
                f"📥 Added {len(tracks)} tracks from Spotify {content_type} to queue\n"
                f"🎵 Now playing: {next_track.title} - {next_track.artist}"
            )
        else:
            await query.edit_message_text(f"📥 Added {len(tracks)} tracks from Spotify {content_type} to queue")
    
    elif action == "spotify_shuffle_list" or action == "spotify_shuffle_album":
        content_id = data[1]
        content_type = "playlist" if action == "spotify_shuffle_list" else "album"
        chat_id = update.effective_chat.id
        
        # Clear current queue
        queue_service.clear_queue(chat_id)
        
        # Get tracks
        if content_type == "playlist":
            tracks = await spotify_service.get_playlist_tracks(f"https://open.spotify.com/playlist/{content_id}")
        else:
            tracks = await spotify_service.get_album_tracks(f"https://open.spotify.com/album/{content_id}")
        
        if not tracks:
            await query.edit_message_text(f"❌ Failed to get tracks from Spotify {content_type}.")
            return
        
        # Shuffle the tracks
        import random
        random.shuffle(tracks)
        
        # Add tracks to queue
        for track in tracks:
            queue_service.add_to_queue(chat_id, track)
        
        # Start playback
        next_track = queue_service.get_next_track(chat_id)
        await query.edit_message_text(
            f"📥 Added {len(tracks)} shuffled tracks from Spotify {content_type}\n"
            f"🎵 Now playing: {next_track.title} - {next_track.artist}"
        )

def register_spotify_commands(app, service_instances):
    """Register all Spotify command handlers"""
    ss, qs, ms = service_instances
    init_services(ss, qs, ms)
    
    app.add_handler(CommandHandler("spotify", spotify_search))
    
    # Message handler for Spotify URLs
    app.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r"^https?://(open\.spotify\.com|spotify\.link)"), 
        spotify_url_handler
    ))
    
    # Callback handler for Spotify actions
    app.add_handler(CallbackQueryHandler(
        handle_spotify_callback,
        pattern="^(spotify_play|spotify_add_all|spotify_play_list|spotify_queue_list|spotify_shuffle_list|spotify_play_album|spotify_queue_album|spotify_shuffle_album):"
    ))
    
    logger.info("Spotify commands registered") 