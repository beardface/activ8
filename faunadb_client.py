from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient

import base64
import os

class FaunaDBConfig:
    def update_profile_steps(self, ref, steps):
        self.fauna_client.query(
            q.update(
                ref,
                { "data": {"steps": steps}}
            )
        )

    def update_profile_stats(self, ref, blocked):
        self.fauna_client.query(
            q.update(
                ref,
                {
                    "data": {
                        "blocked": blocked,
                        "last_checked_time": q.now()
                    }
                }
            )
        )

    def get_profiles(self):
        profiles = []
        
        try:
            res = self.fauna_client.query(
                q.map_(
                    q.lambda_(
                        ["name", "google_calendar_id", "garmin_username", "garmin_password", "notify_phone_number", "ref"],
                        {
                            "name": q.var("name"),
                            "google_calendar_id": q.var("google_calendar_id"),
                            "garmin_username": q.var("garmin_username"),
                            "garmin_password": q.var("garmin_password"),
                            "notify_phone_number": q.var("notify_phone_number"),
                            "ref": q.var("ref")
                        }                
                    ),
                    q.paginate(q.match(q.index('profiles_list_all'))),
            )
            )

            for data in res['data']:
                profiles.append(data)

            return profiles
        except Exception as e:
            print('Unable to get profiles: {}'.format(e))
            return []

    def get_profile(self, profile_id):
        try:
            res = self.fauna_client.query(
                q.get(
                    q.ref(
                        q.collection('profiles'), profile_id
                    )
                )
            )

            return res['data']
        except Exception as e:
            print('Unable to get profile: {}'.format(e))
            return None

    def update_all_devices(self, devices):
        try:
            res = self.fauna_client.query(
                q.map_(
                    lambda device: q.create(
                        q.ref(q.collection("all_devices"), device['mac']),
                        {"data": {
                            "name": device['name'],
                            "ip": device['ip'],
                            "mac": device['mac']
                            }
                        }
                    ),
                    devices
                )
            )

            print(res)
        except Exception as e:
            print('Unable to update all devices: {}'.format(e))
            return None

    def insert_disabled_device(self, device):
        self.fauna_client.query(
            q.insert(
                q.ref(q.collection('disabled_devices'), device),
                {
                    "data": {"name": device}
                }
            )
        )

    def remove_disabled_device(self, device):
        self.fauna_client.query(
            q.delete(
                q.ref(q.collection('disabled_devices'), device)
            )
        )

    def get_all_disabled_devices(self):
        disabled_devices = []
        
        try:
            res = self.fauna_client.query(
                q.map_(
                    q.lambda_(
                        ["name", "mac", "ip", "ref"],
                        {
                            "name": q.var("name"),
                            "mac": q.var("mac"),
                            "ip": q.var("ip"),
                            "ref": q.var("ref")
                        }                
                    ),
                    q.paginate(q.match(q.index('disabled_devices_list_all'))),
            )
            )

            for data in res['data']:
                disabled_devices.append(data)

            return disabled_devices
        except Exception as e:
            print('Unable to get disabled devices: {}'.format(e))
            return []

    def set_common_config(self, common_config):
        self.fauna_client.query(
            q.update(
                q.ref(q.collection("config"), 1),
                { "data": common_config}
            )
        )

    def set_next_update_time(self, update_time):
        self.fauna_client.query(
            q.update(
                q.ref(q.collection("config"), 1),
                { "data": {"next_update_time": update_time}}
            )
        )

    def get_common_config(self):
        res = self.fauna_client.query(
            q.get(
                q.ref(
                    q.collection('config'), '1'
                )
            )
        )

        return res["data"]


    def init(self):
        self.fauna_client = FaunaClient(secret=os.environ.get('FAUNADB_API_KEY'))