# parse.py
from datetime import datetime

#from pinoywok import whatsapp

from pinoywok.config import config

import pinoywok.config
import pinoywok.asset


def format_date(date_string):
    # Convert the input string to a datetime object
    dt_obj = datetime.strptime(date_string, "%Y-%m-%dT%H:%M")
    
    # Format the datetime object to the desired output format
    output_format = "%d-%m-%Y %H:%M"
    formatted_date = dt_obj.strftime(output_format)
    
    return formatted_date
