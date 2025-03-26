from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('👋 Welcome to MusicMaster Bot! Use /help to see available commands.')

async def help_command(update:Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
    *MusicMaster Bot Commands:*" 
    /start - Start the bot
    /help - Show available commands
    /help - show available commands
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

def register_basic_commands(app):
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    