import requests
import logging
import datetime
import json
import sys
import pymongo
import pandas as pd
import subprocess
from datetime import datetime, timedelta
import os
from functions.custom_functions_app import *

logging.basicConfig(level = logging.INFO)

# Retrieve and check data that is delivered
config_data = json.load(open('config/config_cred.json'))
api_key = config_data["api_key"]
base_url = config_data["base_url"]

date_start = date_validation(os.getenv("DATE_START", "2024-04-11"))
date_end = date_validation(os.getenv("DATE_END", "2024-04-18"))
date_length_check(date_start, date_end)
time_range_args = [date_start, date_end]

coordinates_data = json.load(open('config/config_locations.json', encoding='utf-8'))
list_cities = list(coordinates_data.keys())

client_address = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
db_name = os.getenv("MONGO_DB", "weather_data_iso")
full_refresh_param = os.getenv("FR_PARAM", 0)
db_weather_data = connect_to_db(client_address = client_address, db_name = db_name)

date_list = pd.date_range(start=date_start, end=date_end).to_list()
time_range_diff = date_list[-1] - date_list[0]

if full_refresh_param == 1:
    #First check of the DB to avoid retrieving data from the API again
    for city_name in list_cities:
        city_passed = True  # Flag to track if the city passes all date checks

        # Iterate over each date in date_list to check if data for all dates is available
        for date in date_list:
            # Query the database for documents matching the city and date range
            existing_document = db_weather_data.days.find({
                "city": city_name,
                "datetime": {
                    "$gte": date_start,
                    "$lte": date_end
                }
            })
            
            # Create a list of all dates found in the database for this city within the date range
            existing_dates = [doc["datetime"] for doc in existing_document]

            # If no dates are found, mark the city as failing and stop further checks
            if not existing_dates:
                city_passed = False
                logging.info(f"No data found for {date} - {city_name}. Stopping checks for this city.")
                break

            # Convert the list of date strings to datetime objects
            existing_dates = [datetime.strptime(date_str, "%Y-%m-%d") for date_str in existing_dates]
            max_ed_date = max(existing_dates)
            min_ed_date = min(existing_dates)
            existing_dates_range = max_ed_date - min_ed_date

            # If the range of dates in the database doesn't match the desired range, mark the city as failing
            if time_range_diff != existing_dates_range:
                city_passed = False
                # Modification date_start and date_end
                date_start_check = datetime.strptime(date_start, "%Y-%m-%d")
                date_end_check = datetime.strptime(date_end, "%Y-%m-%d")
                if date_start_check <= max_ed_date and date_end_check >= min_ed_date:
                    if date_start == min_ed_date and date_end > max_ed_date:
                        date_start = (max_ed_date + timedelta(days=1)).strftime("%Y-%m-%d")

                    elif date_end_check == max_ed_date and date_start_check < min_ed_date:
                        date_end = (min_ed_date + timedelta(days=1)).strftime("%Y-%m-%d")
                logging.info(f"Incomplete date range for {city_name}. Stopping checks for this city.")
                break

        # After checking all dates for the city, if it has passed all checks, remove it from coordinates_data
        if city_passed:
            del coordinates_data[city_name]
            logging.info(f"{date_list} - {city_name} - All dates are already in the database. Removed from coordinates_data.")

    logging.info(f'''List of cities to get from API: {list(coordinates_data.keys())}''')

# Go through config file
if coordinates_data != {}:
    for item in coordinates_data.items():
        latitude = item[1]['latitude']
        longitude = item[1]['longitude']
        city_name = item[0]

        # Create a link to connect to the API
        api_url = f'{base_url}{latitude},{longitude}/{date_start}/{date_end}?key={api_key}'
        logging.info(coordinates_data.items())
        response = requests.get(api_url)
        if not check_response(response.text):
            list_cities = list_cities[:list_cities.index(city_name)]
            logging.info("Be careful - not all cities have been added to the database!")
            break
        else:
            weather_data = response.json()
            days_db = weather_data['days'] 

            # Check specific cities, days, hours
            for day in days_db:
                hours = day.pop('hours')
                dt = day["datetime"]
                # Check if records exist based on city, days, hours
                existing_document = db_weather_data.days.find_one({
                    "city": city_name,
                    "date": dt
                })

                if existing_document:
                    logging.info(f'''{dt} - {city_name} - Day's data is already in DB''')
                else:
                    # Add datetime and city_name to day section
                    day['datetime'] = dt
                    day['city'] = city_name
                    db_weather_data.days.insert_one(day)
                    logging.info(f'''{dt} - {city_name} - Day's data inserted in DB''')

                for hour in hours:
                    ht_hour = hour["datetime"]

                    # Second check specific cities, days, hours
                    existing_document = db_weather_data.hours.find_one({
                        "city": city_name,
                        "date": dt,
                        "datetime": ht_hour
                    })

                    if existing_document:
                        logging.info(f'''{ht_hour} - {city_name} - Hours's data is already in DB''')
                    else:
                        # Add datetime and city_name to day section
                        hour['date'] = dt
                        hour['city'] = city_name
                        hour['datetime'] = ht_hour

                        # Insertion of modified hour record
                        db_weather_data.hours.insert_one(hour)
                        logging.info(f'''{ht_hour} - {city_name} - Hours's data inserted in DB''')

# Run model for specific city
for city_name in list_cities:
    model_args = [*time_range_args, city_name]

    cursor = db_weather_data.days.find({
        "city": city_name,
        "datetime": {
            "$gte": date_start,
            "$lte": date_end
        }
    })
    # Preparation of data
    data = list(cursor)
    df = pd.DataFrame(data)
    if time_range_diff.days > 90:
    # Run model with arguments
        logging.info('Gradient Boosting model selected')
        subprocess.run(["python", "model.py"] + model_args)
    else:
        logging.info('SARIMA model selected')
        subprocess.run(["python", "model_short.py"] + model_args)