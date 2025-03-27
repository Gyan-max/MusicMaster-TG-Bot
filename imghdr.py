"""
Minimal imghdr replacement module.
Python 3.13 removed the imghdr module, but python-telegram-bot 13.15 still depends on it.
"""

def what(file, h=None):
    """
    Simplified version of imghdr.what() - returns file type based on content.
    """
    if h is None:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                h = f.read(32)
        else:
            location = file.tell()
            h = file.read(32)
            file.seek(location)
            
    # Check for JPEG
    if h[0:2] == b'\xff\xd8':
        return 'jpeg'
    
    # Check for PNG
    if h[0:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    
    # Check for GIF
    if h[0:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    
    # Check for BMP
    if h[0:2] == b'BM':
        return 'bmp'
    
    # Check for WebP
    if h[0:4] == b'RIFF' and h[8:12] == b'WEBP':
        return 'webp'
    
    return None

tests = [] 