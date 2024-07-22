import os
import random
import requests
import ffmpeg
from pydub.utils import mediainfo
import subprocess
import sys
import base64
import json

# Paths
reddit_story_path = './assets/story.txt'
minecraft_video_path = './assets/minecraft_parkour.mp4'
audio_output_path = 'reddit_story.wav'
timestamps_output_path = 'timestamps.json'
video_output_path = 'final_video.mp4'
font_path = './assets/myanmar.ttf'
card_path = './assets/Card.png'

voice_male = "NFG5qt843uXKj4pFvR7C"
voice_female = "i4CzbCVWoqvD0P1QJCUL"

# Variables
video_voice = voice_male
speed_up_factor = 1.2

# Flag to determine whether to regenerate audio and timestamps
regenerate_audio_and_timestamps = True 

# List of API keys
# api_keys = [Your API key/keys]

# ElevenLabs subscription API endpoint
subscription_url = "https://api.elevenlabs.io/v1/user/subscription"

# ElevenLabs TTS API endpoint with timestamps
tts_url_with_timestamps = f"https://api.elevenlabs.io/v1/text-to-speech/{video_voice}/with-timestamps"

# Check if FFmpeg and FFprobe are installed
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['ffprobe', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("FFmpeg or FFprobe is not installed or not found in PATH.")
        sys.exit(1)

# Read Reddit story text
def read_story(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        sys.exit(1)

# Check remaining character count for an API key
def check_character_count(api_key):
    headers = {
        "xi-api-key": api_key
    }
    response = requests.get(subscription_url, headers=headers)
    if response.status_code == 200:
        subscription_info = response.json()
        used_chars = subscription_info.get('character_count', 0)
        char_limit = subscription_info.get('character_limit', 0)
        remaining_chars = char_limit - used_chars
        return remaining_chars
    else:
        print(f"Error checking character count: {response.status_code}, {response.text}")
        return 0

# Generate voice-over from text using ElevenLabs API with timestamps
def generate_voice_with_timestamps(text, output_path, api_key):
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    data = {
        "text": text
    }
    response = requests.post(tts_url_with_timestamps, headers=headers, json=data)

    if response.status_code == 200:
        response_data = response.json()
        audio_content = base64.b64decode(response_data.get('audio_base64'))
        timestamps = response_data.get('alignment')

        if audio_content:
            with open(output_path, 'wb') as f:
                f.write(audio_content)
            print(f"Generated audio saved to {output_path}")
            
            # Save timestamps to JSON file
            with open(timestamps_output_path, 'w') as f:
                json.dump(timestamps, f, indent=4)
            print(f"Timestamps saved to {timestamps_output_path}")
            
            return timestamps
        else:
            print("No audio content received.")
            sys.exit(1)
    else:
        print(f"Error: {response.status_code}, {response.text}")
        sys.exit(1)

# Get media duration using FFmpeg
def get_media_duration(file_path):
    info = mediainfo(file_path)
    return float(info['duration'])

def generate_ass_file(timestamps, text, output_path):
    ass_content = """[Script Info]
PlayResX: 1080
PlayResY: 1920
Title: Generated Subtitles
ScriptType: v4.00+
PlayDepth: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, Bold, BorderStyle, Outline, Shadow, Alignment, Encoding
Style: Default, Myanmar Text, 220, &H00FFFFFF, &H00000000, -1, 1, 13, 3, 5, 1

[Events]
Format: Start, End, Style, Text
"""
    # Identify where the first sentence ends
    end_of_first_sentence = -1
    sentence_end_chars = '.!?'
    for i, char in enumerate(text):
        if char in sentence_end_chars:
            end_of_first_sentence = i + 1  # Include the punctuation
            break

    # Create subtitle events
    events = []
    word = ""
    word_start_time = None

    for i in range(end_of_first_sentence, len(text)):
        char = text[i]
        start_time = timestamps['character_start_times_seconds'][i]
        end_time = timestamps['character_end_times_seconds'][i]

        if word == '':
            word_start_time = start_time

        word += char

        if char in ' ,.!?' or i == len(text) - 1:
            word_end_time = end_time
            events.append(f"Dialogue: {seconds_to_ass_time(word_start_time)},{seconds_to_ass_time(word_end_time)},Default,{word.strip()}")
            word = ""
            word_start_time = None

    ass_content += "\n".join(events)

    # Save to file
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(ass_content)

def seconds_to_ass_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds - int(seconds)) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

# Get the end time of the first sentence
def get_first_sentence_end_time(text, timestamps):
    # Find the index of the first period or newline character
    for i, char in enumerate(text):
        if char in {'.', '\n', '?', '!'}:
            return timestamps['character_end_times_seconds'][i]
    return timestamps['character_end_times_seconds'][-1]

# Update timestamps for 20% speed increase
def update_timestamps(timestamps, factor):
    new_timestamps = {
        "characters": timestamps["characters"],
        "character_start_times_seconds": [round(t / factor, 3) for t in timestamps["character_start_times_seconds"]],
        "character_end_times_seconds": [round(t / factor, 3) for t in timestamps["character_end_times_seconds"]]
    }
    return new_timestamps

def main():
    # Remove final video file if it exists
    if os.path.exists(video_output_path):
        os.remove(video_output_path)

    # Ensure FFmpeg and FFprobe are installed
    check_ffmpeg()

    # Read the Reddit story
    reddit_story = read_story(reddit_story_path)
    story_length = len(reddit_story)

    # Generate or load audio and timestamps
    if regenerate_audio_and_timestamps or not os.path.exists(audio_output_path) or not os.path.exists(timestamps_output_path):
        # Find a suitable API key
        api_key = None
        for key in api_keys:
            remaining_chars = check_character_count(key)
            if remaining_chars >= story_length:
                api_key = key
                break
            else:
                print(f"API key {key} has {remaining_chars} characters remaining, not enough for the story length of {story_length} characters.")

        if not api_key:
            print("None of the API keys have enough characters remaining for the text.")
            sys.exit(1)

        # Generate TTS using the selected API key
        timestamps = generate_voice_with_timestamps(reddit_story, audio_output_path, api_key)
    else:
        # Load existing timestamps
        with open(timestamps_output_path, 'r') as f:
            timestamps = json.load(f)
        print(f"Using existing timestamps from {timestamps_output_path}")

    # Speed up audio by 20%
    sped_up_audio_output_path = audio_output_path.replace('.wav', '_sped_up.wav')
    (
        ffmpeg
        .input(audio_output_path)
        .filter('atempo', speed_up_factor)
        .output(sped_up_audio_output_path)
        .run(overwrite_output=True)
    )

    updated_timestamps = update_timestamps(timestamps, speed_up_factor)

    # Save updated timestamps
    updated_timestamps_output_path = timestamps_output_path.replace('.json', '_updated.json')
    with open(updated_timestamps_output_path, 'w') as f:
        json.dump(updated_timestamps, f)

    # Calculate durations
    audio_duration = get_media_duration(sped_up_audio_output_path)
    video_duration = get_media_duration(minecraft_video_path)

    # Determine random start time for the video segment
    max_start_time = video_duration - audio_duration
    start_time = random.uniform(0, max_start_time)

    # Generate .ass subtitle file
    generate_ass_file(updated_timestamps, reddit_story, 'output_subtitles.ass')

    # Determine the end time of the first sentence
    first_sentence_end_time = get_first_sentence_end_time(reddit_story, updated_timestamps)

    # Define the inputs
    video_input = ffmpeg.input(minecraft_video_path, ss=start_time, t=audio_duration + 1)
    audio_input = ffmpeg.input(sped_up_audio_output_path)
    image_input = ffmpeg.input(card_path, stream_loop=-1, t=audio_duration)

    # Define filters and overlay
    video_with_subs = video_input.filter('ass', 'output_subtitles.ass')
    scaled_image = image_input.filter('scale', 'iw*0.80', 'ih*0.80') 

    # Apply overlay
    overlayed_video = ffmpeg.overlay(
        video_with_subs,
        scaled_image,
        x='(main_w-overlay_w)/2',
        y='(main_h-overlay_h)/2-100',
        enable=f'between(t,0,{first_sentence_end_time})'
    )

    # Concatenate and output
    (
        ffmpeg
        .concat(overlayed_video, audio_input, v=1, a=1)
        .output(video_output_path, vcodec='libx264', video_bitrate='10622k', acodec='aac', audio_bitrate='130k')
        .run(overwrite_output=True)
    )

    # Cleanup temporary files
    os.remove('output_subtitles.ass')
    os.remove('reddit_story_sped_up.wav')
    os.remove('timestamps_updated.json')

if __name__ == "__main__":
    main()
