from __future__ import print_function
from pynetgear import Netgear
import urllib3
import json
import os
import base64

# TOGGLE DEBUG LOGGING
# import logging
# logging.basicConfig(level=logging.DEBUG)

from http.server import HTTPServer, BaseHTTPRequestHandler

from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from datetime import date, datetime, timezone

import threading, time

from twilio.rest import Client

mutex = threading.Lock()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

DISABLED_DEVICES = []

f = open('config.json',) 
config = json.load(f) 

twilioClient = Client(config['twilio']['account_sid'], config['twilio']['auth_token'])

mutex = threading.Lock()

import requests
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        mutex.acquire()
        self.wfile.write(bytes('DISABLED DEVICES: {}'.format(DISABLED_DEVICES), 'utf-8'))
        mutex.release()

class web_server_thread(threading.Thread):
    def run(self):
        global mutex
        global DISABLED_DEVICES
        print("Starting the web server")
        httpd = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
        httpd.serve_forever()

class activity_monitor_thread(threading.Thread):
    def toggle_network(self, denyallow, mac, message):
        netgear = Netgear(
            password=base64.b64decode(config['router']['password']).decode('utf-8'),
            user=config['router']['user'])
            
        notify_phone_number = config['twilio']['notify']

        print('Toggling Network {} to {}'.format(mac, denyallow))
        if self.is_mac_address(mac):
            netgear.allow_block_device(mac_addr=mac, device_status=denyallow)
        else:
            for group in config['device_groups']:
                if group['name'] == mac:
                    for device in group['devices']:
                        netgear.allow_block_device(mac_addr=device, device_status=denyallow)
                    notify_phone_number = group['notify']

        mutex.acquire()
        if denyallow == "Block" and mac not in DISABLED_DEVICES:
            if message != '' and config['twilio']['number'] != '':
                twilioClient.messages.create(
                    from_=config['twilio']['number'],
                    to=notify_phone_number,
                    body=message
                )

            DISABLED_DEVICES.append(mac)
        
        if denyallow == "Allow" and mac in DISABLED_DEVICES:
            if message != '' and config['twilio']['number'] != '':
                twilioClient.messages.create(
                    from_=config['twilio']['number'],
                    to=notify_phone_number,
                    body='Hooray!  {}'.format(message)
                )

            DISABLED_DEVICES.remove(mac)
        mutex.release()

    def validate_steps(self, client, required_steps, mac):
        today = date.today()

        all_steps = 0
        try:
            steps = client.get_steps_data(today.isoformat())
            for s in steps:
                all_steps += s['steps']
        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
        ) as err:
            print("Error occurred during Garmin Connect Client get steps data: %s" % err)
            return
        except Exception:  # pylint: disable=broad-except
            print("Unknown error occurred during Garmin Connect Client get steps data")
            return
        
        if all_steps >= int(required_steps):
            msg = 'You\'ve taken {} steps, which is greater than the required {}! Enabling your device ({})!'.format(all_steps, required_steps, mac)
            print(msg)
            self.toggle_network('Allow', mac, msg)
        else:
            msg = 'Oh No! You\'ve only taken {} steps, which is less than the required {}! Disabling your device ({}) until you take care of business!'.format(all_steps, required_steps, mac)
            print(msg)
            self.toggle_network('Block', mac, msg)

    def validate_stats(self, client, stat, required_value, mac):
        today = date.today()

        value = 0
        try:
            stats = client.get_stats(today.isoformat())
            value = stats[stat]
        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
        ) as err:
            print("Error occurred during Garmin Connect Client get steps data: %s" % err)
            return
        except Exception:  # pylint: disable=broad-except
            print("Unknown error occurred during Garmin Connect Client get steps data")
            return
        
        if value >= int(required_value):
            msg = 'Value in Garmin Connect for {} was {}, which is greater than the required {}! Enabling your device ({})!'.format(stat, value, required_value, mac)
            print(msg)
            self.toggle_network('Allow', mac, msg)
        else:
            msg = 'Oh No! Value in Garmin Connect for {} was {}, which is less than the required {}! Disabling your device ({}) until you take care of business!!'.format(stat, value, required_value, mac)
            print(msg)
            self.toggle_network('Block', mac, msg)

    def time_in_range(self, start, end, time):
        if end < start:
            return time >= start or time <= end
        return start <= time <= end

    def get_active_events(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        service = build('calendar', 'v3', credentials=creds)

        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId=config['calendar_id'], timeMin=now,
                                            maxResults=10, singleEvents=True,
                                            orderBy='startTime').execute()
        events = events_result.get('items', [])

        valid_events = []
        if not events:
            return []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            right_now = datetime.now(timezone.utc)
            if self.time_in_range(datetime.strptime(start, '%Y-%m-%dT%H:%M:%S%z'), datetime.strptime(end, '%Y-%m-%dT%H:%M:%S%z'), right_now):
                valid_events.append(event['summary'])
            
        return valid_events
        
    def process_command(self, command, param, mac, garmin_client):
        print('Handling {} ({}) for {}'.format(command, param, mac))

        if command == "TOGGLE":
            self.toggle_network(param, mac, "")
        elif command == "STEPS":
            self.validate_steps(garmin_client, param, mac)
        elif command == "STATS":
            parts = str.split(param, '=')
            if len(parts) == 2:
                self.validate_stats(garmin_client, parts[0], int(parts[1]), mac)
            else:
                print("ERROR, Invalid format for STATS parameter ({}) expected <stat>=<value>!".format(param))

    def is_mac_address(self, name):
        if len(str.split(name, ':')) == 6:
            return True
        else:
            return False

    def check_activity(self, garmin_client):
        events = self.get_active_events()
        found_mac = []
        for event in events:
            parts = str.split(event, ';')
            if len(parts) == 3:
                self.process_command(parts[0], parts[1], parts[2], garmin_client)
                found_mac.append(parts[2])
        
        mutex.acquire()
        devices = DISABLED_DEVICES
        mutex.release()

        # Enable any expired disablements
        for d in devices:
            if d not in found_mac:
                self.toggle_network('Allow', d, '')
        
    def init_client(self):
        try:
            client = Garmin(config['garmin_account']['email'], base64.b64decode(config['garmin_account']['password']))
        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
        ) as err:
            print("Error occurred during Garmin Connect Client init: %s" % err)
            quit()
        except Exception:  # pylint: disable=broad-except
            print("Unknown error occurred during Garmin Connect Client init")
            quit()

        try:
            client.login()
        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
        ) as err:
            print("Error occurred during Garmin Connect Client login: %s" % err)
            quit()
        except Exception:  # pylint: disable=broad-except
            print("Unknown error occurred during Garmin Connect Client login")
            quit()

        return client

    def run(self):
        global mutex
        global DISABLED_DEVICES

        garmin_client = self.init_client()
        while True:
            self.check_activity(garmin_client)

            print('Sleep {} seconds (because Garmin Connect...)'.format(config['refresh_time_sec']))
            time.sleep(config['refresh_time_sec'])

def main():
    #t1 = web_server_thread()
    t2 = activity_monitor_thread()
    #t2.daemon = True

    #t1.start()
    t2.run()

if __name__ == '__main__':
    main()
