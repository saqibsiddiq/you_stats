import sys
import psycopg2
from googleapiclient.discovery import build
import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

CONN_STRING = os.getenv("DATABASE_URL")

def clean_title(title):
    return title.encode('utf-8', 'ignore').decode('utf-8')

def get_channel_data(youtube, channel_id):
    request = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    )
    response = request.execute()

    for item in response["items"]:
        channel_data = {
            "channel_id": item["id"],
            "channel_name": item["snippet"]["title"],
            "subscribers": int(item["statistics"].get("subscriberCount", 0)),
            "total_views": int(item["statistics"].get("viewCount", 0)),
            "total_videos": int(item["statistics"].get("videoCount", 0)),
            "last_updated": datetime.datetime.now()
        }
    return channel_data

def get_videos(youtube, channel_id):
    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=50,
        order="date",
        type="video"
    )
    response = request.execute()

    videos = []
    for item in response["items"]:
        videos.append({
            "video_id": item["id"]["videoId"],
            "channel_id": channel_id,
            "title": item["snippet"]["title"],
            "publish_date": item["snippet"]["publishedAt"]
        })
    return videos

def get_video_stats(youtube, video_id):
    request = youtube.videos().list(
        part="statistics",
        id=video_id
    )
    response = request.execute()

    stats = {}
    for item in response["items"]:
        stats = {
            "views": int(item["statistics"].get("viewCount", 0)),
            "likes": int(item["statistics"].get("likeCount", 0)),
            "comments": int(item["statistics"].get("commentCount", 0)),
        }
    return stats

def save_to_database(channel_data, videos_data):
    try:
        conn = psycopg2.connect(CONN_STRING)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()

        cursor.execute("DELETE FROM youtube_videos WHERE channel_id = %s", (channel_data['channel_id'],))
        cursor.execute("DELETE FROM youtube_channel WHERE channel_id = %s", (channel_data['channel_id'],))

        cursor.execute("""
            INSERT INTO youtube_channel (channel_id, channel_name, subscribers, total_views, total_videos, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (channel_data['channel_id'], channel_data['channel_name'], channel_data['subscribers'],
              channel_data['total_views'], channel_data['total_videos'], channel_data['last_updated']))

        for video in videos_data:
            video['title'] = clean_title(video['title'])
            video_stats = get_video_stats(build("youtube", "v3", developerKey=API_KEY), video['video_id'])
            video.update(video_stats)
            
            cursor.execute("""
                INSERT INTO youtube_videos (video_id, channel_id, title, publish_date, views, likes, comments)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (video['video_id'], video['channel_id'], video['title'], video['publish_date'], 
                  video['views'], video['likes'], video['comments']))

        conn.commit()
        print("Data successfully saved to the database.")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        if conn:
            conn.close()

def main(channel_id):
    youtube = build("youtube", "v3", developerKey=API_KEY)

    channel_data = get_channel_data(youtube, channel_id)
    videos_data = get_videos(youtube, channel_id)

    save_to_database(channel_data, videos_data)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        channel_id = sys.argv[1]
        main(channel_id)
    else:
        print("No channel ID provided!")

