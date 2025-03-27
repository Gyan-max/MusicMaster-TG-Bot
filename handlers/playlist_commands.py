import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler
from typing import List, Dict

from services.playlist_service import PlaylistService
from services.music_service import MusicService
from services.queue_service import QueueService
from services.user_service import UserService
from models.track import Track

logger = logging.getLogger(__name__)

# Initialize services
playlist_service = None
music_service = None
queue_service = None
user_service = None

def init_services(ps, ms, qs, us):
    global playlist_service, music_service, queue_service, user_service
    playlist_service = ps
    music_service = ms
    queue_service = qs
    user_service = us

async def create_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a new playlist"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Please provide a name for your playlist.\nUsage: /createplaylist [name] [description (optional)]")
        return
    
    name = context.args[0]
    description = " ".join(context.args[1:]) if len(context.args) > 1 else None
    user_id = update.effective_user.id
    
    playlist = playlist_service.create_playlist(name, user_id, description)
    
    await update.message.reply_text(f"Playlist '{playlist.name}' created successfully!")

async def my_playlists(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all playlists for the current user"""
    user_id = update.effective_user.id
    playlists = playlist_service.get_user_playlists(user_id)
    
    if not playlists:
        await update.message.reply_text("You don't have any playlists yet.\nUse /createplaylist to create one.")
        return
    
    response = "Your playlists:\n\n"
    keyboard = []
    
    for i, playlist in enumerate(playlists, 1):
        response += f"{i}. {playlist.name}"
        if playlist.description:
            response += f" - {playlist.description}"
        response += f" ({len(playlist.tracks)} tracks)\n"
        
        # Add buttons for view and play
        keyboard.append([
            InlineKeyboardButton(f"View {playlist.name}", callback_data=f"view_playlist:{playlist.id}"),
            InlineKeyboardButton(f"Play {playlist.name}", callback_data=f"play_playlist:{playlist.id}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, reply_markup=reply_markup)

async def add_to_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add the currently playing or last played track to a playlist"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Get the current track
    current_track = queue_service.get_current_track(chat_id)
    if not current_track:
        await update.message.reply_text("No track is currently playing. Play a track first!")
        return
    
    # Get user's playlists
    playlists = playlist_service.get_user_playlists(user_id)
    if not playlists:
        await update.message.reply_text("You don't have any playlists yet.\nUse /createplaylist to create one.")
        return
    
    # Create a keyboard with playlist options
    keyboard = []
    for playlist in playlists:
        keyboard.append([InlineKeyboardButton(
            playlist.name, callback_data=f"add_to_playlist:{playlist.id}:{current_track.id}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Select a playlist to add '{current_track.title}' to:",
        reply_markup=reply_markup
    )

async def view_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View a specific playlist"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Please provide a playlist name or number.\nUsage: /viewplaylist [name/number]")
        return
    
    user_id = update.effective_user.id
    query = " ".join(context.args)
    
    # Get all user playlists
    playlists = playlist_service.get_user_playlists(user_id)
    if not playlists:
        await update.message.reply_text("You don't have any playlists yet.")
        return
    
    # Try to find the playlist by name or index
    playlist = None
    try:
        # Check if it's a number (index)
        index = int(query) - 1
        if 0 <= index < len(playlists):
            playlist = playlists[index]
    except ValueError:
        # Search by name
        for p in playlists:
            if query.lower() in p.name.lower():
                playlist = p
                break
    
    if not playlist:
        await update.message.reply_text(f"Playlist '{query}' not found.")
        return
    
    # Display the playlist
    response = f"🎵 Playlist: {playlist.name}\n"
    if playlist.description:
        response += f"📝 Description: {playlist.description}\n"
    response += f"🔢 Total tracks: {len(playlist.tracks)}\n\n"
    
    tracks = []
    for track_id in playlist.tracks:
        track = await music_service.get_track_info(track_id)
        if track:
            tracks.append(track)
    
    if not tracks:
        response += "This playlist is empty."
        await update.message.reply_text(response)
        return
    
    # List tracks
    for i, track in enumerate(tracks, 1):
        response += f"{i}. {track.title} - {track.artist}\n"
        if i >= 20:  # Limit to 20 tracks to avoid message too long
            response += f"\n...and {len(tracks) - 20} more tracks."
            break
    
    # Create keyboard for actions
    keyboard = [
        [
            InlineKeyboardButton("Play Playlist", callback_data=f"play_playlist:{playlist.id}"),
            InlineKeyboardButton("Shuffle Play", callback_data=f"shuffle_playlist:{playlist.id}")
        ],
        [
            InlineKeyboardButton("Add to Queue", callback_data=f"queue_playlist:{playlist.id}"),
            InlineKeyboardButton("Delete Playlist", callback_data=f"delete_playlist:{playlist.id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, reply_markup=reply_markup)

async def play_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Play a playlist"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Please provide a playlist name or number.\nUsage: /playplaylist [name/number]")
        return
    
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    query = " ".join(context.args)
    
    # Get all user playlists
    playlists = playlist_service.get_user_playlists(user_id)
    if not playlists:
        await update.message.reply_text("You don't have any playlists yet.")
        return
    
    # Try to find the playlist by name or index
    playlist = None
    try:
        # Check if it's a number (index)
        index = int(query) - 1
        if 0 <= index < len(playlists):
            playlist = playlists[index]
    except ValueError:
        # Search by name
        for p in playlists:
            if query.lower() in p.name.lower():
                playlist = p
                break
    
    if not playlist:
        await update.message.reply_text(f"Playlist '{query}' not found.")
        return
    
    if not playlist.tracks:
        await update.message.reply_text(f"Playlist '{playlist.name}' is empty.")
        return
    
    # Clear current queue
    queue_service.clear_queue(chat_id)
    
    # Fetch all tracks and add to queue
    tracks_added = 0
    for track_id in playlist.tracks:
        track = await music_service.get_track_info(track_id)
        if track:
            queue_service.add_to_queue(chat_id, track)
            tracks_added += 1
    
    # Start playing
    next_track = queue_service.get_next_track(chat_id)
    
    await update.message.reply_text(
        f"Added {tracks_added} tracks from playlist '{playlist.name}' to the queue.\n"
        f"Now playing: {next_track.title} - {next_track.artist}"
    )

async def handle_playlist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle playlist-related callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")
    action = data[0]
    
    if action == "view_playlist":
        playlist_id = data[1]
        playlist = playlist_service.get_playlist(playlist_id)
        
        if not playlist:
            await query.edit_message_text("Playlist not found or was deleted.")
            return
        
        # Display the playlist
        response = f"🎵 Playlist: {playlist.name}\n"
        if playlist.description:
            response += f"📝 Description: {playlist.description}\n"
        response += f"🔢 Total tracks: {len(playlist.tracks)}\n\n"
        
        tracks = []
        for track_id in playlist.tracks[:20]:  # Limit to 20 to avoid message too long
            track = await music_service.get_track_info(track_id)
            if track:
                tracks.append(track)
        
        if not tracks:
            response += "This playlist is empty."
            await query.edit_message_text(response)
            return
        
        # List tracks
        for i, track in enumerate(tracks, 1):
            response += f"{i}. {track.title} - {track.artist}\n"
        
        if len(playlist.tracks) > 20:
            response += f"\n...and {len(playlist.tracks) - 20} more tracks."
        
        # Create keyboard for actions
        keyboard = [
            [
                InlineKeyboardButton("Play Playlist", callback_data=f"play_playlist:{playlist.id}"),
                InlineKeyboardButton("Shuffle Play", callback_data=f"shuffle_playlist:{playlist.id}")
            ],
            [
                InlineKeyboardButton("Add to Queue", callback_data=f"queue_playlist:{playlist.id}"),
                InlineKeyboardButton("Delete Playlist", callback_data=f"delete_playlist:{playlist.id}")
            ],
            [
                InlineKeyboardButton("Back to Playlists", callback_data="back_to_playlists")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(response, reply_markup=reply_markup)
    
    elif action == "play_playlist":
        playlist_id = data[1]
        playlist = playlist_service.get_playlist(playlist_id)
        chat_id = update.effective_chat.id
        
        if not playlist:
            await query.edit_message_text("Playlist not found or was deleted.")
            return
        
        if not playlist.tracks:
            await query.edit_message_text(f"Playlist '{playlist.name}' is empty.")
            return
        
        # Clear current queue
        queue_service.clear_queue(chat_id)
        
        # Fetch all tracks and add to queue
        tracks_added = 0
        for track_id in playlist.tracks:
            track = await music_service.get_track_info(track_id)
            if track:
                queue_service.add_to_queue(chat_id, track)
                tracks_added += 1
        
        # Start playing
        next_track = queue_service.get_next_track(chat_id)
        
        await query.edit_message_text(
            f"Added {tracks_added} tracks from playlist '{playlist.name}' to the queue.\n"
            f"Now playing: {next_track.title} - {next_track.artist}"
        )
    
    elif action == "shuffle_playlist":
        playlist_id = data[1]
        playlist = playlist_service.get_playlist(playlist_id)
        chat_id = update.effective_chat.id
        
        if not playlist:
            await query.edit_message_text("Playlist not found or was deleted.")
            return
        
        if not playlist.tracks:
            await query.edit_message_text(f"Playlist '{playlist.name}' is empty.")
            return
        
        # Clear current queue
        queue_service.clear_queue(chat_id)
        
        # Fetch all tracks and add to queue
        tracks_added = 0
        
        # Convert track_ids to tracks
        tracks_to_add = []
        for track_id in playlist.tracks:
            track = await music_service.get_track_info(track_id)
            if track:
                tracks_to_add.append(track)
                tracks_added += 1
        
        # Shuffle tracks
        import random
        random.shuffle(tracks_to_add)
        
        # Add to queue
        for track in tracks_to_add:
            queue_service.add_to_queue(chat_id, track)
        
        # Start playing
        next_track = queue_service.get_next_track(chat_id)
        
        await query.edit_message_text(
            f"Added {tracks_added} tracks from playlist '{playlist.name}' to the queue (shuffled).\n"
            f"Now playing: {next_track.title} - {next_track.artist}"
        )
    
    elif action == "queue_playlist":
        playlist_id = data[1]
        playlist = playlist_service.get_playlist(playlist_id)
        chat_id = update.effective_chat.id
        
        if not playlist:
            await query.edit_message_text("Playlist not found or was deleted.")
            return
        
        if not playlist.tracks:
            await query.edit_message_text(f"Playlist '{playlist.name}' is empty.")
            return
        
        # Fetch all tracks and add to queue
        tracks_added = 0
        for track_id in playlist.tracks:
            track = await music_service.get_track_info(track_id)
            if track:
                queue_service.add_to_queue(chat_id, track)
                tracks_added += 1
        
        await query.edit_message_text(
            f"Added {tracks_added} tracks from playlist '{playlist.name}' to the queue."
        )
    
    elif action == "delete_playlist":
        playlist_id = data[1]
        playlist = playlist_service.get_playlist(playlist_id)
        
        if not playlist:
            await query.edit_message_text("Playlist not found or was already deleted.")
            return
        
        # Create confirmation keyboard
        keyboard = [
            [
                InlineKeyboardButton("Yes, delete", callback_data=f"confirm_delete:{playlist_id}"),
                InlineKeyboardButton("No, keep it", callback_data=f"view_playlist:{playlist_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Are you sure you want to delete playlist '{playlist.name}'?",
            reply_markup=reply_markup
        )
    
    elif action == "confirm_delete":
        playlist_id = data[1]
        playlist_name = playlist_service.get_playlist(playlist_id).name if playlist_service.get_playlist(playlist_id) else "Unknown"
        
        # Delete the playlist
        success = playlist_service.delete_playlist(playlist_id)
        
        if success:
            await query.edit_message_text(f"Playlist '{playlist_name}' has been deleted.")
        else:
            await query.edit_message_text(f"Failed to delete playlist '{playlist_name}'.")
    
    elif action == "add_to_playlist":
        playlist_id = data[1]
        track_id = data[2]
        
        playlist = playlist_service.get_playlist(playlist_id)
        if not playlist:
            await query.edit_message_text("Playlist not found or was deleted.")
            return
        
        # Try to get track info
        track = await music_service.get_track_info(track_id)
        if not track:
            await query.edit_message_text("Track information could not be retrieved.")
            return
        
        # Add the track to the playlist
        success = playlist_service.add_track_to_playlist(playlist_id, track_id)
        
        if success:
            await query.edit_message_text(f"Added '{track.title}' to playlist '{playlist.name}'.")
        else:
            await query.edit_message_text(f"Failed to add track to playlist '{playlist.name}'.")
    
    elif action == "back_to_playlists":
        # Show user's playlists
        user_id = update.effective_user.id
        playlists = playlist_service.get_user_playlists(user_id)
        
        if not playlists:
            await query.edit_message_text("You don't have any playlists yet.\nUse /createplaylist to create one.")
            return
        
        response = "Your playlists:\n\n"
        keyboard = []
        
        for i, playlist in enumerate(playlists, 1):
            response += f"{i}. {playlist.name}"
            if playlist.description:
                response += f" - {playlist.description}"
            response += f" ({len(playlist.tracks)} tracks)\n"
            
            # Add buttons for view and play
            keyboard.append([
                InlineKeyboardButton(f"View {playlist.name}", callback_data=f"view_playlist:{playlist.id}"),
                InlineKeyboardButton(f"Play {playlist.name}", callback_data=f"play_playlist:{playlist.id}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(response, reply_markup=reply_markup)

async def search_playlists(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for public playlists by name"""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Please provide a search query.\nUsage: /searchplaylists [query]")
        return
    
    query = " ".join(context.args)
    playlists = playlist_service.search_playlists(query)
    
    if not playlists:
        await update.message.reply_text(f"No public playlists found matching '{query}'.")
        return
    
    response = f"Public playlists matching '{query}':\n\n"
    keyboard = []
    
    for i, playlist in enumerate(playlists, 1):
        response += f"{i}. {playlist.name}"
        if playlist.description:
            response += f" - {playlist.description}"
        response += f" ({len(playlist.tracks)} tracks)\n"
        
        # Add buttons for view and play
        keyboard.append([
            InlineKeyboardButton(f"View {playlist.name}", callback_data=f"view_playlist:{playlist.id}"),
            InlineKeyboardButton(f"Play {playlist.name}", callback_data=f"play_playlist:{playlist.id}")
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, reply_markup=reply_markup)

def register_playlist_commands(app, service_instances):
    """Register all playlist command handlers"""
    ps, ms, qs, us = service_instances
    init_services(ps, ms, qs, us)
    
    app.add_handler(CommandHandler("createplaylist", create_playlist))
    app.add_handler(CommandHandler("myplaylists", my_playlists))
    app.add_handler(CommandHandler("playlists", my_playlists))  # Alias
    app.add_handler(CommandHandler("addtoplaylist", add_to_playlist))
    app.add_handler(CommandHandler("viewplaylist", view_playlist))
    app.add_handler(CommandHandler("playplaylist", play_playlist))
    app.add_handler(CommandHandler("searchplaylists", search_playlists))
    
    # Add callback handler for playlist actions
    app.add_handler(CallbackQueryHandler(
        handle_playlist_callback, 
        pattern="^(view_playlist|play_playlist|shuffle_playlist|queue_playlist|delete_playlist|confirm_delete|add_to_playlist|back_to_playlists):"
    ))
    
    logger.info("Playlist commands registered") 