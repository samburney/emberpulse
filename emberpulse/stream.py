import time
import threading
import traceback
import json
import re
import websocket
import requests
import pytz
from datetime import datetime, timezone

from . import config, session

# Start WebSocket Stream
def start_stream():
    connect = True
    while connect == True:
        connect = ws_connect()
        time.sleep(10)

# Connect to WebSocket
def ws_connect():
    sid = session.get_sid()
    emberpulse_url = config.emberpulse_url.replace('https', 'wss')
    url = f'{emberpulse_url}/socket.io/?EIO=3&transport=websocket&sid={sid}'

    ws = websocket.WebSocketApp(
                                url,
                                on_message = ws_message,
                                on_error = ws_error,
                                on_close = ws_close
                                )
    ws.on_open = ws_open
    
    ## Connect in a loop
    while ws.run_forever():
        if threading.active_count() > 1:
            print('Waiting for threads to end...')
            while threading.active_count() > 1:
                time.sleep(1)
        print('Reconnecting...')

        return True
    
    return False

# Open new WebSocket connection
def ws_open(ws):
    print('Connected.')

    # Send 'start' message (Expect '3probe' as response)
    ws.send('2probe')
    time.sleep(1)

    # This appears to request the server begin streaming messages
    ws.send('5')

    # Start keep-alive for this connection
    ws_keepalive(ws)

# Create thread to send keep-alive messages
def ws_keepalive(ws):
    def keepalive_thread(*args):

        # Send keep-alive message (Expect '3' as response)
        while ws.sock is not None:
            ws.send('2')
            time.sleep(10)

    t = threading.Thread(target=keepalive_thread)
    t.start()

# Handle messages
def ws_message(ws, message):
    try:
        message_match = re.match('^42(.*)$', message)
        if message_match is not None:
            data = json.loads(message_match.group(1))
            if data is not None:
                process_data(data[0], data[1])
    except:
        traceback.print_exc()

# Handle errors
def ws_error(ws, error):
    print(f'Error: {error}')

# Handle connection close
def ws_close(ws, *args):
    print(f'Connection closed.')

# Process data
def process_data(endpoint, data):
    # Handle device data
    if endpoint == 'ha/attribute':
        output_data = process_device_data(endpoint, data)
    else:
        output_data = process_metric_data(endpoint, data)

    if output_data is not None:
        if config.debug is False:
            r = requests.post(config.telegraf_url, json=output_data)
            print(r.status_code, output_data)
        else:
            print('DEBUG', output_data)

# Process device output
def process_device_data(endpoint, data):
    output_data = None

    if data['type'] == "29":
        device_id = data['external_id']
        device_input = data['parent']['endpoint']['id']

        for device in config.devices:
            if device['device_id'] == device_id and device['device_input'] == device_input:
                date = datetime.fromisoformat(data['updated'])
                timestamp = f'{(datetime.timestamp(date.astimezone(pytz.timezone(config.telegraf_timezone))) * 1000):.0f}'

                output_data = {
                    'timestamp': timestamp,
                    'source': 'emberpulse_stream',
                    device['name']: data['value'],
                }

    return output_data
           
# Process other metric data
def process_metric_data(endpoint, data):
    output_data = None

    # Process named values
    if 'name' in data:
        if data['name'] in config.metrics:
            date = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            timestamp = f"{(datetime.timestamp(date.astimezone(pytz.timezone(config.telegraf_timezone))) * 1000):.0f}"

            output_data = {
                'timestamp': timestamp,
                'source': 'emberpulse_stream',
                config.metrics[data['name']]['name']: data['value'],   
            }

    # Derive 'usage' value from 'spending' endpoint
    if endpoint == 'spending':
        date = datetime.now(timezone.utc)
        timestamp = f"{(datetime.timestamp(date.astimezone(pytz.timezone(config.telegraf_timezone))) * 1000):.0f}"
        
        value = data['avgw'] + data['solarpower'] - data['avgw-export']

        output_data = {
            'timestamp': timestamp,
            'source': 'emberpulse_stream',
            'usage': value,
            'led_colour': data['led-colour'],
            'typical_usage': data['typical-avgw'],
        }

    return output_data
