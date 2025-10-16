# After Work Weather Alert for Biking

Checks if it's going to rain so I know whether to bike home from work or not.

## What does this do?

I bike around Singapore after work, but I hate getting caught in the rain. This script checks NEA's weather forecast for my usual routes and pings me on Telegram + desktop notification around 5:30pm.

It only bugs me once per day, even if my WiFi keeps reconnecting.

## Setup

### Install stuff

```bash
sudo apt install python3-requests libnotify-bin
```

### Telegram bot setup

You need a Telegram bot to receive messages:

1. Message `@BotFather` on Telegram
2. Send `/newbot` and pick a name
3. Copy the token it gives you
4. Message your new bot (just say hi or whatever)
5. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in your browser
6. Look for `"chat":{"id":123456789}` - that's your chat ID

### Config file

Make a file called `weather_config.ini` in the same folder as the script:

```ini
[telegram]
bot_token = your_bot_token_here
chat_id = your_chat_id_here
```

Then lock it down:
```bash
chmod 600 weather_config.ini
```

### Auto-run on WiFi reconnect

This is the part that makes it automatic. When your WiFi connects, it triggers the script.

```bash
sudo nano /etc/NetworkManager/dispatcher.d/99-weather-check
```

Paste this (change `alann` and the path to match yours):

```bash
#!/bin/bash

if [ "$2" = "up" ]; then
    su - alann -c "cd /home/alann/path/to/script && /usr/bin/python3 /home/alann/path/to/script/rain_check.py >> /tmp/weather.log 2>&1"
fi
```

Make it executable:
```bash
sudo chmod +x /etc/NetworkManager/dispatcher.d/99-weather-check
```

## How to use it

Just leave it running. When you reconnect WiFi after 5:30pm, you'll get a notification showing the weather for all your areas.

To test it manually:
```bash
python3 rain_check.py
```

## What areas does it check?

Right now: Tampines, City (MBS area), Paya Lebar, Jurong East, Punggol, Woodlands, Yishun, Queenstown

Edit `MONITORED_AREAS` in the script to change this.

## Troubleshooting

**Nothing's happening?**

Check the log:
```bash
cat /tmp/weather.log
```

**Getting spammed with notifications?**

Check if it's recording runs:
```bash
cat ~/.weather_last_run.txt
```

Should show today's date if it ran already.

**Want to force it to run again?**
```bash
rm ~/.weather_last_run.txt
```

**Dispatcher script not triggering?**

Make sure it exists and is executable:
```bash
ls -l /etc/NetworkManager/dispatcher.d/99-weather-check
```

## How it works

1. Only runs after 5:30pm
2. Checks if it already ran today (if yes, quits silently)
3. Grabs weather from NEA's API
4. Looks for rain keywords: "Showers", "Rain", "Thundery"
5. Sends notification if rain detected
6. Saves today's date so it won't spam you

## Customizing

- **Different areas**: Edit `MONITORED_AREAS` list
- **Different time**: Change the hour/minute check (look for `current_hour < 17`)
- **Different rain detection**: Edit `BAD_WEATHER` keywords

## Notes

Don't commit `weather_config.ini` to git. Add it to `.gitignore`:
```bash
echo "weather_config.ini" > .gitignore
```

Weather data from [NEA via data.gov.sg](https://data.gov.sg)