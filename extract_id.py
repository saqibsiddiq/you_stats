import re
import requests
import subprocess
import sys
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    print("Error: YOUTUBE_API_KEY is not set. Please configure your environment variables.")
    sys.exit(1)

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

def extract_handle_from_url(url):
    """
    Extracts the YouTube handle (e.g., @GangstaPerspectives) from a given URL.
    
    Args:
        url (str): The YouTube channel homepage URL.
    
    Returns:
        str: The extracted handle, or None if not found.
    """
    pattern = r'youtube\.com/@([a-zA-Z0-9_-]+)'
    match = re.search(pattern, url)
    if match:
        return f"@{match.group(1)}"  
    return None

def get_channel_id_from_url(url):
    """
    Resolves a YouTube channel homepage URL to the channel ID.
    
    Args:
        url (str): The YouTube channel homepage URL.
    
    Returns:
        str: The resolved channel ID, or an error message.
    """
    handle = extract_handle_from_url(url)
    if not handle:
        return "Invalid YouTube URL: No handle found."

    base_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": handle,
        "type": "channel",
        "key": API_KEY,
    }
    
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "items" in data and data["items"]:
            return data["items"][0]["id"]["channelId"]
        else:
            return "No channel ID found for the given URL."
    else:
        return f"Error: {response.status_code}, {response.text}"

def main():
    url = input("Enter the YouTube channel homepage URL (e.g., https://www.youtube.com/@GangstaPerspectives): ")
    channel_id = get_channel_id_from_url(url)
    print(f"Resolved Channel ID: {channel_id}")
    
    if "Error" not in channel_id and "No channel ID found" not in channel_id:
        print("Calling main.py with the resolved channel ID...")
        subprocess.run([sys.executable, 'main.py', channel_id, API_KEY]) 

if __name__ == "__main__":
    main()