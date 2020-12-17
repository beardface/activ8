import base64
import pymongo
import os

from datetime import datetime, timedelta, date, time
import calendar

class MongoConfigDB:
    def update_profile(self, profile_name, devices, notify_phone_number, garmin_username, garmin_password, google_calendar_id):
        profile_query = {"name": profile_name}
        
        if "profiles" in self.db.list_collection_names():
            profiles_col = self.db["profiles"]

            profiles_col.delete_one(profile_query)

            profile_data = {
                "name": profile_name,
                "devices": devices,
                "notify_phone_number": notify_phone_number,
                "google_calendar_id": google_calendar_id,
                "garmin_username": garmin_username,
                "garmin_password": base64.b64encode(garmin_password.encode('ascii'))
            }
            profiles_col.insert_one(profile_data)
        else:
            profiles_col = self.db["profiles"]
            profiles_col.insert_one(profile_query)

    def update_profile_steps(self, profile_name, steps):
        profile_query = {"name": profile_name}
        
        if "profiles" in self.db.list_collection_names():
            profiles_col = self.db["profiles"]

            profile_data =  {"$set": {
                "name": profile_name,
                "steps": steps,
            }}
            profiles_col.find_one_and_update(profile_query, profile_data)

    def update_profile_stats(self, profile_name, blocked, last_checked_time):
        profile_query = {"name": profile_name}
        
        if "profiles" in self.db.list_collection_names():
            profiles_col = self.db["profiles"]

            profile_data = {"$set": {
                "name": profile_name,
                "blocked": blocked,
                "last_checked_time": last_checked_time
            }}
            profiles_col.find_one_and_update(profile_query, profile_data)

    def get_profiles(self):
        profiles = []
        if "profiles" in self.db.list_collection_names():
            for profile in self.db["profiles"].find({}):
                profiles.append(profile)

        return profiles

    def get_profile(self, profile_name):
        profile_query = {"name": profile_name}
        if "profiles" in self.db.list_collection_names():
            profile = self.db["profiles"].find_one(profile_query)
            return profile
        
        return None

    def update_all_devices(self, devices):
        if "all_devices" in self.db.list_collection_names():
            all_devices_col = self.db["all_devices"]
            all_devices_col.drop()
        
        all_devices_col = self.db["all_devices"]
        for d in devices:
            all_devices_col.insert_one(d)

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

    def is_between(time, time_range):
        if time_range[1] < time_range[0]:
            return time >= time_range[0] or time <= time_range[1]
        return time_range[0] <= time <= time_range[1]

    def get_active_user_events(self, profile_name):
        events = []

        my_date = date.today()
        today = calendar.day_name[my_date.weekday()]
         
        if "events" in self.db.list_collection_names():
            for e in self.db["events"].find({"user": profile_name}):
                if today in e['days']:
                    now = datetime.now()

                    current_time = now.strftime("%H:%M:%S")
                    sH,sM,sS = e['start_time'].split(':')
                    eH,eM,eS = e['end_time'].split(':')
                    nH,nM,nS = current_time.split(':')
                    if time(int(sH), int(sM), int(sS)) <  time(int(nH),int(nM),int(nS)) < time(int(eH),int(eM),int(eS)):
                        events.append(e)
            
        return events

    def set_common_config(self, common_config):
        if "config" in self.db.list_collection_names():
            commonConfig = self.db["config"]
            commonConfig.drop()

        commonConfig = self.db["config"]
        commonConfig.insert_one(common_config)

    def set_next_update_time(self, update_time):
        if "config" in self.db.list_collection_names():
            commonConfig = self.db["config"]
            commonConfig.update_one({}, {"$set": {"next_update_time": update_time}})

    def get_common_config(self):
        if "config" in self.db.list_collection_names():
            return self.db["config"].find_one({})

        return None

    def get_twilio_account(self):
        if "twilio_account" in self.db.list_collection_names():
            return self.db["twilio_account"].find_one({})
        
        return None

    def get_router_account(self):
        if "router_account" in self.db.list_collection_names():
            return self.db["router_account"].find_one({})

        return None

    def debug_log(self, log):
        logs_message = {"message" : log, "timestamp": datetime.now()}

        if "logs" in self.db.list_collection_names():
            logs_col = self.db["logs"]

            logs_col.insert_one(logs_message)
        else:
            logs_col = self.db["logs"]
            logs_col.insert_one(logs_message)

        self.db["logs"].remove(
            { 
                "timestamp" : {"$lt" : datetime.now() - timedelta(minutes = 30)}
            }
        )

    def init(self):
        mongo_host = "localhost"
        if os.getenv("MONGO_HOST") != None:
            print(os.getenv("MONGO_HOST"))
            mongo_host = os.getenv("MONGO_HOST")
        self.mongo_client = pymongo.MongoClient("mongodb://{}:27017/".format(mongo_host))
        self.db = self.mongo_client["activ8"]