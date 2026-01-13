import random
import shutil

import ffmpeg

# Video editor function
def add_floating_text(video_path, output_path):
    """Add floating 'zeb.monster' text to video in random places and directions."""
    try:
        # Get video dimensions
        probe = ffmpeg.probe(video_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        width = int(video_stream['width'])
        height = int(video_stream['height'])

        # Random movement across the video
        amplitude_x = random.uniform(width / 8, width / 2)
        amplitude_y = random.uniform(height / 8, height / 2)
        freq_x = random.uniform(0.05, 0.2)
        freq_y = random.uniform(0.05, 0.2)
        offset_x = random.uniform(0, width / 2)
        offset_y = random.uniform(0, height / 2)

        # Construct the ffmpeg drawtext filter
        text = 'zeb.monster'
        x_expr = f"{offset_x} + {amplitude_x}*sin({freq_x}*2*PI*t)"
        y_expr = f"{offset_y} + {amplitude_y}*cos({freq_y}*2*PI*t)"

        (
            ffmpeg
            .input(video_path)
            .drawtext(text=text, x=x_expr, y=y_expr, fontsize=24, fontcolor='white', box=1, boxcolor='black@0.5')
            .output(output_path, vcodec='libx264', acodec='aac')
            .run(overwrite_output=True)
        )
    except Exception as e:
        print(f"Error in add_floating_text: {e}")
        print("Video editing failed. Please ensure ffmpeg is installed and in your PATH.")
        import shutil
        shutil.copy(video_path, output_path)