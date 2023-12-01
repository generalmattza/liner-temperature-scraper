#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Matthew Davidson
# Created Date: 2023-11-22
# version ='1.0'
# ---------------------------------------------------------------------------
"""A script to scrape liner temperature data from html"""
# ---------------------------------------------------------------------------
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import logging
import re

from htmlscraper import (
    fetch_html_content,
    parse_html_content,
    extract_elements_by_ids,
)
from custom_influxdb_client import CustomInfluxDBClient
from fast_influxdb_client.fast_influxdb_client import InfluxMetric
import log_formatter

ENV_FILEPATH = ".env"

# Load environment variables from .env file
load_dotenv(ENV_FILEPATH)


def setup_logging():
    import sys

    # Setup logging
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    if not log_formatter.setup_logging(
        console_log_output="stdout",
        console_log_level="info",
        console_log_color=True,
        logfile_file=f"{script_name}.log",
        logfile_log_level="debug",
        logfile_log_color=False,
        logfile_log_template="%(color_on)s[%(created)d] [%(threadName)s] [%(levelname)-8s] %(message)s%(color_off)s",
    ):
        print("Failed to setup logging, aborting.")
        return 1


def process_txt_file(file_path):
    try:
        with open(file_path, "r") as txt_file:
            result_list = [line.strip() for line in txt_file.readlines()]
            return result_list
    except Exception as e:
        logging.error(e)
        return None


def convert_to_float(string):
    # Use regular expression to remove non-numeric characters
    numeric_string = re.sub(r"[^0-9.]+", "", string)

    try:
        result_float = float(numeric_string)
        return result_float
    except ValueError:
        logging.error(f"Unable to convert '{string}' to a float.")
        return 0


def display_data(scraped_data):
    if scraped_data:
        # Print or use the extracted data as needed
        for key, value in scraped_data.items():
            logging.info(f"{key}: {value}")
    else:
        # Print a message if there is no data to display
        logging.warning("No data to display.")


def post_process_data(data):
    new_data_dict = {}

    included_keys = [
        "top_TC1",
        "top_TC2",
        "top_TC3",
        "IR_ref",
        "IR_array_temp0",
        "IR_array_temp1",
        "IR_array_temp2",
        "IR_array_temp3",
        "IR_array_temp4",
        "IR_array_temp5",
        "IR_array_temp6",
        "IR_array_temp7",
        "top_setpoint",
        "top_PID",
        "bot_TC1",
        "bot_TC2",
        "bot_TC3",
        "bot_setpoint",
        "bot_PID",
    ]

    for k, v in data.items():
        if k in included_keys:
            v = convert_to_float(v)
        if v is None:
            v = 0.0
        new_data_dict[k] = v

    return new_data_dict


def main():
    # Replace 'your_ip_address' with the actual IP address
    ip_address = os.getenv("IP_ADDRESS")  # bench address
    path = os.getenv("PATH")  # bench address
    # Setup fast influxdb client
    update_period = float(os.getenv("UPDATE_PERIOD"))

    setup_logging()

    client = CustomInfluxDBClient(ENV_FILEPATH, delay=update_period)

    id_lookup_path = "lookup_ids.txt"
    lookup_ids_list = process_txt_file(id_lookup_path)

    while 1:
        # Fetch HTML content from the specified address and path
        html = fetch_html_content(ip_address, path, protocol="http")
        # Parse the HTML content using BeautifulSoup
        soup = parse_html_content(html)
        # Scrape data from the parsed HTML
        data = extract_elements_by_ids(soup, lookup_ids_list)

        data = post_process_data(data)

        metric = InfluxMetric(measurement="liner_heater", fields=data)
        client.add_metrics_to_queue(metric)

        logging.info(f"*** {datetime.now()} ***")
        display_data(data)
        time.sleep(update_period)


if __name__ == "__main__":
    main()
