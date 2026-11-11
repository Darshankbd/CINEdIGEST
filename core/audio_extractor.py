import os
import subprocess

def extract_audio(video_path: str, output_audio_path: str = None) -> str:
    """
    Extracts 16kHz mono WAV audio from video files (mp4, mkv, mov) using imageio_ffmpeg.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    if output_audio_path is None:
        base, _ = os.path.splitext(video_path)
        output_audio_path = f"{base}_audio.wav"

    # 1. Use imageio-ffmpeg bundled binary
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg_exe, "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            output_audio_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(output_audio_path):
            return output_audio_path
    except Exception:
        pass

    # 2. Fallback to system ffmpeg if present
    try:
        cmd = [
            "ffmpeg", "-y", "-i", video_path, 
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", 
            output_audio_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and os.path.exists(output_audio_path):
            return output_audio_path
    except Exception:
        pass

    return output_audio_path
