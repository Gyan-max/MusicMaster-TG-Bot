from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from services.music_service import MusicService
import os
import logging

logger = logging.getLogger(__name__)

music_service = MusicService()

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Please provide a search query")
        return
    
    respsonse = "search results:\n"
    for i, track in enumerate(results, 1):
        respsonse += f'{i}. {track["title"]} - {track["artist"]}\n'

        await update.message.reply_text(respsonse)

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

async def skip (update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = await music_service.skip_music()
    if result:
        await update.message.reply_text(f'skipped to: {result["title"]} - {result["artist"]}')
    else:
        await update.message.reply_text("Nothing to play next")

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

async def volume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        current_vol = await music_service.get_volume()
        await update.message.reply_text(f'Current volume: {current_vol}%')
        return
    try:
        level = int(context.args[0])
        if 0 <= level <= 100:
            await music_service.set_volume(level)
            await update.message.reply_text(f'Volume set to: {level}%')
        else:
            await update.message.reply_text("Volume level must be between 0 and 100")
    except ValueError:
        await update.message.reply_text("Please provide a valid volume number")

async def queue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tracks = await music_service.get_queue()
    if not tracks:
        await update.message.reply_text("Queue is empty")
        return
    
    response = "Current queue:\n"
    for i, track in enumerate(tracks, 1):
        response += f'{i}. {track["title"]} - {track["artist"]}\n'

    await update.message.reply_text(response)

def register_handlers(app):
    """Register all music command handlers"""
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("pause", pause))
    app.add_handler(CommandHandler("resume", resume))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("skip", skip))
    app.add_handler(CommandHandler("previous", previous))
    app.add_handler(CommandHandler("current", current))
    app.add_handler(CommandHandler("volume", volume))
    app.add_handler(CommandHandler("queue", queue))

    logger.info("Music commands registered")