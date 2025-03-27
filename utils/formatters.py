import re
from typing import Union, Optional


def format_duration(seconds: Union[int, float]) -> str:
    """
    Format seconds into a human-readable time format (HH:MM:SS or MM:SS)
    """
    if not seconds or seconds < 0:
        return "00:00"
    
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def format_filesize(bytes: Union[int, float]) -> str:
    """
    Format bytes into a human-readable file size
    """
    if not bytes or bytes < 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


def escape_markdown(text: str) -> str:
    """
    Escape Markdown special characters in a string
    """
    if not text:
        return ""
    
    # Characters to escape: _ * [ ] ( ) ~ ` > # + - = | { } . !
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def format_message(message: str, markdown: bool = True) -> str:
    """
    Format a message for Telegram, with optional Markdown escaping
    """
    if not message:
        return ""
    
    # Trim to Telegram's message limit (4096 chars)
    if len(message) > 4096:
        message = message[:4093] + "..."
    
    if markdown:
        message = escape_markdown(message)
    
    return message


def truncate_text(text: str, max_length: int = 100, add_ellipsis: bool = True) -> str:
    """
    Truncate text to a maximum length, optionally adding an ellipsis
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    if add_ellipsis:
        truncated += "..."
    
    return truncated


def clean_filename(filename: str) -> str:
    """
    Clean a filename to make it safe for saving files
    """
    if not filename:
        return "unnamed"
    
    # Remove invalid characters for filenames
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    
    # Replace multiple spaces with a single space
    filename = re.sub(r'\s+', " ", filename).strip()
    
    # Ensure the filename is not too long
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename or "unnamed"
