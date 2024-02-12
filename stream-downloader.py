import requests, datetime, time, os, subprocess
from requests.auth import HTTPBasicAuth
from tools import Tools
from pathlib import Path

tools = Tools()

def convert_mjpeg_to_mp4(input_filename, output_filename):
    """
    Converts an MJPEG video file to MP4 format using ffmpeg.

    Args:
    - input_filename (str): The path to the input MJPEG file.
    - output_filename (str): The desired path for the output MP4 file.
    """
    try:
        # Construct the ffmpeg command to convert the video format
        command = [
            'ffmpeg',
            '-i', input_filename,  # Input file
            '-vcodec', 'libx264',  # Specify the video codec
            '-pix_fmt', 'yuv420p',  # Specify the pixel format
            output_filename  # Output file
        ]
        Tools.log(' '.join(command))

        # Execute the ffmpeg command
        a = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    except Exception as e:
        Tools.log(f"Error during conversion: ")
        Tools.log(e)

def delete_old_files(directory, exts, hours=14*24):
    """
    Deletes files older than a specified number of hours from the given directory.

    Args:
    - directory (str): The path to the directory containing MP4 files.
    - exts (list): Extensions of files which should be deleted.
    - hours (int): The age threshold in hours for deleting files. Files older than this will be deleted.
    """
    # Get the current time
    now = datetime.datetime.now()
    # Calculate the threshold time
    cutoff = now - datetime.timedelta(hours=hours)

    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        # Construct the full path to the file
        file_path = os.path.join(directory, filename)
        ext = Path(filename).suffix.lstrip('.')
        # Check if the file is an MP4 file
        if ext in exts:
            # Get the file's modification time
            file_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            # Check if the file is older than the cutoff time
            if file_mod_time < cutoff:
                # Delete the file
                os.remove(file_path)
                print(f"Deleted: {file_path}")

def download_stream(url:str, directory:str, login:str, password:str, duration=60):
    """
    Downloads MJPEG video stream with HTTP Basic Authentication and saves it into hourly segments.

    Args:
    - url (str): The URL of the MJPEG video stream.
    - login (str): The login or username for HTTP Basic Authentication.
    - password (str): The password for HTTP Basic Authentication.
    - duration (int): Duration in seconds for each segment. Default is 3600 seconds (1 hour).
    """
    directory = directory.rstrip('/\\')

    # Create an HTTPBasicAuth object for authentication
    auth = HTTPBasicAuth(login, password)

    while True:
        # Generate the filename based on the current date and time
        filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print('')
        Tools.log(f"Starting to download stream to {directory}/{filename}.mjpeg")

        # Open the stream with authentication
        with requests.get(url, auth=auth, stream=True) as r:
            r.raise_for_status()  # Ensure the request was successful
            start_time = time.time()

            # Open the file to write the stream into
            with open(f"{directory}/{filename}.mjpeg", 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    # Check if the duration has passed, and if so, break the loop to start a new file
                    if time.time() - start_time > duration:
                        break
                    # Write video stream to the file in chunks
                    if chunk:
                        f.write(chunk)

        # Convert mjpeg to mp4
        convert_mjpeg_to_mp4(f"{directory}/{filename}.mjpeg", f"{directory}/{filename}.mp4")

        # Delete old recordings
        delete_old_files(directory, ['mp4', 'mkv', 'avi'], hours=14*24)
        delete_old_files(directory, ['mjpeg'], hours=2)  # delete mjpeg videos after the conversion to mp4

if __name__ == "__main__":
    import config
    download_stream(config.VIDEO_STREAM_URL, config.DIRECTORY, config.LOGIN, config.PASSWORD)
