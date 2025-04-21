import yt_dlp
import os

def download_youtube_video(url, quality="best"):
    # Get the path to the user's Downloads folder (works on most OS)
    download_folder = os.path.join(os.path.expanduser("~"), "Downloads")

    # Ensure the folder exists
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    # Setting options for yt-dlp
    ydl_opts = {
        'format': quality,  # You can set the desired quality here (e.g., 'best', 'worst', 'bestaudio', etc.)
        'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),  # Store video in Downloads folder
        'noplaylist': True,  # Do not download playlists
    }

    try:
        # Create a yt-dlp object with the specified options
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download the video using the provided URL
            ydl.download([url])
        print(f"Download completed successfully! The video is stored in {download_folder}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example usage
if __name__ == "__main__":
    url = input("Enter YouTube video URL: ")
    download_youtube_video(url)
