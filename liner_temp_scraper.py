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
from dotenv import load_dotenv
import logging

import htmlscraper as scraper
from custom_influxdb_client import CustomInfluxDBClient, InfluxDBLoggingHandler
from fast_influxdb_client.fast_influxdb_client import InfluxMetric
import log_formatter
from measurement import load_measurements_from_yaml


ENV_FILEPATH = ".env"

# Load environment variables from .env file
load_dotenv(ENV_FILEPATH)


def setup_logging():
    import sys

    # Setup logging
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    logger = log_formatter.setup_logging(
        console_log_output="stdout",
        console_log_level="info",
        console_log_color=True,
        console_log_datefmt="%Y%m%d %H:%M:%S",
        logfile_file=f"{script_name}.log",
        logfile_log_level="info",
        logfile_log_color=False,
        logfile_log_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] %(message)s%(color_off)s",
        logfile_log_datefmt="%Y%m%d %H:%M:%S",
    )
    if not logger:
        print("Failed to setup logging, aborting.")
        return None
    return logger


def main():
    # Load variables from .env
    ip_address = os.getenv("IP_ADDRESS")
    path = os.getenv("ADDRESS_PATH")
    update_period = float(os.getenv("UPDATE_PERIOD"))

    # setup customised logging
    logger = setup_logging()

    # Setup fast influxdb client
    client = CustomInfluxDBClient(ENV_FILEPATH, delay=update_period)
    logging.info(
        f"Connecting to client at {ip_address} with update frequency of {update_period}s"
    )
    # Setup and assign logging handler to influxdb
    logger.addHandler(client.getLoggingHandler())

    measurement_filepath = "measurements.yaml"
    measurements = load_measurements_from_yaml(measurement_filepath)

    while True:
        try:
            # Fetch HTML content from the specified address and path
            html = scraper.fetch_html_content(ip_address, path, protocol="http")
        except scraper.GetRequestUnsuccessful:
            logging.warning("HTML get request was not successful")
            continue

        # Parse the HTML content using BeautifulSoup
        soup = scraper.parse_html_content(html)
        # Scrape data from the parsed HTML
        scraped_values = scraper.extract_elements_by_ids(soup, measurements.ids)
        measurements.update_values(scraped_values)
        metric = InfluxMetric(measurement="liner_heater", fields=measurements.asdict())
        client.add_metrics_to_queue(metric)

        logging.info(f"Metric uploaded to influx successfully")
        logging.debug(str(measurements))
        time.sleep(update_period)


if __name__ == "__main__":
    main()
