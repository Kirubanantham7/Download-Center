from flask import Flask, render_template, request
import yt_dlp
import os

app = Flask(__name__)

# Path to the Downloads folder (customize as needed)
downloads_folder = os.path.expanduser('~/Downloads')

# Function to handle Instagram downloads
def download_instagram(url):
    options = {
        'outtmpl': os.path.join(downloads_folder, '%(title)s.%(ext)s'),  # Save video/image in Downloads folder with title as filename
        'noplaylist': True,  # Ensure only the single media is downloaded
        'merge_output_format': 'mp4',  # For videos, ensure the output is in mp4 format
        'format': 'best',  # Default to best quality available
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            # Download the content from the provided URL
            ydl.download([url])
        return "Download completed!"
    except Exception as e:
        return f"An error occurred: {e}"

# Route to handle the home page and form submission
@app.route('/')
def home():
    return render_template('index.html')

# Route to handle the Instagram download
@app.route('/download_instagram', methods=['POST'])
def download_instagram_route():
    url = request.form['url']

    # Call the download function
    result = download_instagram(url)

    # Return the result to the user
    return render_template('download_success.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)





