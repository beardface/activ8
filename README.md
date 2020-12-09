# 2FAt.club
This repository allows you to disable network access to any devices if you don't meet an activity goal for a time period.

For example, if you wanted to turn off your internet to your Desktop or Mobile unless you've gotten a certain number of steps for the day... this will do that for you.

## How does it work?
This works by integrating with Garmin Connect to get your activity, and your nighthawk router to remotely control devices by MAC address.

To set up time periods for device control, you create a Google Calendar and add events that correlate with control of those devices.

## Syntax for Control on Google Calendar
The syntax for control on the calendar is:
`<COMMAND>;<PARAM>;<MAC ADDRESS>`

Supported Commands:
* TOGGLE - This will take a param of `Allow` or `Block` to turn on or off internet access during a time period to devices
* STEPS - This command takes a parameter (int) of the number of steps required for the day to avoid disabling internet access.
* STATS - This provides the ability to pull from additional Garmin Connect Stats to gate connectivity:
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

## Configuration
To configure this repository, you need to create a `config.json` file that has the credentials for the router and your garmin connect account, as well as the google calendar ID.  (See `config.json.template`)

You'll also need to place a `credentials.json` file in the folder that enables you to connect to the Google Calendar API. [here](https://developers.google.com/calendar/quickstart/go)
