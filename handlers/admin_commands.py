import logging
import os
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from typing import List
import time

from services.music_service import MusicService
from services.user_service import UserService

logger = logging.getLogger(__name__)

# Initialize services
music_service = None
user_service = None

# List of admin user IDs
ADMIN_IDS = []  # Add admin Telegram IDs here

def init_services(ms, us):
    global music_service, user_service, ADMIN_IDS
    music_service = ms
    user_service = us
    
    # Try to get admin IDs from environment
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    if admin_ids_str:
        try:
            ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",")]
        except ValueError:
            logger.error("Invalid ADMIN_IDS in environment. Format should be comma-separated integers.")

def is_admin(user_id: int) -> bool:
    """Check if the user is an admin"""
    return user_id in ADMIN_IDS

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get bot usage statistics"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("This command is only available to admins.")
        return
    
    try:
        # Get all users
        users = user_service.get_all_users()
        
        # Calculate statistics
        total_users = len(users)
        active_users_24h = 0
        active_users_7d = 0
        
        now = time.time()
        for user in users:
            last_active_timestamp = user.last_active.timestamp() if hasattr(user, "last_active") else 0
            
            if now - last_active_timestamp < 24 * 60 * 60:  # 24 hours
                active_users_24h += 1
            
            if now - last_active_timestamp < 7 * 24 * 60 * 60:  # 7 days
                active_users_7d += 1
        
        # Format response
        response = (
            "📊 Bot Statistics:\n\n"
            f"👥 Total Users: {total_users}\n"
            f"👤 Active Users (24h): {active_users_24h}\n"
            f"👥 Active Users (7d): {active_users_7d}\n"
        )
        
        # Add download directory size
        download_path = music_service.download_path
        total_size = 0
        file_count = 0
        
        for dirpath, dirnames, filenames in os.walk(download_path):
            for f in filenames:
                if f.endswith(('.mp3', '.ogg', '.m4a')):
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
                    file_count += 1
        
        # Format size
        if total_size < 1024:
            size_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.2f} KB"
        elif total_size < 1024 * 1024 * 1024:
            size_str = f"{total_size / (1024 * 1024):.2f} MB"
        else:
            size_str = f"{total_size / (1024 * 1024 * 1024):.2f} GB"
        
        response += f"\n💾 Downloads: {file_count} files ({size_str})"
        
        await update.message.reply_text(response)
    
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        await update.message.reply_text(f"Error getting statistics: {str(e)}")

async def cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clean up old downloaded files"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("This command is only available to admins.")
        return
    
    try:
        days = 7  # Default to 7 days
        
        if context.args and len(context.args) > 0:
            try:
                days = int(context.args[0])
                if days < 1:
                    await update.message.reply_text("Days parameter must be at least 1.")
                    return
            except ValueError:
                await update.message.reply_text("Invalid days parameter. Must be a number.")
                return
        
        await update.message.reply_text(f"🧹 Cleaning up files older than {days} days...")
        
        # Run cleanup
        count = music_service.cleanup_downloads(days)
        
        await update.message.reply_text(f"✅ Cleanup complete. Removed {count} old files.")
    
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        await update.message.reply_text(f"Error during cleanup: {str(e)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message to all users"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("This command is only available to admins.")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text("Please provide a message.\nUsage: /broadcast [message]")
        return
    
    message = " ".join(context.args)
    
    try:
        users = user_service.get_all_users()
        
        await update.message.reply_text(f"📣 Broadcasting message to {len(users)} users...")
        
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user.id,
                    text=f"📢 *Announcement from MasterMusic*\n\n{message}",
                    parse_mode="Markdown"
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Error sending broadcast to {user.id}: {str(e)}")
                error_count += 1
        
        await update.message.reply_text(
            f"✅ Broadcast complete\n"
            f"✓ Sent: {success_count}\n"
            f"✗ Failed: {error_count}"
        )
    
    except Exception as e:
        logger.error(f"Error during broadcast: {str(e)}")
        await update.message.reply_text(f"Error during broadcast: {str(e)}")

def register_admin_commands(app, service_instances):
    """Register all admin command handlers"""
    ms, us = service_instances
    init_services(ms, us)
    
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("cleanup", cleanup))
    app.add_handler(CommandHandler("broadcast", broadcast))
    
    logger.info("Admin commands registered")