#!/usr/bin/env python3
"""
After Work Rain Alert

This script checks the NEA weather forecast for specific areas in Singapore
and sends you notifications (desktop + Telegram) if rain is coming.

It only runs after 5:30pm to help decide if it's safe to bike home.
"""

import requests          # For making HTTP requests to APIs (getting weather data)
import subprocess        # System commands for desktop notifications
import configparser      # Telegram bot credentials
import os                # For file path operations
from datetime import datetime  # For working with dates and times

# The URL of NEA's weather API endpoint
# This is a public API that returns SG's weather forecasts in JSON format
API_URL = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"

# File to track when we last ran the script (prevents spam)
# Stored in home directory as a hidden file
LAST_RUN_FILE = os.path.expanduser("~/.weather_last_run.txt")

# List of Singapore areas I am monitoring
# These must match the exact names NEA uses in their API
MONITORED_AREAS = [
    "Tampines",
    "City",        # This covers Marina Bay/MBS area
    "Paya Lebar",
    "Jurong East",
    "Punggol",
    "Woodlands",
    "Yishun",
    "Queenstown"
]

BAD_WEATHER = ["Showers", "Rain", "Thundery"]

def get_weather():
    """
    Fetches weather data from NEA's API.
    
    How it works:
    1. Sends an HTTP GET request to NEA's API
    2. NEA responds with JSON data containing weather forecasts
    3. We convert that JSON into a Python dictionary
    
    Returns:
        dict: Weather data with all areas and their forecasts
    """
    response = requests.get(API_URL)  # Make HTTP request
    return response.json()            # Convert JSON response to Python dict

def check_already_ran_today():
    """
    Checks if the script already ran today to prevent spam.
    
    How it works:
    1. Tries to read the last run date from a file
    2. Compares it with today's date
    3. Returns True if already ran today, False otherwise
    
    Returns:
        bool: True if already ran today, False otherwise
    """
    today = datetime.now().strftime('%Y-%m-%d')  # Get today's date (e.g., "2025-10-16")
    
    # Check if the tracking file exists
    if os.path.exists(LAST_RUN_FILE):
        # Read the last run date from the file
        with open(LAST_RUN_FILE, 'r') as f:
            last_run_date = f.read().strip()  # Remove any whitespace
        
        # If last run was today, we already ran
        if last_run_date == today:
            return True
    
    # Either file doesn't exist or last run was a different day
    return False

def update_last_run():
    """
    Updates the last run file with today's date.
    
    This marks that we successfully ran today, so we won't run again
    until tomorrow.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Write today's date to the file
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(today)

def send_telegram(message):
    """
    Sends a message to your Telegram account via your bot.
    
    How it works:
    1. Reads your bot token and chat ID from the config file
    2. Constructs the Telegram API URL with your bot token
    3. Sends a POST request to Telegram with your message
    
    Args:
        message (str): The text message to send
    """
    # Read credentials from the config file
    config = configparser.ConfigParser()
    config.read('weather_config.ini')  # Looks for file in same directory
    
    # Extract bot token and chat ID from the [telegram] section
    bot_token = config['telegram']['bot_token']
    chat_id = config['telegram']['chat_id']
    
    # Build the Telegram API URL
    # Format: https://api.telegram.org/bot<TOKEN>/sendMessage
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Prepare the message data
    # chat_id = who to send to, text = the message content
    data = {"chat_id": chat_id, "text": message}
    
    # Send the message via HTTP POST request
    try:
        requests.post(url, data=data)
    except:
        # If Telegram fails (no internet, etc.), just silently continue
        # This prevents the script from crashing if Telegram is unreachable
        pass

def show_notification(title, message):
    """
    Shows a desktop notification popup on Ubuntu.
    
    How it works:
    Uses the 'notify-send' system command to display a notification.
    The -t parameter sets how long (milliseconds) to display it.
    
    Args:
        title (str): Notification title (bold text at top)
        message (str): Notification body (main text)
    """
    try:
        # Run the notify-send command
        # -t 15000 = show for 15 seconds (15000 milliseconds)
        subprocess.run(["notify-send", "-t", "15000", title, message])
    except:
        # If notify-send isn't installed, silently continue
        pass

def main():
    """
    Main function that orchestrates the entire weather check process.
    
    Process flow:
    1. Check if it's after 5:30pm (only run during biking hours)
    2. Check if we already ran today (prevent spam)
    3. Fetch weather data from NEA API
    4. Filter data to only your monitored areas
    5. Check if any area has bad weather (rain keywords)
    6. Send notifications via desktop + Telegram
    7. Mark that we ran today
    """
    
    # STEP 1: Time Check - Only run after 5:30pm
    
    current_hour = datetime.now().hour      # Get current hour (0-23)
    current_minute = datetime.now().minute  # Get current minute (0-59)
    
    # Check if it's before 5:30pm
    # Logic: If hour < 17 (before 5pm) OR (hour is 17 but minute < 30)
    # COMMENTED OUT FOR TESTING - Uncomment these lines to enable time restriction
    if current_hour < 17 or (current_hour == 17 and current_minute < 30):
        print("Too early - script runs after 5:30pm only")
        return  # Exit the function early
    
    # STEP 2: Check if Already Ran Today (Prevent Spam)
    
    if check_already_ran_today():
        # Already ran today, exit silently without any output
        # This prevents you from getting spammed with notifications
        # every time you reconnect WiFi
        return
    
    # STEP 3: Fetch Weather Data
    
    data = get_weather()  # Call our function to get data from NEA
    
    # Extract the forecasts list from the nested structure
    forecasts = data['items'][0]['forecasts']

    # STEP 4: Filter to Your Monitored Areas Only
    
    # Create an empty dictionary to store area -> weather mapping
    # Example: {"Tampines": "Cloudy", "Jurong East": "Rain"}
    my_areas = {}
    
    # Loop through all forecasts from NEA
    for f in forecasts:
        # Check if this area is in your monitored list
        if f['area'] in MONITORED_AREAS:
            # Add it to our dictionary
            # Key = area name, Value = forecast text
            my_areas[f['area']] = f['forecast']
    
    # STEP 5: Prepare Output and Check for Bad Weather
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')  # Format as "2025-10-16 17:45"
    
    # Print header to console
    print(f"\nWeather Check - {timestamp}")
    print("=" * 50)
    
    # Track whether we found any bad weather
    has_bad_weather = False
    
    # Build list of output lines for notifications
    output_lines = [f"Weather Check - {timestamp}\n"]
    
    # Loop through your monitored areas in order
    for area in MONITORED_AREAS:
        # Check if we have data for this area
        if area in my_areas:
            weather = my_areas[area]  # Get the forecast text
            line = f"{area}: {weather}"
            
            # Print to console
            print(line)
            
            # Add to our output list
            output_lines.append(line)
            
            # Check if this weather contains any bad keywords
            # any() returns True if ANY element in the list is True
            # Example: any(["Showers" in "Heavy Showers", "Rain" in "Heavy Showers"])
            #          -> True because first condition matches
            if any(bad in weather for bad in BAD_WEATHER):
                has_bad_weather = True
    
    print("=" * 50)
    
    # Join all lines into a single message for Telegram
    # \n means newline (line break)
    message = "\n".join(output_lines)
    
    # STEP 6: Send Notifications
    
    if has_bad_weather:
        # Rain detected! Send warning notifications
        print("🚨 RAIN DETECTED - Bike safely!\n")
        title = "🚨 Rain Alert - Bike Safely!"
        
        # Desktop notification (exclude first line which is timestamp)
        show_notification(title, "\n".join(output_lines[1:]))
        
        # Telegram notification (include full message with timestamp)
        send_telegram(f"{title}\n\n{message}")
    else:
        # All clear! Send positive notifications
        print("✅ Clear weather - Safe to bike!\n")
        title = "✅ Safe to Bike!"
        
        # Send both notifications
        show_notification(title, "\n".join(output_lines[1:]))
        send_telegram(f"{title}\n\n{message}")
    
    # STEP 7: Mark That We Ran Today
    
    # Update the last run file so we don't run again today
    # This prevents notification spam when you reconnect WiFi multiple times
    update_last_run()

if __name__ == "__main__":
    main()  # Run the main function