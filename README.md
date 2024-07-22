# Video-Generator

The Video-Generator project automates the process of creating engaging video content using text-to-speech and video editing techniques. It primarily integrates with Reddit to fetch stories and generate videos with audio narrations and subtitles.

## Features

- **Text-to-Speech Conversion**: Utilizes the ElevenLabs API to convert Reddit stories into audio files with timestamps.
- **Video Editing**: Incorporates FFmpeg to synchronize audio with video clips, apply overlays, and generate final video outputs.
- **Subtitle Generation**: Creates .ass subtitle files from the timestamps and story text.
- **Story Filtering and Cleaning**: Processes Reddit stories, cleans text, and replaces specific terms with more appropriate alternatives.
- **Social Media Upload**: Automates the uploading of generated videos to Instagram and TikTok with custom titles and thumbnails.

## Project Structure

- **main.py**: The main script that orchestrates the entire video generation process.
- **resolution.py**: A utility script to resize and crop videos to a specific aspect ratio.
- **stories.py**: Handles fetching, cleaning, and storing Reddit stories.
- **upload.py**: Manages the uploading of videos to Instagram and TikTok, including thumbnail extraction and title generation.

## Installation

To install the necessary dependencies, run:

```bash
pip install -r requirements.txt
```

## Usage

### Generating Videos

**Prepare Assets**: Ensure the following assets are available in the `./assets` directory:

- `story.txt`: The Reddit story text file.
- `minecraft_parkour.mp4`: The video clip to be used.
- `myanmar.ttf`: Font file for subtitles.
- `Card.png`: Image overlay for the video.

**Run the Main Script**:

```bash
python main.py
```

## Uploading Videos
### Extract Thumbnail and Upload to Instagram:

```bash
python upload.py
```

This script will:

1. Extract the first frame of the video as a thumbnail.
2. Generate a title from the first sentence of the story.
3. Upload the video to Instagram using the provided credentials.






