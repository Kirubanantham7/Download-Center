# Paste this in your Flask app file
from flask import Flask, render_template, request, redirect, url_for, send_file
import yt_dlp
import os
import platform
from werkzeug.utils import secure_filename
from urllib.parse import unquote

app = Flask(__name__)

# Add this helper function near the top of your file
def get_yt_dlp_opts(extra_opts=None):
    base_opts = {
        'quiet': True,
        'cookiefile': 'cookies_youtube.txt',
        'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }
    if extra_opts:
        base_opts.update(extra_opts)
    return base_opts

def get_download_folder():
    if platform.system() == "Windows":
        return os.path.join(os.environ["USERPROFILE"], "Downloads")
    else:
        return os.path.join(os.environ["HOME"], "Downloads")

def get_video_details(url):
    with yt_dlp.YoutubeDL({'quiet': True, 'cookies': 'cookies_youtube.txt'}) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'video')
        thumbnail = info.get('thumbnail') or (info['thumbnails'][-1]['url'] if 'thumbnails' in info and info['thumbnails'] else '')
        duration = info.get('duration', 0)
        size = sum(f.get('filesize', 0) for f in info.get('formats', []) if f.get('filesize')) or 0
        return title, thumbnail, size, duration

def get_available_formats(url):
    with yt_dlp.YoutubeDL(get_yt_dlp_opts()) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get('formats', [])

def format_duration(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes} min {secs} sec"

def format_size(bytes_size):
    mb = bytes_size / (1024 * 1024)
    return f"{mb:.2f} MB"

def download_video(url, format_choice, filename_path):
    ydl_opts = get_yt_dlp_opts({
        'format': format_choice,
        'outtmpl': filename_path,
        'merge_output_format': 'mp4',
        'postprocessors': [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}],
    })
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def download_audio(url, filepath):
    ydl_opts = get_yt_dlp_opts({
        'format': 'bestaudio/best',
        'outtmpl': filepath,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    })
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download_youtube', methods=['POST'])
def download_youtube_route():
    url = request.form['url']
    quality = request.form.get('quality', 'default')
    title, thumbnail_url, size, duration = get_video_details(url)
    video_size = format_size(size)
    video_duration = format_duration(duration)

    download_folder = get_download_folder()
    base_title = secure_filename(title)
    mp4_filename = f"{base_title}.mp4"
    mp3_filename = f"{base_title}.mp3"
    mp4_path = os.path.join(download_folder, mp4_filename)
    mp3_path = os.path.join(download_folder, mp3_filename)

    if quality == 'default':
        # Just download YouTube's default best format
        format_choice = 'best'
    else:
        # Convert string to integer resolution
        max_res = int(quality)

        # Get formats and filter video-only ones
        formats = get_available_formats(url)
        valid_video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('height')]

        # Find best video format within max resolution
        best_format = max(
            (f for f in valid_video_formats if f['height'] <= max_res),
            key=lambda f: f.get('height', 0),
            default=None
        )

        if not best_format:
            return f"No suitable format available under {max_res}p", 400

        format_choice = f"{best_format['format_id']}+bestaudio"

    # Download video & audio
    download_video(url, format_choice, mp4_path)
    download_audio(url, mp3_path)

    return redirect(url_for('download_success',
                            platform='YouTube',
                            video_title=title,
                            thumbnail_url=thumbnail_url,
                            video_filename=mp4_filename,
                            audio_filename=mp3_filename,
                            video_size=video_size,
                            duration=video_duration))

@app.route('/download_facebook', methods=['POST'])
def download_facebook_route():
    url = request.form.get('url')
    if not url:
        return "URL is missing.", 400
    try:
        formats = get_available_formats(url)
        valid_formats = [f for f in formats if f.get('height')]
        if not valid_formats:
            return "No valid video formats found.", 400

        format_choice = max(valid_formats, key=lambda f: f['height'])['format_id']
        title, thumbnail, size, duration = get_video_details(url)
        video_size = format_size(size)
        video_duration = format_duration(duration)
        safe_title = secure_filename(f"{title[:150].strip()}.mp4")

        download_folder = get_download_folder()
        file_path = os.path.join(download_folder, safe_title)

        download_video(url, f'{format_choice}+bestaudio', file_path)

        return redirect(url_for('download_success1',
                                platform='Facebook',
                                video_filename=safe_title,
                                video_title=title,
                                thumbnail_url=thumbnail,
                                video_size=video_size,
                                duration=video_duration))
    except Exception as e:
        return f"Facebook video download failed: {str(e)}", 500

@app.route('/download_instagram', methods=['POST'])
def download_instagram_route():
    url = request.form['url']
    try:
        formats = get_available_formats(url)
        valid_formats = [f for f in formats if f.get('height')]
        if not valid_formats:
            return "No valid formats found.", 400

        format_choice = max(valid_formats, key=lambda f: f['height'])['format_id']
        title, thumbnail, size, duration = get_video_details(url)
        video_size = format_size(size)
        video_duration = format_duration(duration)
        safe_title = secure_filename(f"{title[:150].strip()}.mp4")

        download_folder = get_download_folder()
        file_path = os.path.join(download_folder, safe_title)

        download_video(url, f'{format_choice}+bestaudio', file_path)

        return redirect(url_for('download_success1',
                                platform='Instagram',
                                video_filename=safe_title,
                                video_title=title,
                                thumbnail_url=thumbnail,
                                video_size=video_size,
                                duration=video_duration))
    except Exception as e:
        return f"Instagram video download failed: {str(e)}", 500

@app.route('/download_twitter', methods=['POST'])
def download_twitter_route():
    url = request.form['url']
    try:
        formats = get_available_formats(url)
        valid_formats = [f for f in formats if f.get('height')]
        if not valid_formats:
            return "No valid video formats found for Twitter.", 400

        format_choice = max(valid_formats, key=lambda f: f['height'])['format_id']
        title, thumbnail, size, duration = get_video_details(url)
        video_size = format_size(size)
        video_duration = format_duration(duration)
        safe_title = secure_filename(f"{title[:150].strip()}.mp4")

        download_folder = get_download_folder()
        file_path = os.path.join(download_folder, safe_title)

        download_video(url, f'{format_choice}+bestaudio', file_path)

        return redirect(url_for('download_success1',
                                platform='Twitter (X)',
                                video_filename=safe_title,
                                video_title=title,
                                thumbnail_url=thumbnail,
                                video_size=video_size,
                                duration=video_duration))
    except Exception as e:
        return f"Twitter (X) video download failed: {str(e)}", 500


@app.route('/download_tiktok', methods=['POST'])
def download_tiktok_route():
    url = request.form['url']
    try:
        formats = get_available_formats(url)
        valid_formats = [f for f in formats if f.get('height')]
        if not valid_formats:
            return "No valid video formats found for TikTok.", 400

        format_choice = max(valid_formats, key=lambda f: f['height'])['format_id']
        title, thumbnail, size, duration = get_video_details(url)
        video_size = format_size(size)
        video_duration = format_duration(duration)
        safe_title = secure_filename(f"{title[:150].strip()}.mp4")

        download_folder = get_download_folder()
        file_path = os.path.join(download_folder, safe_title)

        download_video(url, f'{format_choice}+bestaudio', file_path)

        return redirect(url_for('download_success1',
                                platform='TikTok',
                                video_filename=safe_title,
                                video_title=title,
                                thumbnail_url=thumbnail,
                                video_size=video_size,
                                duration=video_duration))
    except Exception as e:
        return f"TikTok video download failed: {str(e)}", 500


@app.route('/download_success')
def download_success():
    return render_template('download_success.html',
                           platform=request.args.get('platform'),
                           video_title=request.args.get('video_title'),
                           thumbnail_url=request.args.get('thumbnail_url'),
                           video_filename=request.args.get('video_filename'),
                           audio_filename=request.args.get('audio_filename'),
                           video_size=request.args.get('video_size'),
                           duration=request.args.get('duration'))

@app.route('/download_success1')
def download_success1():
    return render_template('download_success1.html',
                           platform=request.args.get('platform'),
                           video_title=request.args.get('video_title'),
                           thumbnail_url=request.args.get('thumbnail_url'),
                           video_filename=request.args.get('video_filename'),
                           video_size=request.args.get('video_size'),
                           duration=request.args.get('duration'))

@app.route('/download_file/<path:video_filename>')
def download_file(video_filename):
    try:
        decoded_filename = unquote(video_filename)
        safe_name = secure_filename(decoded_filename)
        file_path = os.path.join(get_download_folder(), safe_name)
        return send_file(file_path, as_attachment=True, download_name=safe_name)
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
 
