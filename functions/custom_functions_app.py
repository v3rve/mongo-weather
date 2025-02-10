import requests
import logging
import datetime
import json
import sys
import pymongo
import pandas as pd
import subprocess
from datetime import datetime

def date_validation(date_input):
    while True:
        try:
            datetime.strptime(date_input, "%Y-%m-%d")
            logging.info("Date has been inserted correctly!")
            return date_input
        except:
            raise ValueError("Wrong date format, it should be YYYY-MM-DD")
            logging.warning("Attention! Date has NOT been inserted correctly!")

def date_length_check(date_start, date_end):
    while ((datetime.strptime(date_end, "%Y-%m-%d") - datetime.strptime(date_start, "%Y-%m-%d")).days < 7) or date_start > date_end:

        logging.warning("Wrong day period! Please remember that the minimum day difference is 7 and date_start must be smaller than date_end.")
        date_start = date_validation(input("Please write start day: "))
        date_end = date_validation(input("Please write end day: "))

    logging.info("Correct day period!")
    return date_start, date_end 

def coordinates_validation(prompt, range_min, range_max):
    while True:
        coordinate_input = input(prompt)
        try:
            isinstance(coordinate_input, float) and min(range_min, range_max) < coordinate_input < max(range_min, range_max)
            logging.info("Coordinate_input has been inserted correctly")
            return coordinate_input
        except:
            raise ValueError(f'Wrong coordinate_input format, it should be type: float and in range from {range_min} to {range_max}!')
            logging.warning("Attention! Date has NOT been inserted correctly!")

def add_json_element(json_to_update, name_to_add, element_to_add):
        new_date_dict = {name_to_add: element_to_add}
        new_date_dict.update(json_to_update)
        return new_date_dict

def connect_to_db(client_address, db_name):
    client = pymongo.MongoClient(client_address)
    db_connection = client[db_name] 
    return db_connection 

def check_response(response_text):
    MAX_INFO = "You have exceeded the maximum"
    if response_text.startswith(MAX_INFO):
            logging.warning("We have reached the max number of API requests!")
            return False
    return True