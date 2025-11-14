import os
from datetime import datetime,timedelta

from response_parser import get_data_from_rows
from response_parser import get_csrf_token

# Get credentials and base URL from environment
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8000')
LOGIN_URL = f'{BASE_URL}/admin/login/'
USERNAME = os.environ.get('USERNAME', 'admin')
PASSWORD = os.environ.get('PASSWORD', 'password')


# Function to login and get CSRF token
def login(session):
    response = session.get(LOGIN_URL)
    csrf_token = get_csrf_token(response.text)
    payload = {
        'csrfmiddlewaretoken': csrf_token,
        'username': USERNAME,
        'password': PASSWORD
    }
    return session.post(LOGIN_URL, data=payload, headers={'Referer': LOGIN_URL})

def get_recording_data(session):
    response = session.get(f'{BASE_URL}/sdr/transmissions/')
    data = get_data_from_rows(response.text)
    return data

#    date = data_entry.get("Date")
#    duration = data_entry.get("Duration")
#    file_link = data_entry.get("Decoded file")
def recording_ready_for_download(data_entry):
    current_time = datetime.now()
    gap_in_seconds = 60
    print(f"Current time: {current_time}")
    date_time = data_entry.get("Date")          # datetime object
    duration = data_entry.get("Duration")       # timedelta object

    if date_time and duration:
        end_time = date_time + duration + timedelta(seconds=gap_in_seconds)

        if end_time < current_time:
            print("✅ End time + gap is in the past")
            return True
        else:
            print("⏳ Still ongoing or just ended")
    else:
        print("⚠️ Missing date or duration in entry")
        return False


def make_filename(entry):
    date_time = entry.get("Date")
    frequency = entry.get("Frequency")

    if not date_time or not frequency:
        return None

    # Format date as a filename-safe string
    date_str = date_time.strftime("%Y-%m-%d_%H-%M-%S")

    return f"{date_str}-{frequency}.mp3"

def download_mp3(session, data_entry, directory):
    data_url = f'{BASE_URL}/{data_entry.get("Decoded file")}'
    # Download the file
    response = session.get(data_url)
    if response.ok:
        os.makedirs(directory, exist_ok=True)
        # Save the file to the 'sounds' folder if it does not already exist
        file_path = os.path.join(directory, make_filename(data_entry))
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"File {file_path} has been successfully downloaded.")
    else:
        print("Failed to download the file.")