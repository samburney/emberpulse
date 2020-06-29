import os
import requests
import pickle
from bs4 import BeautifulSoup

from . import config

# Start API session
def start_session():
    s = None

    # Check if session file exists
    if os.path.isfile(config.session_file):
        with open(config.session_file, 'rb') as f:
            s = pickle.load(f)

    else:
        s = requests.Session()

        # Open login page and get _csrf value
        r = s.get(config.emberpulse_url + '/login')
        soup = BeautifulSoup(r.text, features="html.parser")
        action = soup.form['action']
        csrf = soup.form.find('input', attrs={"name": "_csrf"})['value']

        # Log in
        uri = config.emberpulse_url + action
        data = {
            'username': config.username,
            'password': config.password,
            '_csrf': csrf,
        }
        r = s.post(uri, data=data)

        # Save session to file
        if r.status_code == 200:
            save_session(s)

    return s

# Save session to file
def save_session(s):
    with open(config.session_file, 'wb') as f:
        pickle.dump(s, f)

# Return sid for WebSocket creation
def get_sid():
    sid = None
    
    s = start_session()

    data = {
        'EIO': 3,
        'transport': 'polling',
    }
    r = s.get(config.emberpulse_url + '/socket.io/', params=data)
    if r.status_code == 200:
        cookies = s.cookies.get_dict()
        if 'io' in cookies:
            sid = cookies['io']
            save_session(s)

    return sid
