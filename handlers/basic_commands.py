import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from music_commands import music_service 

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('👋 Welcome to MusicMaster Bot! Use /help to see available commands.')

async def help_command(update:Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
    *MusicMaster Bot Commands:*" 
    /start - Start the bot
    /help - Show available commands
    /search [song name] - Search for a song
    /play [song number] - Play a song
    /pause - Pause the current song
    /resume - Resume the current song
    /stop - Stop the current song
    /queue - Show the current queue
    /skip - Skip the current song
    /clear - Clear the queue
    """

    await update.message.reply_text(help_text, parse_mode='Markdown')

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Please provide a search query")
        return
    
    results = await music_service.search_music(query)
    if not results:
        await update.message.reply_text("No results found for your query.")
        return

    response = "Search results:\n"
    for i, track in enumerate(results, 1):
        response += f'{i}. {track["title"]} - {track["artist"]}\n'

    await update.message.reply_text(response)

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Please provide a search query")
        return
    
    result = await music_service.play_music(query)
    if result:
        await update.message.reply_text(f"Now playing: {result['title']} - {result['artist']}")
    else:
        await update.message.reply_text(f'No results found for "{query}"')

async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await music_service.pause_music():
        await update.message.reply_text("Music paused")
    else:
        await update.message.reply_text("No music is playing")

async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await music_service.resume_music():
        await update.message.reply_text("Music resumed")
    else:
        await update.message.reply_text("No music is paused")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await music_service.stop_music():
        await update.message.reply_text("Music stopped")
    else:
        await update.message.reply_text("No music is playing")

async def queue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    queue = await music_service.get_queue()
    if not queue:
        await update.message.reply_text("Queue is empty")
        return

    response = "Current queue:\n"
    for i, track in enumerate(queue, 1):
        response += f'{i}. {track["title"]} - {track["artist"]}\n'

    await update.message.reply_text(response)

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = await music_service.skip_music()
    if result:
        await update.message.reply_text(f'skipped to: {result["title"]} - {result["artist"]}')
    else:
        await update.message.reply_text("Nothing to play next")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await music_service.clear_queue()
    await update.message.reply_text("Queue cleared")

async def volume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        current_vol = await music_service.get_volume()
        await update.message.reply_text(f'Current volume: {current_vol}%')
    else:
        try:
            volume = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Volume must be an integer")
            return

        await music_service.set_volume(volume)
        await update.message.reply_text(f'Volume set to {volume}%')

async def previous(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = await music_service.previous_music()
    if result:
        await update.message.reply_text(f'Playing previous: {result["title"]} - {result["artist"]}')
    else:
        await update.message.reply_text("Nothing to play previous")

async def current(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = await music_service.current_music()
    if result:
        await update.message.reply_text(f'Now playing: {result["title"]} - {result["artist"]}')
    else:
        await update.message.reply_text("No music is playing")


def register_basic_commands(app):
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('search', search))
    app.add_handler(CommandHandler('play', play))
    app.add_handler(CommandHandler('pause', pause))
    app.add_handler(CommandHandler('resume', resume))
    app.add_handler(CommandHandler('stop', stop))
    app.add_handler(CommandHandler('queue', queue))
    app.add_handler(CommandHandler('skip', skip))
    app.add_handler(CommandHandler('clear', clear))
    app.add_handler(CommandHandler('volume', volume))
    app.add_handler(CommandHandler('previous', previous))
    app.add_handler(CommandHandler('current', current))

    logger.info("Basic commands registered")

    