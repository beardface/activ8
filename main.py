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

import os.path

from datetime import date, datetime, timezone, timedelta

import time

from twilio.rest import Client

import requests
from urllib3.exceptions import InsecureRequestWarning

import mongo_client
# import faunadb_client

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# database = faunadb_client.FaunaDBConfig()
# database.init()
database = mongo_client.MongoConfigDB()
database.init()

class activity_monitor():
    def debug(self, message):
        print(message)
        database.debug_log(message)

    def refresh_all_devices(self):
        common_config = database.get_common_config()

        if "router_username" not in common_config or "router_password" not in common_config:
            self.debug("[ERROR] No valid router configuration provided! Can't toggle network.")
            return

        netgear = Netgear(
            password=base64.b64decode(common_config['router_password']).decode('utf-8'),
            user=common_config['router_username'])
        
        cached_devices = []
        devices = netgear.get_attached_devices()
        if devices != None:
            self.debug("[INFO] Successfully connected to router, found {} attached devices.".format(len(devices)))
            for device in devices:
                d = {
                    "name": device.name,
                    "ip": device.ip,
                    "mac": device.mac,
                    "type": device.type,
                }
                cached_devices.append(d)
            database.update_all_devices(cached_devices)
        else:
            self.debug("[ERROR] Unable to get devices from the router, check credentials!")


    def toggle_network(self, denyallow, profile, message):
        common_config = database.get_common_config()

        if "router_username" not in common_config or "router_password" not in common_config:
            self.debug("[ERROR] No valid router configuration provided! Can't toggle network.")
            return False

        netgear = Netgear(
            password=base64.b64decode(common_config['router_password']).decode('utf-8'),
            user=common_config['router_username'])
        
        notify_phone_number = ''
        if 'notify_phone_number' in profile:
            notify_phone_number = profile['notify_phone_number']

        self.debug('[INFO] Toggling Network {} to {}'.format(profile["name"], denyallow))
        if profile != None:
            if "devices" in profile:
                for device in profile['devices']:
                    netgear.allow_block_device(mac_addr=device, device_status=denyallow)
        else:
            self.debug("[ERROR] No profile provided, can't toggle devices!")
            return False

        disabled_devices = database.get_all_disabled_devices()
        if denyallow == "Block" and profile["name"] not in disabled_devices:
            if message != '' and common_config['twilio_number']:
                if 'twilio_sid' in common_config:
                    twilioClient = Client(base64.b64decode(common_config['twilio_sid']).decode("utf-8"), base64.b64decode(common_config['twilio_auth_token']).decode("utf-8"))
                    twilioClient.messages.create(
                        from_=common_config['twilio_number'],
                        to=notify_phone_number,
                        body=message
                    )

            database.insert_disabled_device(profile["name"])
            return True
        
        if denyallow == "Allow" and profile["name"] in disabled_devices:
            if message != '' and common_config['twilio_number']:
                twilioClient = Client(base64.b64decode(common_config['twilio_sid']).decode("utf-8"), base64.b64decode(common_config['twilio_auth_token']).decode("utf-8"))
                twilioClient.messages.create(
                    from_=common_config['twilio_number'],
                    to=notify_phone_number,
                    body='Hooray!  {}'.format(message)
                )

            database.remove_disabled_device(profile["name"])
            return False

    def validate_steps(self, required_steps, profile):
        today = date.today()

        client = self.init_garmin_client(profile)
        if client == None:
            self.debug("[ERROR] Unable to validate steps, no Garmin Client available!")
            return False

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
            self.debug("[ERROR] Error occurred during Garmin Connect Client get steps data: %s" % err)
            return False
        except Exception:  # pylint: disable=broad-except
            self.debug("[ERROR] Unknown error occurred during Garmin Connect Client get steps data")
            return False
        
        database.update_profile_steps(profile["name"], all_steps)
        if all_steps >= int(required_steps):
            msg = 'You\'ve taken {} steps, which is greater than the required {}! Enabling your device ({})!'.format(all_steps, required_steps, profile["name"])
            self.debug('[INFO] Sending: {}'.format(msg))
            return self.toggle_network('Allow', profile, msg)
        else:
            msg = 'Oh No! You\'ve only taken {} steps, which is less than the required {}! Disabling your device ({}) until you take care of business!'.format(all_steps, required_steps, profile["name"])
            self.debug('[INFO] Sending: {}'.format(msg))
            return self.toggle_network('Block', profile, msg)

    def validate_stats(self, stat, required_value, profile):
        today = date.today()

        client = self.init_garmin_client(profile)
        if client == None:
            self.debug("[ERROR] Unable to validate steps, no Garmin Client available!")
            return False

        value = 0
        try:
            stats = client.get_stats(today.isoformat())
            value = stats[stat]
        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
        ) as err:
            self.debug("[ERROR] Error occurred during Garmin Connect Client get steps data: %s" % err)
            return False
        except Exception:  # pylint: disable=broad-except
            self.debug("[ERROR] Unknown error occurred during Garmin Connect Client get steps data")
            return False
        
        if value >= int(required_value):
            msg = 'Value in Garmin Connect for {} was {}, which is greater than the required {}! Enabling your device ({})!'.format(stat, value, required_value, profile["name"])
            self.debug('[INFO] Sending: {}'.format(msg))
            return self.toggle_network('Allow', profile, msg)
        else:
            msg = 'Oh No! Value in Garmin Connect for {} was {}, which is less than the required {}! Disabling your device ({}) until you take care of business!!'.format(stat, value, required_value, profile["name"])
            self.debug('[INFO] Sending: {}'.format(msg))
            return self.toggle_network('Block', profile, msg)

    def time_in_range(self, start, end, time):
        if end < start:
            return time >= start or time <= end
        return start <= time <= end
        
    def process_command(self, event, profile):
        print('Handling {}: {} ({}) for {}'.format(event['title'], event['activity'], event['value'], profile["name"]))

        if event['activity'] == "TOGGLE":
            return self.toggle_network(event['value'], profile, "")
        elif event['activity'] == "STEPS":
            return self.validate_steps(event['value'], profile)
        elif event['activity'] == "STATS":
            return self.validate_stats(event['stat'], event['value'], profile)

    def is_mac_address(self, name):
        if len(str.split(name, ':')) == 6:
            return True
        else:
            return False

    def check_activity(self, profile):
        events = database.get_active_user_events(profile['name'])
        block_found = False
        for event in events:
            res = self.process_command(event, profile)
            if res:
                block_found = True
        
        database.update_profile_stats(profile["name"], block_found, datetime.now())
        return block_found
        
    def init_garmin_client(self, profile):
        if "garmin_username" not in profile or "garmin_password" not in profile:
            self.debug("[ERROR] No valid Garmin Account configured! Can't get Activity.")
            return None

        try:
            client = Garmin(profile['garmin_username'], base64.b64decode(profile['garmin_password']))
        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
        ) as err:
            self.debug("[ERROR] During Garmin Connect Client init: %s" % err)
            return None
        except Exception:  # pylint: disable=broad-except
            self.debug("[ERROR] Unknown error occurred during Garmin Connect Client init")
            return None

        try:
            client.login()
        except (
            GarminConnectConnectionError,
            GarminConnectAuthenticationError,
            GarminConnectTooManyRequestsError,
        ) as err:
            self.debug("[ERROR] Error occurred during Garmin Connect Client login: %s" % err)
            return None
        except Exception:  # pylint: disable=broad-except
            self.debug("[ERROR] Unknown error occurred during Garmin Connect Client login")
            return None

        return client

    def run(self):
        while True:
            update = False
            refresh = 600
            common = database.get_common_config()
            if common != None:
                if 'refresh_time_sec' in common:
                    refresh = common['refresh_time_sec']

                if 'next_update_time' in common:
                    if common['next_update_time'] < datetime.utcnow():
                        update = True
                else:
                    update = True
            else:
                database.set_common_config({
                    "refresh_time_sec": refresh,
                    "next_update_time": datetime.utcnow() + timedelta(seconds=refresh)
                })
                update = True

            if update:
                self.refresh_all_devices()

                self.debug("[INFO] Processing activity for Users Now...")
                found_disabled_profiles = []
                for profile in database.get_profiles():
                    if self.check_activity(profile):
                        found_disabled_profiles.append(profile['name'])

                self.debug("[INFO] Sleeping 30 seconds before processing networks to allow...")
                time.sleep(30)
                disabled_devices = database.get_all_disabled_devices()

                # Enable any expired disablements
                for d in disabled_devices:
                    if d not in found_disabled_profiles:
                        self.debug("[INFO] Re-enabling {} as it is disabled, but not in the registered disabled devices: {} (found: {})".format(
                            d, disabled_devices, found_disabled_profiles))
                        self.toggle_network('Allow', database.get_profile(d), '')

                database.set_next_update_time(datetime.utcnow() + timedelta(seconds=int(refresh)))
            else:
                time.sleep(5)

def main():
    monitor_task = activity_monitor()
    monitor_task.run()

if __name__ == '__main__':
    main()
