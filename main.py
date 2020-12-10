from __future__ import print_function
from pynetgear import Netgear
import urllib3
import json
import os
import base64

# TOGGLE DEBUG LOGGING
# import logging
# logging.basicConfig(level=logging.DEBUG)

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

import time

from twilio.rest import Client

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

import requests
from urllib3.exceptions import InsecureRequestWarning

import pymongo

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class MongoConfigDB:
    def update_profile(self, profile_name, devices, notify_phone_number):
        profile_query = {"name": profile_name}
        
        if "profiles" in self.db.list_collection_names():
            profiles_col = self.db["profiles"]

            profiles_col.delete_one(profile_query)

            profile_data = {
                "name": profile_name,
                "devices": devices,
                "notify_phone_number": notify_phone_number
            }
            profiles_col.insert_one(profile_data)
        else:
            profiles_col = self.db["profiles"]
            profiles_col.insert_one(profile_query)

    def get_profile(self, profile_name):
        profile_query = {"name": profile_name}
        if "profiles" in self.db.list_collection_names():
            profile = self.db["profiles"].find_one(profile_query)
            return profile
        
        return None

    def insert_disabled_device(self, device):
        device_query = {"name" : device}

        if "disabled_devices" in self.db.list_collection_names():
            disabled_devices_col = self.db["disabled_devices"]

            if disabled_devices_col.find_one(device_query) == None:
                disabled_devices_col.insert_one(device_query)
        else:
            disabled_devices_col = self.db["disabled_devices"]
            disabled_devices_col.insert_one(device_query)

    def remove_disabled_device(self, device):
        if "disabled_devices" in self.db.list_collection_names():
            disabled_devices_col = self.db["disabled_devices"]
            device_query = {"name" : device}

            disabled_devices_col.delete_one(device_query)

    def get_all_disabled_devices(self):
        response = []
        if "disabled_devices" in self.db.list_collection_names():
            for d in self.db["disabled_devices"].find({}):
                response.append(d["name"])
            
        return response

    def set_common_config(self, common_config):
        if "config" in self.db.list_collection_names():
            commonConfig = self.db["config"]
            commonConfig.drop()

        commonConfig = self.db["config"]
        commonConfig.insert_one(common_config)

    def get_common_config(self):
        if "config" in self.db.list_collection_names():
            return self.db["config"].find_one({})

        return None

    def set_google_calendar(self, calendar_id):
        if "google_calendar" in self.db.list_collection_names():
            googleCalendar = self.db["google_calendar"]
            googleCalendar.drop()

        googleCalendar = self.db["google_calendar"]
        googleCalendar.insert_one({
            "calendar_id": calendar_id
        })

    def get_google_calendar(self):
        if "google_calendar" in self.db.list_collection_names():
            googleCalendar = self.db["google_calendar"].find_one({})
            if "calendar_id" in googleCalendar:
                return googleCalendar["calendar_id"]

        return ""

    def set_twilio_account(self, notify_phone_number, twilio_number, twilio_sid, twilio_auth_token):
        if "twilio_account" in self.db.list_collection_names():
            twilioAccount = self.db["twilio_account"]
            twilioAccount.drop()

        twilioAccount = self.db["twilio_account"]
        twilioAccount.insert_one({
            "notify_phone_number": twilio_number,
            "twilio_number": twilio_number,
            "twilio_sid": base64.b64encode(twilio_sid.encode('ascii')),
            "twilio_auth_token": base64.b64encode(twilio_auth_token.encode('ascii'))
        })

    def get_twilio_account(self):
        if "twilio_account" in self.db.list_collection_names():
            return self.db["twilio_account"].find_one({})
        
        return None

    def set_router_account(self, username, password):
        if "router_account" in self.db.list_collection_names():
            routerAccount = self.db["router_account"]
            routerAccount.drop()

        routerAccount = self.db["router_account"]
        routerAccount.insert_one({
            "user": username,
            "password": base64.b64encode(password.encode('ascii'))
        })

    def get_router_account(self):
        if "router_account" in self.db.list_collection_names():
            return self.db["router_account"].find_one({})

        return None

    def set_garmin_account(self, username, password):
        if "garmin_account" in self.db.list_collection_names():
            garminAccount = self.db["garmin_account"]
            garminAccount.drop()

        garminAccount = self.db["garmin_account"]
        garminAccount.insert_one({
            "email": username,
            "password": base64.b64encode(password.encode('ascii'))
        })

    def get_garmin_account(self):
        if "garmin_account" in self.db.list_collection_names():
            return self.db["garmin_account"].find_one({})

        return None

    def init(self):
        self.mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.mongo_client["2FAt"]

mongoConfig = MongoConfigDB()
mongoConfig.init()

class activity_monitor():
    def toggle_network(self, denyallow, mac, message):
        twilioConfig = mongoConfig.get_twilio_account()
        routerConfig = mongoConfig.get_router_account()

        if routerConfig == None:
            print("[ERROR] No valid router configuration provided! Can't toggle network.")
            return

        netgear = Netgear(
            password=base64.b64decode(routerConfig['password']).decode('utf-8'),
            user=routerConfig['user'])
        
        notify_phone_number = ''
        if 'notify_phone_number' in twilioConfig:
            notify_phone_number = twilioConfig['notify_phone_number']

        print('Toggling Network {} to {}'.format(mac, denyallow))
        if self.is_mac_address(mac):
            netgear.allow_block_device(mac_addr=mac, device_status=denyallow)
        else:
            profile = mongoConfig.get_profile(mac)
            if profile != None:
                if "devices" in profile:
                    for device in profile['devices']:
                        netgear.allow_block_device(mac_addr=device, device_status=denyallow)

                        if "notify_phone_number" in profile:
                            notify_phone_number = profile['notify_phone_number']
            else:
                print("[ERROR] No matching profile for {}, can't toggle devices!".format(mac))
                return

        disabled_devices = mongoConfig.get_all_disabled_devices()
        if denyallow == "Block" and mac not in disabled_devices:
            if message != '' and twilioConfig['twilio_number']:
                if 'account_sid' in twilioConfig:
                    twilioClient = Client(base64.b64decode(twilioConfig['account_sid']), base64.b64decode(twilioConfig['auth_token']))

                    twilioClient.messages.create(
                        from_=twilioConfig['twilio_number'],
                        to=notify_phone_number,
                        body=message
                    )

            mongoConfig.insert_disabled_device(mac)
        
        if denyallow == "Allow" and mac in disabled_devices:
            if message != '' and twilioConfig['twilio_number']:
                twilioClient.messages.create(
                    from_=twilioConfig['twilio_number'],
                    to=notify_phone_number,
                    body='Hooray!  {}'.format(message)
                )

            mongoConfig.remove_disabled_device(mac)

    def validate_steps(self, required_steps, mac):
        today = date.today()

        client = self.init_garmin_client()
        if client == None:
            print("[ERROR] Unable to validate steps, no Garmin Client available!")
            return

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

    def validate_stats(self, stat, required_value, mac):
        today = date.today()

        client = self.init_garmin_client()
        if client == None:
            print("[ERROR] Unable to validate steps, no Garmin Client available!")
            return

        value = 0
        try:
            stats = client.get_stats(today.isoformat())
            value = stats[stat]
        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
        ) as err:
            print("[ERROR] Error occurred during Garmin Connect Client get steps data: %s" % err)
            return
        except Exception:  # pylint: disable=broad-except
            print("[ERROR] Unknown error occurred during Garmin Connect Client get steps data")
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

        calendar_id = mongoConfig.get_google_calendar()
        if calendar_id == "":
            print("[ERROR] No valid Google Calendar ID, can't get schedule!")
            return []

        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(calendarId=calendar_id, timeMin=now,
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
        
    def process_command(self, command, param, mac):
        print('Handling {} ({}) for {}'.format(command, param, mac))

        if command == "TOGGLE":
            self.toggle_network(param, mac, "")
        elif command == "STEPS":
            self.validate_steps(param, mac)
        elif command == "STATS":
            parts = str.split(param, '=')
            if len(parts) == 2:
                self.validate_stats(parts[0], int(parts[1]), mac)
            else:
                print("[ERROR] Invalid format for STATS parameter ({}) expected <stat>=<value>!".format(param))

    def is_mac_address(self, name):
        if len(str.split(name, ':')) == 6:
            return True
        else:
            return False

    def check_activity(self):
        events = self.get_active_events()
        found_mac = []
        for event in events:
            parts = str.split(event, ';')
            if len(parts) == 3:
                self.process_command(parts[0], parts[1], parts[2])
                found_mac.append(parts[2])
        
        disabled_devices = mongoConfig.get_all_disabled_devices()

        # Enable any expired disablements
        for d in disabled_devices:
            if d not in found_mac:
                self.toggle_network('Allow', d, '')
        
    def init_garmin_client(self):
        garminAccount = mongoConfig.get_garmin_account()
        if garminAccount == None:
            print("[ERROR] No valid Garmin Account configured! Can't get Activity.")
            return None

        try:
            client = Garmin(garminAccount['email'], base64.b64decode(garminAccount['password']))
        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
        ) as err:
            print("[ERROR] During Garmin Connect Client init: %s" % err)
            return None
        except Exception:  # pylint: disable=broad-except
            print("[ERROR] Unknown error occurred during Garmin Connect Client init")
            return None

        try:
            client.login()
        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
        ) as err:
            print("[ERROR] Error occurred during Garmin Connect Client login: %s" % err)
            return None
        except Exception:  # pylint: disable=broad-except
            print("[ERROR] Unknown error occurred during Garmin Connect Client login")
            return None

        return client

    def run(self):
        mongoConfig.update_profile("Justin", [
                "DC:44:27:1D:2C:A2"
            ],
            "+13149568019"
        )
        
        while True:
            self.check_activity()

            refresh = 600
            common = mongoConfig.get_common_config()
            if common != None:
                if 'refresh_time_sec' in common:
                    refresh = common['refresh_time_sec']

            print('Sleep {} seconds before next check...'.format(refresh))
            time.sleep(refresh)

def main():
    monitor_task = activity_monitor()
    monitor_task.run()

if __name__ == '__main__':
    main()
