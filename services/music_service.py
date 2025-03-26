from pytube import Search
import yt_dlp
import os

class MusicService:
    def __init__(self, download_path="./downloads"):
        self.download_path = download_path
        if not os.path.exists(download_path):
            os.makedirs(download_path)

    def search(self, query, max_results = 5):
        """Search for videos on Youtube"""
        search_results = Search(query).results[:max_results]
        formatted_results = []

        for video in search_results:
            formatted_results.append({
                'title': video.title,
                'url' : f"https://youtube.com/watch?v={video.video_id}",
                'thumbnail': video.thumbnail,
                'duration': video.lenght,
                'channel': video.channel,
                'views': video.views,
                'publish_date': video.publish_date
            })

        return formatted_results
    
    def download(self, youtube_url):
        """Download a video from YouTube"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            return f"{self.download_path}/{info['title']}.mp3", info['title']
