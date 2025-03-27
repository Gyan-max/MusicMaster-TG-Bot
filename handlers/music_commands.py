import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler
from services.music_service import MusicService
import os

logger = logging.getLogger(__name__)

# Initialize service
music_service = None

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Please provide a search query")
        return
    
    results = await music_service.search(query)
    if not results:
        await update.message.reply_text("No results found for your query.")
        return

    # Create keyboard with play buttons for each result
    keyboard = []
    response = "Search results:\n"
    for i, track in enumerate(results, 1):
        response += f'{i}. {track.title} - {track.artist}\n'
        keyboard.append([InlineKeyboardButton(f"Play: {track.title[:30]}...", callback_data=f"music_play_{track.id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, reply_markup=reply_markup)

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Please provide a search query")
        return
    
    # Search and add to queue
    await update.message.reply_text(f"Searching for: {query}")
    result = await music_service.play_music(query)
    
    if not result:
        await update.message.reply_text(f'No results found for "{query}"')
        return
    
    # Download the track
    file_path = await music_service.download(result)
    if not file_path:
        await update.message.reply_text("Sorry, couldn't download the track.")
        return
    
    # Send the audio file as voice message
    try:
        await update.message.reply_voice(
            voice=open(file_path, 'rb'),
            caption=f"🎵 *{result.title}*\n👤 {result.artist}",
            parse_mode='Markdown'
        )
        await update.message.reply_text(f"Now playing: {result.title} - {result.artist}")
    except Exception as e:
        logger.error(f"Error sending voice message: {str(e)}")
        await update.message.reply_text("Sorry, there was an error sending the voice message.")

async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await music_service.pause_music():
        await update.message.reply_text("Music paused (queue management only)")
    else:
        await update.message.reply_text("No music is playing")

async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await music_service.resume_music():
        await update.message.reply_text("Music resumed (queue management only)")
    else:
        await update.message.reply_text("No music is paused")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await music_service.stop_music():
        await update.message.reply_text("Music stopped (queue management only)")
    else:
        await update.message.reply_text("No music is playing")

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = await music_service.skip_music()
    if result:
        # Create inline keyboard with YouTube link
        keyboard = [
            [InlineKeyboardButton("▶️ Play on YouTube", url=result.url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send track info with link to play online
        await update.message.reply_photo(
            photo=result.thumbnail if result.thumbnail else "https://i.imgur.com/QLQgRUh.png",
            caption=f"🎵 *{result.title}*\n👤 {result.artist}\n\nSkipped to next track. Click the button below to play on YouTube.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Nothing to play next")

async def previous(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = await music_service.previous_music()
    if result:
        # Create inline keyboard with YouTube link
        keyboard = [
            [InlineKeyboardButton("▶️ Play on YouTube", url=result.url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send track info with link to play online
        await update.message.reply_photo(
            photo=result.thumbnail if result.thumbnail else "https://i.imgur.com/QLQgRUh.png",
            caption=f"🎵 *{result.title}*\n👤 {result.artist}\n\nPlaying previous track. Click the button below to play on YouTube.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Nothing to play previous")

async def current(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = await music_service.current_music()
    if result:
        # Create inline keyboard with YouTube link
        keyboard = [
            [InlineKeyboardButton("▶️ Play on YouTube", url=result.url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send track info with link to play online
        await update.message.reply_photo(
            photo=result.thumbnail if result.thumbnail else "https://i.imgur.com/QLQgRUh.png",
            caption=f"🎵 *Currently Playing*\n*{result.title}*\n👤 {result.artist}\n\nClick the button below to play on YouTube.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("No music is playing")

async def queue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tracks = await music_service.get_queue()
    if not tracks:
        await update.message.reply_text("Queue is empty")
        return
    
    # Create keyboard with play buttons for each track in queue
    keyboard = []
    response = "Current queue:\n"
    for i, track in enumerate(tracks, 1):
        response += f'{i}. {track.title} - {track.artist}\n'
        keyboard.append([InlineKeyboardButton(f"Play: {track.title[:30]}...", url=track.url)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, reply_markup=reply_markup)

async def handle_music_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from music commands"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    chat_id = update.effective_chat.id
    
    if data.startswith("music_play_"):
        # Extract track ID from callback data
        track_id = data.replace("music_play_", "")
        track = await music_service.get_track_info(track_id)
        
        if track:
            # Download the track
            file_path = await music_service.download(track)
            if not file_path:
                await query.edit_message_text("Sorry, couldn't download the track.")
                return
            
            # Send the audio file as voice message
            try:
                await context.bot.send_voice(
                    chat_id=chat_id,
                    voice=open(file_path, 'rb'),
                    caption=f"🎵 *{track.title}*\n👤 {track.artist}",
                    parse_mode='Markdown'
                )
                await query.edit_message_text(f"Now playing: {track.title} - {track.artist}")
            except Exception as e:
                logger.error(f"Error sending voice message: {str(e)}")
                await query.edit_message_text("Sorry, there was an error sending the voice message.")
        else:
            await query.edit_message_text("Sorry, could not find track information.")
    
    elif data.startswith("music_queue_"):
        # Extract track ID from callback data
        track_id = data.replace("music_queue_", "")
        track = await music_service.get_track_info(track_id)
        
        if track:
            # Add to queue
            await music_service.add_to_queue(track)
            await query.edit_message_reply_markup(None)
            await context.bot.send_message(chat_id, f"Added to queue: {track.title} - {track.artist}")
        else:
            await context.bot.send_message(chat_id, "Sorry, could not find track information.")

def register_music_commands(app, service_instances=None):
    """Register all music command handlers with the application"""
    global music_service
    
    if service_instances:
        ms, qs, us = service_instances
        music_service = ms
    
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("pause", pause))
    app.add_handler(CommandHandler("resume", resume))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("skip", skip))
    app.add_handler(CommandHandler("previous", previous))
    app.add_handler(CommandHandler("current", current))
    app.add_handler(CommandHandler("queue", queue))
    app.add_handler(CallbackQueryHandler(handle_music_callback, pattern="^music_"))
    
    logger.info("Music commands registered")