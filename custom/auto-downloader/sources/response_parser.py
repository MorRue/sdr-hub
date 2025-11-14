from bs4 import BeautifulSoup
from datetime import datetime,timedelta

def get_csrf_token(response_text):
    soup = BeautifulSoup(response_text, 'html.parser')
    csrf_token = soup.find('input', attrs={'name': 'csrfmiddlewaretoken'})['value']
    return csrf_token

def get_complete_table(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='table table-striped table-bordered table-hover')
    return table

def get_rows(table):
    rows = table.find_all('tr')
    # Remove first row because it only contains the filter
    rows = rows[1:]
    return rows

def get_headers(row):
    # Extract headers from second row
    header_cells = row.find_all(['th', 'td'])
    headers = []
    for cell in header_cells:
        text = cell.get_text(separator=' ', strip=True)
        headers.append(text)
    return headers


# <td class="py-1"> <nobr> 2025-09-29 <b>12:18:41</b> </nobr> </td>
def handle_date_cell(cell):
    # Extract the date and time from the <nobr> and <b> tags
    date_text = cell.find('nobr').contents[0].strip()  # '2025-09-29'
    time_text = cell.find('b').text.strip()            # '12:18:41'
    full_datetime_str = f"{date_text} {time_text}"     # '2025-09-29 12:18:41'
    return datetime.strptime(full_datetime_str, "%Y-%m-%d %H:%M:%S")

# <td class="py-1">0:01:06</td>
def handle_duration_cell(cell):
    # Example: "0:01:00" (h:mm:ss)
    duration_str = cell.text.strip()
    h, m, s = map(int, duration_str.split(":"))
    return timedelta(hours=h, minutes=m, seconds=s)

# <td class="py-1">
#  <div class="btn-group" role="group">
#      <audio controls="" preload="none">
#          <source src="/sdr/transmission/17/data" type="audio/mpeg">
#      </audio>
#      <a href="/sdr/transmission/17/data" class="btn btn-primary" download="">
#         download </a>
# </div>
#</td>
def handle_decoded_file_cell(cell):
    link = cell.find('a', string=lambda s: s and 'download' in s.lower())
    value = link['href'] if link else ''
    return value

#<td class="py-1">145.400 MHz</td>
def handle_frequency_cell(cell):
    text = cell.text.strip()
    text = text.replace(" ", "").replace(".", "_")
    return text

def get_data_from_rows(response_text):
    table = get_complete_table(response_text)
    rows = get_rows(table)
    headers = get_headers(rows[0])
    data_rows = rows[1:]

    data = []
    for row in data_rows:
        cells = row.find_all('td')
        entry = {}

        for i, cell in enumerate(cells):
            # Handle the "Date" field with <nobr> and <b>
            if headers[i] == "Date":
                entry[headers[i]] = handle_date_cell(cell)
        # Handle the "Duration" field
            elif headers[i] == "Duration":
                entry[headers[i]] = handle_duration_cell(cell)
        # Handle "Decoded file" column (get audio source link)
            elif headers[i] == "Decoded file":
                entry[headers[i]] = handle_decoded_file_cell(cell)
        # Handle "Frequency" column
            elif headers[i] == "Frequency":
                entry[headers[i]] = handle_frequency_cell(cell)
        data.append(entry)
    return data