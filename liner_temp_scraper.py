#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Matthew Davidson
# Created Date: 2023-11-22
# ---------------------------------------------------------------------------
"""A script to scrape liner temperature data from html"""
# ---------------------------------------------------------------------------
import os
import time
import logging
import toml

import htmlscraper as scraper
from fast_influxdb_client import FastInfluxDBClient, InfluxMetric
import log_formatter
from measurement import load_measurements_from_yaml, load_data_from_csv

CLIENT_CONFIG_FILEPATH = 'config.toml'


def setup_logging():

    import sys

    # Setup logging
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    logger = log_formatter.setup_logging(
        console_log_output="stdout",
        console_log_level="info",
        console_log_color=True,
        # console_log_datefmt="%Y%m%d %H:%M:%S",
        console_log_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] %(message)s%(color_off)s",
        logfile_file=f"logs/{script_name}.log",
        logfile_log_level="debug",
        logfile_log_color=False,
        logfile_log_template="%(color_on)s[%(asctime)s] [%(threadName)s] [%(levelname)-8s] %(message)s%(color_off)s",
        logfile_log_datefmt="%Y%m%d %H:%M:%S",
        # logfile_timed_rotation=True,
    )
    if not logger:
        print("Failed to setup logging, aborting.")
        return None
    return logger


def read_toml_file(filepath):
    with open(filepath, 'r') as file:
        return toml.load(file)


def load_measurements_from_csv():
    data_file_path = "measurement_data_20231201.csv"
    measurement_file_path = "measurements.yaml"

    measurements = load_measurements_from_yaml(measurement_file_path)
    measurements_series = load_data_from_csv(data_file_path, measurements)

    client = FastInfluxDBClient.from_config_file(CLIENT_CONFIG_FILEPATH)

    for measurements in measurements_series:
        metric = InfluxMetric(
            measurement="liner_heater",
            fields=measurements.asdict(),
            time=measurements.time,
        )
        client.add_metrics_to_queue(metric)

    time.sleep(10)


def main():

    influx_config = read_toml_file('config.toml')['influx2']

    client = FastInfluxDBClient.from_config_file(
        CLIENT_CONFIG_FILEPATH, delay=influx_config['update_period'])
    client.default_bucket = 'prototype-zero'

    # setup customised logging
    logger = setup_logging()
    # Setup and assign logging handler to influxdb
    influx_logging_handler = client.get_logging_handler()
    influx_logging_handler.setLevel(logging.INFO)
    logger.addHandler(influx_logging_handler)

    # Setup fast influxdb client
    logger.info(
        f"Created client to {client.url}", extra=dict(details=f"{client=}")
    )

    measurement_filepath = "measurements.yaml"
    measurements = load_measurements_from_yaml(measurement_filepath)

    heater_control_webpage_config = read_toml_file(
        'config.toml')['heater_control_webpage']
    webpage_url = heater_control_webpage_config['url']

    while True:
        try:
            # Fetch HTML content from the specified address and path
            html = scraper.fetch_html_content(webpage_url)
        except scraper.GetRequestUnsuccessful:
            # If unsuccessful, then restart loop and try again
            continue

        # Parse the HTML content using BeautifulSoup
        soup = scraper.parse_html_content(html)
        # Scrape data from the parsed HTML
        scraped_values = scraper.extract_elements_by_ids(
            soup, measurements.ids)
        measurements.update_values(scraped_values)
        metric = InfluxMetric(
            measurement="liner_heater",
            fields=measurements.asdict()
        )
        client.write_metric(metric)
        logger.debug(str(measurements))
        time.sleep(influx_config['update_period'])


if __name__ == "__main__":
    main()
    # load_measurements_from_csv()
