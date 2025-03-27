import logging
import os
import asyncio
import tempfile
from typing import Optional, Tuple
import aiohttp
from pydub import AudioSegment
import uuid

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self, downloads_path: str = "./downloads"):
        """Initialize the voice service"""
        self.downloads_path = downloads_path
        
        # Create the downloads directory if it doesn't exist
        if not os.path.exists(downloads_path):
            os.makedirs(downloads_path)
    
    async def text_to_speech(self, text: str, lang: str = "en") -> Optional[str]:
        """
        Convert text to speech and return the file path
        
        Simple implementation using Google Translate TTS (for demo purposes only)
        In production, use a proper TTS API like Google Cloud TTS, Amazon Polly, etc.
        """
        if not text:
            return None
        
        # Limit text length to prevent abuse
        if len(text) > 200:
            text = text[:200]
        
        # Generate a unique filename
        filename = f"tts_{uuid.uuid4()}.mp3"
        file_path = os.path.join(self.downloads_path, filename)
        
        try:
            # Google Translate TTS endpoint (not official API)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={lang}&q={text}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching TTS: {response.status}")
                        return None
                    
                    data = await response.read()
                    
                    # Save the audio file
                    with open(file_path, "wb") as f:
                        f.write(data)
                    
                    return file_path
        
        except Exception as e:
            logger.error(f"Error generating TTS: {str(e)}")
            return None
    
    async def extract_audio(self, video_path: str) -> Optional[str]:
        """Extract audio from a video file"""
        if not os.path.exists(video_path):
            logger.error(f"Video file does not exist: {video_path}")
            return None
        
        try:
            # Generate output filename
            filename = os.path.basename(video_path)
            base_name = os.path.splitext(filename)[0]
            output_path = os.path.join(self.downloads_path, f"{base_name}.mp3")
            
            # Use ffmpeg to extract audio
            cmd = f"ffmpeg -i \"{video_path}\" -q:a 0 -map a \"{output_path}\" -y"
            
            # Run the command
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Error extracting audio: {stderr.decode()}")
                return None
            
            return output_path
        
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            return None
    
    async def speed_change(self, audio_path: str, speed: float = 1.0) -> Optional[str]:
        """Change the speed of an audio file"""
        if not os.path.exists(audio_path):
            logger.error(f"Audio file does not exist: {audio_path}")
            return None
        
        if speed <= 0 or speed > 3.0:
            logger.error(f"Invalid speed value: {speed}")
            return None
        
        try:
            # Load the audio file
            sound = AudioSegment.from_file(audio_path)
            
            # Generate output filename
            filename = os.path.basename(audio_path)
            base_name, ext = os.path.splitext(filename)
            output_path = os.path.join(self.downloads_path, f"{base_name}_speed{speed}{ext}")
            
            # Change the speed
            sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
                "frame_rate": int(sound.frame_rate * speed)
            })
            
            # Export the audio file
            sound_with_altered_frame_rate.export(output_path, format=ext.strip('.'))
            
            return output_path
        
        except Exception as e:
            logger.error(f"Error changing audio speed: {str(e)}")
            return None
    
    async def convert_audio_format(self, audio_path: str, format: str = "mp3") -> Optional[str]:
        """Convert an audio file to a different format"""
        if not os.path.exists(audio_path):
            logger.error(f"Audio file does not exist: {audio_path}")
            return None
        
        if format not in ["mp3", "ogg", "wav", "m4a"]:
            logger.error(f"Unsupported audio format: {format}")
            return None
        
        try:
            # Generate output filename
            filename = os.path.basename(audio_path)
            base_name = os.path.splitext(filename)[0]
            output_path = os.path.join(self.downloads_path, f"{base_name}.{format}")
            
            # Use ffmpeg to convert the audio
            cmd = f"ffmpeg -i \"{audio_path}\" \"{output_path}\" -y"
            
            # Run the command
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Error converting audio format: {stderr.decode()}")
                return None
            
            return output_path
        
        except Exception as e:
            logger.error(f"Error converting audio format: {str(e)}")
            return None
    
    async def merge_audio_files(self, audio_paths: list, output_name: str = "merged") -> Optional[str]:
        """Merge multiple audio files into one"""
        if not audio_paths:
            logger.error("No audio files provided")
            return None
        
        try:
            # Check if all files exist
            for path in audio_paths:
                if not os.path.exists(path):
                    logger.error(f"Audio file does not exist: {path}")
                    return None
            
            # Create a temporary file for the file list
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                for path in audio_paths:
                    f.write(f"file '{os.path.abspath(path)}'\n")
                temp_file = f.name
            
            # Generate output filename
            output_path = os.path.join(self.downloads_path, f"{output_name}.mp3")
            
            # Use ffmpeg to merge the files
            cmd = f"ffmpeg -f concat -safe 0 -i \"{temp_file}\" -c copy \"{output_path}\" -y"
            
            # Run the command
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Remove the temporary file
            os.unlink(temp_file)
            
            if process.returncode != 0:
                logger.error(f"Error merging audio files: {stderr.decode()}")
                return None
            
            return output_path
        
        except Exception as e:
            logger.error(f"Error merging audio files: {str(e)}")
            return None
