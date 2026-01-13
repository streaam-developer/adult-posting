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

        # Center of the screen
        center_x = width / 2
        center_y = height / 2

        # Random amplitudes and frequencies for sinusoidal movement
        amplitude_x = random.uniform(0, width / 4)
        amplitude_y = random.uniform(0, height / 4)
        freq_x = random.uniform(0.1, 0.5)
        freq_y = random.uniform(0.1, 0.5)

        # Construct the ffmpeg drawtext filter
        text = 'zeb.monster'
        x_expr = f"{center_x} + {amplitude_x}*sin({freq_x}*2*PI*t)"
        y_expr = f"{center_y} + {amplitude_y}*sin({freq_y}*2*PI*t)"

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