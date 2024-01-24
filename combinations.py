import requests
from playwright.sync_api import sync_playwright
import time
import csv
from faker import Faker
from datetime import datetime, timedelta
import re

def extract_hotel_id(url):
    match = re.search(r'/properties/(\d+)', url)
    if match:
        return match.group(1)
    return None

def fetch_prices(url):
    # Use requests to fetch HTML content
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: Unable to fetch the page. Status code: {response.status_code}")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Set the content of the page using requests response
        page.content = response.text

        rooms_data = []
        fake = Faker()

        for _ in range(25):
            check_in_date = (datetime.now() + timedelta(days=fake.random_int(min=1, max=30))).strftime('%Y-%m-%d')
            check_out_date = (datetime.strptime(check_in_date, '%Y-%m-%d') + timedelta(days=fake.random_int(min=1, max=5))).strftime('%Y-%m-%d')

            # Extract hotel ID from the URL for each iteration
            hotel_id = extract_hotel_id(url)

            # Update URL with new check-in and check-out dates
            current_url = url.replace('checkIn=2024-02-06', f'checkIn={check_in_date}').replace('checkOut=2024-02-07', f'checkOut={check_out_date}')

            # Use Playwright to navigate to the URL
            page.goto(current_url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(4)

            hotels = page.locator('.css-du5wmh-Box.e1m6xhuh0').all()
            print(f'There are: {len(hotels)} rooms for {check_in_date} - {check_out_date} at hotel ID {hotel_id}.')

            for i, hotel in enumerate(hotels, start=1):
                room_data = {
                    'Room_Name': hotel.locator('.css-19vc6se-Heading-Heading-Text.e13es6xl3').inner_text(),
                    'Rate_Name': hotel.locator('.css-10yvquw-Heading-Heading-Text.e13es6xl3').inner_text(),
                    'Description': hotel.locator('.css-zapqsm-Text.epfmh1m0').inner_text().replace('\u2022', ' '),
                    'Prices': [],
                    'CheckIn': check_in_date,
                    'CheckOut': check_out_date,
                    'Hotel_ID': hotel_id,
                }

                prices_container = hotel.locator('[data-testid="offer-card"] .css-n8sys9-Box-Flex.e1pfwvfi0')
                prices = prices_container.all()

                for price in prices:
                    price_data = {
                        'Price': price.inner_text().replace('\n', '').strip(),
                    }
                    room_data['Prices'].append(price_data)

                if len(room_data['Prices']) < 3:
                    additional_prices = hotel.locator('[data-testid="offer-card"] .css-n8sys9-Box-Flex.e1pfwvfi0 ~ .css-n8sys9-Box-Flex.e1pfwvfi0').all()
                    for price in additional_prices:
                        price_data = {
                            'Price': price.inner_text().replace('\n', '').strip(),
                        }
                        room_data['Prices'].append(price_data)

                rooms_data.append(room_data)
                print(room_data)

            time.sleep(2)

        csv_file = 'combinations.csv'
        with open(csv_file, 'w', newline='') as csvfile:
            fieldnames = ['Room_Name', 'Rate_Name', 'Description', 'Price', 'CheckIn', 'CheckOut', 'Hotel_ID']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for room_data in rooms_data:
                for price_data in room_data['Prices']:
                    writer.writerow({
                        'Room_Name': room_data['Room_Name'],
                        'Rate_Name': room_data['Rate_Name'],
                        'Description': room_data['Description'],
                        'Price': price_data['Price'],
                        'CheckIn': room_data['CheckIn'],
                        'CheckOut': room_data['CheckOut'],
                        'Hotel_ID': room_data['Hotel_ID'],
                    })

        browser.close()

if __name__ == '__main__':
    page_url = 'https://www.qantas.com/hotels/properties/18482?adults=2&checkIn=2024-02-06&checkOut=2024-02-07&children=0&infants=0&location=London%2C%20England%2C%20United%20Kingdom&page=1&payWith=cash&searchType=list&sortBy=popularity'

    fetch_prices(page_url)
