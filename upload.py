from instagrapi import Client
import cv2
import os
import re
import google.auth
import google.auth.transport.requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Extracts the first frame from a video
def extract_first_frame(video_path, thumbnail_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video.")
        return False
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(thumbnail_path, frame)
        print(f"Thumbnail saved to {thumbnail_path}")
    else:
        print("Error: Could not read the first frame.")
    cap.release()
    return ret

# Uploads a reel to Instagram
def upload_instagram_reel(video_path, title, thumbnail_path, instagram_json):
    username = ''
    password = ''
    client = Client()
    client.load_settings(instagram_json)
    client.login(username=username, password=password)
    client.clip_upload(video_path, title, thumbnail=thumbnail_path)

# Extracts the first sentence from a text file
def get_first_sentence(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    match = re.search(r'[^.!?]*[.!?]', text)
    if match:
        return match.group(0).strip()
    else:
        return "No sentence found."

# Uploads a video to YouTube
def upload_youtube_video(video_path, title, description, youtube_json):
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    credentials = Credentials.from_authorized_user_file(youtube_json, SCOPES)

    try:
        youtube = build('youtube', 'v3', credentials=credentials)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": ["redditstories", "reddit", "askreddit"],
                    "categoryId": "22"
                },
                "status": {
                    "privacyStatus": "public"
                }
            },
            media_body=video_path
        )
        response = request.execute()
        print(f"Video uploaded to YouTube with video ID: {response['id']}")

    except HttpError as e:
        print(f"An HTTP error occurred: {e}")
        return False

    return True

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    instagram_json = os.path.join(script_dir, 'instagram.json')
    youtube_json = os.path.join(script_dir, 'youtube_credentials.json')
    video_path = os.path.join(script_dir, '../final_video.mp4')
    story_path = os.path.join(script_dir, '../assets/story.txt')
    thumbnail_path = os.path.join(script_dir, 'thumbnail.jpg')

    title = get_first_sentence(story_path)
    whole_title = f"""{title}
#redditstories #reddit #askreddit
"""
    
    print(whole_title)

    if not extract_first_frame(video_path, thumbnail_path):
        print("Failed to extract thumbnail.")
        return
    
    description = f"{title}\n\n#redditstories #reddit #askreddit"
    if not upload_youtube_video(video_path, title, description, youtube_json):
        print("Failed to upload video to YouTube.")
        return

    upload_instagram_reel(video_path, whole_title, thumbnail_path, instagram_json)



    os.remove(thumbnail_path)

if __name__ == "__main__":
    main()
