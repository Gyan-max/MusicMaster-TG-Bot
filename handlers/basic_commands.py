import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler
import asyncio

logger = logging.getLogger(__name__)

# Initialize service
music_service = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('👋 Welcome to MusicMaster Bot! Use /help to see available commands.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
    *MusicMaster Bot Commands:*" 
    /start - Start the bot
    /help - Show available commands
    /search [song name] - Search for a song
    /play [song name] - Find and play a song online
    /queue - Show the current queue
    /skip - Skip to the next song
    /clear - Clear the queue
    """

    await update.message.reply_text(help_text, parse_mode='Markdown')

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
        keyboard.append([InlineKeyboardButton(f"Play: {track.title[:30]}...", callback_data=f"basic_play_{track.id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, reply_markup=reply_markup)

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
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

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    chat_id = update.effective_chat.id
    
    if data.startswith("basic_play_"):
        # Extract track ID from callback data
        track_id = data.replace("basic_play_", "")
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
    
    elif data.startswith("basic_queue_"):
        # Extract track ID from callback data
        track_id = data.replace("basic_queue_", "")
        track = await music_service.get_track_info(track_id)
        
        if track:
            # Add to queue
            await music_service.add_to_queue(track)
            await query.edit_message_reply_markup(None)
            await context.bot.send_message(chat_id, f"Added to queue: {track.title} - {track.artist}")
        else:
            await context.bot.send_message(chat_id, "Sorry, could not find track information.")

async def queue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    queue = await music_service.get_queue()
    if not queue:
        await update.message.reply_text("Queue is empty")
        return

    # Create keyboard with play buttons for each track in queue
    keyboard = []
    response = "Current queue:\n"
    for i, track in enumerate(queue, 1):
        response += f'{i}. {track.title} - {track.artist}\n'
        keyboard.append([InlineKeyboardButton(f"Play: {track.title[:30]}...", url=track.url)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, reply_markup=reply_markup)

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    
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

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await music_service.clear_queue()
    await update.message.reply_text("Queue cleared")

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

def register_basic_commands(app, service_instances):
    """Register all basic command handlers"""
    ms, qs, us, ls = service_instances
    global music_service
    music_service = ms
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('search', search))
    app.add_handler(CommandHandler('play', play))
    app.add_handler(CommandHandler('queue', queue))
    app.add_handler(CommandHandler('skip', skip))
    app.add_handler(CommandHandler('clear', clear))
    app.add_handler(CommandHandler('current', current))
    app.add_handler(CallbackQueryHandler(handle_callback, pattern="^basic_"))

    logger.info("Basic commands registered")

    