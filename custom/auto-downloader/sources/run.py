# taken from: https://pastebin.com/raw/sD67WXcp
# NEITHER TESTED NOR REVIEWED
import requests
import time
import os

from download_util import login
from download_util import get_recording_data
from download_util import recording_ready_for_download
from download_util import download_mp3

# Time interval for checking (in seconds)
CHECK_INTERVAL = 30  # Check every 30 seconds
# Name of the folder for saving sounds
SOUNDS_DIR = 'sounds'

# If the folder doesn't exist, create it
if not os.path.exists(SOUNDS_DIR):
    os.makedirs(SOUNDS_DIR)


# Start session
with requests.Session() as session:
    # Log in
    response = login(session)

    if response.url.endswith('/'):
        print("Login was successful.")

        while True:
            data = get_recording_data(session)
            for d in data:
                if recording_ready_for_download(d):
                    download_mp3(session,d,SOUNDS_DIR)
            time.sleep(CHECK_INTERVAL)
    else:
        print("Login failed.")