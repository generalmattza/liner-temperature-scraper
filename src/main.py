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
from measurement import load_measurements_from_yaml
from custom_logging import setup_logger, ColoredLogFormatter

CLIENT_CONFIG_FILEPATH = "config.toml"
CLIENT_DEFAULT_BUCKET = "prototype-zero"
CLIENT_DEFAULT_MEASUREMENT = "liner_heater"


def setup_logging(client):
    import sys

    # Setup logging
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    debug_file_handler = logging.FileHandler(filename=f"logs/{script_name}.debug.log")
    debug_file_handler.setLevel(logging.DEBUG)

    info_file_handler = logging.FileHandler(filename=f"logs/{script_name}.info.log")
    info_file_handler.setLevel(logging.INFO)

    # set the log format for the handlers
    console_handler.setFormatter(
        ColoredLogFormatter(
            fmt="%(asctime)s,%(msecs)d - %(name)s - %(levelname)-8s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    debug_file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s,%(msecs)d - %(name)s - %(levelname)-8s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    info_file_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s,%(msecs)d - %(name)s - %(levelname)-8s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # Setup and assign logging handler to influxdb
    influx_logging_handler = client.get_logging_handler()
    influx_logging_handler.setLevel(logging.INFO)

    # create the logger
    logger = setup_logger(
        handlers=[console_handler, debug_file_handler, influx_logging_handler, info_file_handler]
    )

    return logger


def read_toml_file(filepath):
    with open(filepath, "r") as file:
        return toml.load(file)


def main():
    influx_config = read_toml_file("config.toml")["influx2"]

    client = FastInfluxDBClient.from_config_file(
        CLIENT_CONFIG_FILEPATH, delay=influx_config["update_period"]
    )
    client.default_bucket = CLIENT_DEFAULT_BUCKET

    # setup customised logging
    logger = setup_logging(client)

    # Setup fast influxdb client
    logger.info(f"Created client to {client.url}", extra=dict(details=f"{client=}"))

    measurement_filepath = "src/measurements.yaml"

    heater_control_webpage_config = read_toml_file("config.toml")[
        "heater_control_webpage"
    ]
    webpage_url = heater_control_webpage_config["url"]

    tags_extra = {
        "shot_id": "xxxxxx",
        "shot_name": "PZero Shot 4",
        "campaign": "Commissioning",
    }
    
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
        measurements = load_measurements_from_yaml(measurement_filepath)
        scraped_values = scraper.extract_elements_by_ids(soup, measurements.ids)
        logger.debug(scraped_values)
        # Update existing measurements object values, stripping null values, and return new object
        measurements = measurements.update_values(scraped_values)
        # set tags for data storage
        for measurement in measurements:
            # Create new metric
            try:
                tags_merged = measurement.tags | tags_extra
            except TypeError:
                tags_merged = tags_extra
            metric = InfluxMetric(
                measurement=CLIENT_DEFAULT_MEASUREMENT,
                fields=measurement.fields,
                tags=tags_merged,
            )
            # Write to influx server
            # client.write_metric(metric)
        # Log measurements to file for debugging
        logger.debug(measurements)
        time.sleep(influx_config["update_period"])


if __name__ == "__main__":
    main()
