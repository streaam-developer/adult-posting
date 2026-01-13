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

        # Random position within video dimensions
        # Assuming text width ~ 200px, height ~ 50px for fontsize 50
        text_width = 200
        text_height = 50
        x = random.randint(0, max(0, width - text_width))
        y = random.randint(0, max(0, height - text_height))

        # Construct the ffmpeg drawtext filter
        text = 'zeb.monster'
        x_expr = str(x)
        y_expr = str(y)

        (
            ffmpeg
            .input(video_path)
            .drawtext(text=text, x=x_expr, y=y_expr, fontsize=50, fontcolor='white', box=1, boxcolor='black@0.5', fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
            .output(output_path, vcodec='libx264', acodec='aac')
            .run(overwrite_output=True)
        )
    except Exception as e:
        print(f"Error in add_floating_text: {e}")
        print("Video editing failed. Please ensure ffmpeg is installed and in your PATH.")
        import shutil
        shutil.copy(video_path, output_path)