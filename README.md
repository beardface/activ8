# ACTIV8
This repository allows you to disable network access to any devices if you don't meet an activity goal for a time period.

For example, if you **wanted to turn off your internet to your Desktop or Mobile unless you've gotten a certain number of steps for the day...** this will do that for you.

<img src="https://github.com/beardface/activ8/blob/main/main.png?raw=true" width="700">

## How does it work?
This works by integrating with Garmin Connect to get your activity, and your nighthawk router to remotely control devices by MAC address.

To set up time periods for device control, you create a Google Calendar and add events that correlate with control of those devices.

<img src="https://github.com/beardface/activ8/blob/main/how.png?raw=true" width="700">

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
