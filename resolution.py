import ffmpeg

input_file = './assets/minecraft_parkour.mp4'  # Replace with your input file path
output_file = './assets/minecraft_parkour_test.mp4'  # Replace with your desired output file path

# Get video info to calculate the crop area
probe = ffmpeg.probe(input_file)
video_info = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
width = int(video_info['width'])
height = int(video_info['height'])

# Calculate cropping parameters to maintain the 9:16 aspect ratio
crop_height = int((width * 16) / 9)
crop_y = (height - crop_height) // 2

# Set the start time to skip the first 10 seconds
start_time = 10  # in seconds

# Execute ffmpeg command to skip the first 10 seconds, crop, and resize video
(
    ffmpeg
    .input(input_file, ss=start_time)  # Skip the first 10 seconds
    .filter('crop', width, crop_height, 0, crop_y)  # Crop to the center, adjusting to maintain 9:16 aspect ratio
    .filter('scale', 1080, 1920)  # Then resize to 1080x1920
    .output(output_file, b='10613k', r='60')  # Maintain high bitrate and frame rate
    .run()
)

print(f"Resized video saved as {output_file}")
