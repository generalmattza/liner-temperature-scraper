#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Matthew Davidson
# Created Date: 2023-11-22
# version ='1.0'
# ---------------------------------------------------------------------------
"""Tools to assist with webscraping"""
# ---------------------------------------------------------------------------

import requests
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)


class GetRequestUnsuccessful(Exception):
    pass


def fetch_html_content(url):
    # Construct the URL with the given IP address and optional path
    try:
        # Make a GET request to the URL
        response = requests.get(url)
    except requests.exceptions.ConnectionError as e:
        logger.warning('HTML GET request was unsuccessful',
                       extra=dict(details=e))
        raise GetRequestUnsuccessful

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Return the HTML content if successful
        return response.text
    else:
        # Print an error message if the request fails and return None
        logger.warning(f"Failed to retrieve HTML. Status code: {response.status_code}")
        raise GetRequestUnsuccessful


def parse_html_content(html):
    # Parse the HTML content using BeautifulSoup
    return BeautifulSoup(html, "html.parser")


def extract_timestamp_from_strings(strings):
    # Define a regular expression pattern for the timestamp format
    timestamp_pattern = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

    # Iterate through the strings to find a matching timestamp
    for string in strings:
        match = timestamp_pattern.search(string)
        if match:
            return match.group()

    # Return None if no timestamp is found
    return None


def scrape_timestamp_from_soup(soup):
    # Extract all strings within the soup
    all_strings = soup.stripped_strings

    # Attempt to extract timestamp from the strings
    timestamp = extract_timestamp_from_strings(all_strings)

    if timestamp:
        return timestamp
    else:
        # Print a message if the timestamp is not found
        logger.warning("Timestamp not found.")
        return None

def remove_null_values_from_dict(result_dict, null='NaN'):
    assert isinstance(result_dict, dict)
    result_dict_copy = result_dict.copy()
    for k,v in result_dict:
        if v == null:
            result_dict_copy.pop(k)
    return result_dict_copy

def extract_elements_by_ids(html, id_list):
    result_dict = {}

    if isinstance(html, str):
        soup = BeautifulSoup(html, "html.parser")
    else:
        soup = html

    # Ensure id_list is a list, even if it contains a single ID
    if not isinstance(id_list, list):
        id_list = [id_list]

    for element_id in id_list:
        element = soup.find(id=element_id)

        if element:
            result_dict[element_id] = element.text

    result_dict = remove_null_values_from_dict(result_dict)
    return result_dict


def display_data(scraped_data):
    if scraped_data:
        # Print or use the extracted data as needed
        for key, value in scraped_data.items():
            logger.info(f"{key}: {value}")
    else:
        # Print a message if there is no data to display
        logger.warning("No data to display.")
