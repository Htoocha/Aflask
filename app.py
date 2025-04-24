from flask import Flask, render_template, request
from pytubefix import YouTube
import os
import subprocess

app = Flask(__name__)
DOWNLOAD_PATH = "/storage/emulated/0/memo/"

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    if request.method == 'POST':
        url = request.form.get('url')
        try:
            yt = YouTube(url)
            title = yt.title.replace(" ", "_")

            # Try video in priority order
            video = yt.streams.filter(res="1080p", mime_type="video/mp4", only_video=True).first()
            if not video:
                video = yt.streams.filter(res="720p", mime_type="video/mp4", only_video=True).first()
            if not video:
                video = yt.streams.filter(res="360p", mime_type="video/mp4", only_video=True).first()

            # Get best audio
            audio = yt.streams.filter(only_audio=True, mime_type="audio/mp4").order_by('abr').desc().first()

            if not video or not audio:
                message = "Suitable video or audio stream not found."
            else:
                video_path = video.download(output_path=DOWNLOAD_PATH, filename="temp_video.mp4")
                audio_path = audio.download(output_path=DOWNLOAD_PATH, filename="temp_audio.mp4")
                output_path = os.path.join(DOWNLOAD_PATH, f"{title}.mp4")

                # Merge using ffmpeg
                ffmpeg_cmd = f'ffmpeg -y -i "{video_path}" -i "{audio_path}" -c:v copy -c:a aac "{output_path}"'
                subprocess.run(ffmpeg_cmd, shell=True, check=True)

                os.remove(video_path)
                os.remove(audio_path)

                message = f"Download complete: {output_path}"

        except Exception as e:
            message = f"Error: {str(e)}"

    return render_template("index.html", message=message)

if __name__ == '__main__':
    app.run(debug=True)
