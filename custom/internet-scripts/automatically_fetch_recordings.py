# taken from: https://pastebin.com/raw/sD67WXcp
# NEITHER TESTED NOR REVIEWED

import requests
from bs4 import BeautifulSoup
import time
import re
import os

# Get credentials and base URL from environment
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8000')
LOGIN_URL = f'{BASE_URL}/admin/login/'
USERNAME = os.environ.get('USERNAME', 'admin')
PASSWORD = os.environ.get('PASSWORD', 'password')

# Time interval for checking (in seconds)
CHECK_INTERVAL = 30  # Check every 30 seconds

# Name of the folder for saving sounds
SOUNDS_DIR = 'sounds'

# If the folder doesn't exist, create it
if not os.path.exists(SOUNDS_DIR):
    os.makedirs(SOUNDS_DIR)

# Function to login and get CSRF token
def login(session):
    response = session.get(LOGIN_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', attrs={'name': 'csrfmiddlewaretoken'})['value']
    payload = {
        'csrfmiddlewaretoken': csrf_token,
        'username': USERNAME,
        'password': PASSWORD
    }
    return session.post(LOGIN_URL, data=payload, headers={'Referer': LOGIN_URL}), csrf_token

# Function to get the list of available files
def get_latest_file_number(session):
    response = session.get(f'{BASE_URL}/sdr/transmissions/')
    soup = BeautifulSoup(response.text, 'html.parser')
    file_numbers = [
        int(link.get('href').split('/')[-2])  # Change the index from [-3] to [-2]
        for link in soup.find_all('a', href=re.compile(r'/sdr/transmission/\d+/data'))
    ]
    return max(file_numbers) if file_numbers else None


# Start session
with requests.Session() as session:
    # Log in
    response, csrf_token = login(session)

    if response.url.endswith('/'):
        print("Login was successful.")
        last_downloaded_file = None
        
        while True:
            latest_file_number = get_latest_file_number(session)
            
            if latest_file_number is None:
                print("Failed to retrieve file numbers.")
                time.sleep(CHECK_INTERVAL)
                continue

            if last_downloaded_file is None or latest_file_number > last_downloaded_file:
                last_downloaded_file = latest_file_number
                DATA_URL = f'{BASE_URL}/sdr/transmission/{latest_file_number}/data'
                
                # Download the file
                response = session.get(DATA_URL)
                if response.ok:
                    # Save the file to the 'sounds' folder
                    filename = os.path.join(SOUNDS_DIR, f'{latest_file_number}.mp3')
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"File {filename} has been successfully downloaded.")
                else:
                    print("Failed to download the file.")
            
            time.sleep(CHECK_INTERVAL)
    else:
        print("Login failed.")