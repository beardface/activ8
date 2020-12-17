# ACTIV8
This repository allows you to disable network access to any devices if you don't meet an activity goal for a time period.

For example, if you **wanted to turn off your internet to your Desktop or Mobile unless you've gotten a certain number of steps for the day...** this will do that for you.

**Want to require a certain number of high activity (running / cycling / rowing)?** Done.

**Want to reach a certain maximum heartbeat to turn on access to the internet?** You got it.

**Staying up too late and want your device's internet to shut off per a scheduled calendar event?** Yep.

<img src="https://github.com/beardface/activ8/blob/main/main.png?raw=true" width="500">

## How does it work?
This works by integrating with Garmin Connect to get your activity, and your nighthawk router to remotely control devices by MAC address.

To set up time periods for device control, you create a Google Calendar and add events that correlate with control of those devices.

**Supported Commands:**
* `TOGGLE` - This will take a param of `Allow` or `Block` to turn on or off internet access during a time period to devices
* `STEPS` - This command takes a parameter (int) of the number of steps required for the day to avoid disabling internet access.
* `STATS` - This provides the ability to pull from additional Garmin Connect Stats to gate connectivity:
Format <stat>=<value> (`ex. totalKilocalories=1000` would require a totalKilocalories (burnt calories) greater than 1000 to enable a device)

| Statistic | Description | Type |
| --------- | ----------- | ---- |
| totalKilocalories |  | int |
| activeKilocalories | Active kilocalories (dietary calories) burned through actual movement and activity during the monitoring period. | int |
| bmrKilocalories | BMR Kilocalories burned by existing Basal Metabolic Rate (calculated based on user height/weight/age/other demographic data) | int |
| totalSteps | Count of steps recorded during the monitoring period.  | int |
| totalDistanceMeters | Distance traveled in meters. | int |
| highlyActiveSeconds |  Portion of the monitoring period (in seconds) in which the device wearer was considered Highly Active. This relies on heuristics internal to each device. | int |
| activeSeconds | Portion of the monitoring period (in seconds) in which the device wearer was considered Active. This relies on heuristics internal to each device. | int |
| moderateIntensityMinutes | Cumulative duration of activities of moderate intensity, lasting at least 600 seconds at a time. Moderate intensity is defined as activity with MET (resting metabolic rate) value range 3-6 | int |
| vigorousIntensityMinutes | Cumulative duration of activities of vigorous intensity, lasting at least 600 seconds at a time. Vigorous intensity is defined as activity with MET (resting metabolic rate) value > 6 | int |
| maxHeartRate | Maximum of heart rate values captured during the monitoring period, in beats per minute | int |

## Twilio
You can add a twilio account to configuration to get a text message when your device is being disabled due to failing your fitness goals.

<img src="https://github.com/beardface/activ8/blob/main/twilio.jpg?raw=true" width="300">

### Building
```
# Backend
docker build .
docker tag <hash> activ8/backend:<version>
docker push activ8/backend:<version>
```

```
# Frontemd
cd frontend
docker build .
docker tag <hash> activ8/frontend:<version>
docker push activ8/frontend:<version>
```

## Installing / Setting up
1. Flash Berry Lan on a Raspberry Pi Zero and Connect the WiFi
http://berrylan.org/

2. Install Docker
ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no pi@raspberrypi.local

`sudo apt-get update && sudo apt-get upgrade`

# Install Docker on Raspberry Pi
```
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker pi
sudo reboot
```

3. Log back in and Start Containers

# Create Network
`docker network create internal-activ8-network`

# Start Mongo
```
docker run -d \
--name rpi3-mongodb3 \
--restart unless-stopped \
-v /data/db:/data/db \
-v /data/configdb:/data/configdb \
-p 27017:27017 \
-p 28017:28017 \
--network internal-activ8-network \
andresvidal/rpi3-mongodb3:latest \
mongod
```

# Start Backend
```
docker run -d \
--name activ8-backend \
--restart unless-stopped \
-e MONGO_HOST=rpi3-mongodb3 \
--network internal-activ8-network \
activ8/backend:0.0.3
```

# Start Frontend
```
docker run -d \
--name activ8-frontend \
--restart unless-stopped \
--network internal-activ8-network \
-e MONGO_HOST=rpi3-mongodb3 \
-p 80:80 \
activ8/frontend:0.0.3
```

4. You're done!
On your local network, head to [http://raspberrypi.local](http://raspberrypi.local) to configure
