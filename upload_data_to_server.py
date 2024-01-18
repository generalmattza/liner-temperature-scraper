#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Matthew Davidson
# Created Date: 2023-11-22
# ---------------------------------------------------------------------------
"""A script to scrape liner temperature data from html"""
# ---------------------------------------------------------------------------

import logging
import toml

from fast_influxdb_client import FastInfluxDBClient, InfluxMetric
from src.measurement import load_measurements_from_yaml, load_data_from_csv

CLIENT_CONFIG_FILEPATH = "config.toml"


def read_toml_file(filepath):
    with open(filepath, "r") as file:
        return toml.load(file)


def main():
    influx_config = read_toml_file("config.toml")["influx2"]

    client = FastInfluxDBClient.from_config_file(
        CLIENT_CONFIG_FILEPATH, delay=influx_config["update_period"]
    )
    client.default_bucket = "prototype-zero"

    measurements = load_measurements_from_yaml("src/measurements.yaml")
    measurements_set = load_data_from_csv(
        "data/measurement_data_20240112.csv", measurements
    )

    tags = dict(shot_id="000622", shot_name="PZero Shot 4", campaign="Commissioning")

    number_metrics = len(measurements_set)
    metric_counter = 0

    for measurements in measurements_set:
        metric = InfluxMetric(
            measurement="liner_heater",
            fields=measurements.asdict(),
            tags=tags,
            time=measurements.time,
        )
        client.write_metric(metric)
        print(f"Writing metric {metric_counter} of {number_metrics}")
        metric_counter += 1

    print(f"Finished writing {metric_counter} metrics")


if __name__ == "__main__":
    main()
