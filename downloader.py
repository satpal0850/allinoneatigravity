import yt_dlp # type: ignore
import instaloader # type: ignore
import re
from urllib.parse import urlparse

# Initialize Instaloader globally
L = instaloader.Instaloader(
    download_pictures=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False
)

def is_instagram(url: str) -> bool:
    return "instagram.com" in urlparse(url).netloc

def is_snapchat(url: str) -> bool:
    return "snapchat.com" in urlparse(url).netloc

def extract_instagram(url: str, extract_audio: bool = False) -> dict:
    """
    Handle Instagram specifically.
    For Reels/Videos, yt-dlp generally works very well statelessly.
    For Profiles/Stories, Instaloader is required (may require login for private/stories).
    """
    try:
        # Check if it's a profile URL
        match = re.search(r'instagram\.com/([a-zA-Z0-9_\.]+)/?$', url)
        if match and "reel" not in url and "p" not in url and "tv" not in url:
            username = match.group(1)
            profile = instaloader.Profile.from_username(L.context, username)
            return {
                "title": f"Profile: {username}",
                "thumbnail": profile.profile_pic_url,
                "author": profile.full_name,
                "downloads": [
                    {"url": profile.profile_pic_url, "ext": "jpg", "resolution": "Profile Pic"}
                ],
                "type": "image"
            }
            
        # For Reels and Posts, use yt-dlp for best results without login
        # (Instaloader often gets rate limited on posts quickly)
        return extract_with_ytdlp(url, extract_audio)
    except Exception as e:
        return {"error": f"Instagram extraction failed: {str(e)}"}


def extract_snapchat(url: str, extract_audio: bool = False) -> dict:
    """Dedicated yt-dlp extractor for Snapchat. Avoids extract_flat which causes issues on Spotlight."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestaudio/best' if extract_audio else 'best',
        # Do NOT use 'extract_flat' here as it breaks Spotlight/Story extraction
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # If the extraction returned a playlist, grab the first entry
            if 'entries' in info and info['entries']:
                info = info['entries'][0]

            title = info.get('title', 'Snapchat Media')
            thumbnail = info.get('thumbnail', '')
            author = info.get('uploader', info.get('creator', 'Snapchat User'))
            
            downloads = []
            
            if info.get('url'):
                downloads.append({
                    "url": info['url'],
                    "ext": info.get('ext', 'mp3' if extract_audio else 'mp4'),
                    "resolution": f"{info.get('height', 'HD')}p" if info.get('height') else ("Audio" if extract_audio else "HD")
                })
            
            if not downloads:
                return {"error": "Could not extract direct stream link from Snapchat."}
                
            return {
                "title": title,
                "thumbnail": thumbnail,
                "author": author,
                "downloads": downloads,
                "type": "audio" if extract_audio else "video"
            }
            
    except yt_dlp.utils.DownloadError as e:
        return {"error": f"Failed to download information from Snapchat: {str(e)}"}
    except Exception as e:
         return {"error": f"An unexpected error occurred: {str(e)}"}

def extract_with_ytdlp(url: str, extract_audio: bool = False) -> dict:
    """Generic yt-dlp extractor for TikTok, Pinterest, Bluesky, Twitch, etc."""
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestaudio/best' if extract_audio else 'best',
        'extract_flat': 'in_playlist',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Format results
            title = info.get('title', 'Media Download')
            thumbnail = info.get('thumbnail', '')
            author = info.get('uploader', info.get('creator', 'Unknown'))
            
            downloads = []
            
            if info.get('url'):
                downloads.append({
                    "url": info['url'],
                    "ext": info.get('ext', 'mp3' if extract_audio else 'mp4'),
                    "resolution": f"{info.get('height', 'HD')}p" if info.get('height') else ("Audio" if extract_audio else "HD")
                })
            
            if not downloads:
                return {"error": "Could not extract direct stream link. Site might be blocking access."}
                
            return {
                "title": title,
                "thumbnail": thumbnail,
                "author": author,
                "downloads": downloads,
                "type": "audio" if extract_audio else "video"
            }
            
    except yt_dlp.utils.DownloadError as e:
        return {"error": f"Failed to download information: {str(e)}"}
    except Exception as e:
         return {"error": f"An unexpected error occurred: {str(e)}"}

def extract_media(url: str, format_type: str = "video") -> dict:
    """Main entry point for extracting media."""
    extract_audio = format_type == "audio"
    
    # Specific handlers
    if is_instagram(url):
         result = extract_instagram(url, extract_audio)
    elif is_snapchat(url):
         result = extract_snapchat(url, extract_audio)
    else:
        # yt-dlp natively supports TikTok, Twitch, Pinterest, Bluesky
        result = extract_with_ytdlp(url, extract_audio)
        
    return result
