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
from dotenv import load_dotenv

from htmlscraper import scrape_timestamp_from_soup, fetch_html_content, parse_html_content

# Load environment variables from .env file
load_dotenv()


def scrape_temp_data_from_soup(soup):
    try:
        top_plate_temp = {
            f'Thermocouple {i}': temp.get_text(strip=True)
            for i, temp in enumerate(soup.select('h1:-soup-contains("Top Plate Temperature") + p'))
        }

        bottom_plate_temp = {
            f'Thermocouple {i}': temp.get_text(strip=True)
            for i, temp in enumerate(soup.select('h1:-soup-contains("Bottom Plate Temperature") + p'))
        }

        ir_sensor_array_temps = [temp.get_text(strip=True) if temp and temp.get_text(
            strip=True) else '0' for temp in soup.select('table td')]

        current_temp_setpoint_top_elem = soup.find(
            'label', string='Current temperature setpoint:')
        current_temp_setpoint_top = current_temp_setpoint_top_elem.find_next(
            'p').get_text(strip=True) if current_temp_setpoint_top_elem else None

        current_temp_setpoint_bot_elem = soup.find('h1', string='Bottom Plate Temperature').find_next(
            'label', string='Current temperature setpoint:')
        current_temp_setpoint_bot = current_temp_setpoint_bot_elem.find_next(
            'p').get_text(strip=True) if current_temp_setpoint_bot_elem else None

        sd_card_status_elem = soup.find(
            'h1', string='Data logging').find_next('p')
        sd_card_status = sd_card_status_elem.get_text(
            strip=True) if sd_card_status_elem else None

        # Extract timestamp using a more general approach
        timestamp = scrape_timestamp_from_soup(soup)

        return {
            "Top Plate Temperature": top_plate_temp,
            "Bottom Plate Temperature": bottom_plate_temp,
            "IR Sensor Array Temperatures": ir_sensor_array_temps,
            "Current Temperature Setpoint (Top Plate)": current_temp_setpoint_top,
            "Current Temperature Setpoint (Bottom Plate)": current_temp_setpoint_bot,
            "SD Card Status": sd_card_status,
            "Timestamp": timestamp,
        }
    except Exception as e:
        # Handle exceptions and print an error message
        print(f"Error during scraping: {e}")
        return None


def display_data(scraped_data):
    if scraped_data:
        # Print or use the extracted data as needed
        for key, value in scraped_data.items():
            print(f"{key}:", value)
    else:
        # Print a message if there is no data to display
        print("No data to display.")


def scrape_data_from_address(ip_address, path=None):
    # Fetch HTML content from the specified address and path
    html = fetch_html_content(ip_address, path)

    # Parse the HTML content using BeautifulSoup
    soup = parse_html_content(html)

    # Scrape data from the parsed HTML
    temp_data = scrape_temp_data_from_soup(soup)

    # Return the scraped data
    return temp_data


def main():
    # Replace 'your_ip_address' with the actual IP address
    ip_address = os.getenv("IP_ADDRESS")  # bench address
    path = os.getenv("PATH")  # bench address

    # Scrape and display data from the specified IP address
    data = scrape_data_from_address(ip_address, path)
    display_data(data)


if __name__ == "__main__":
    main()
