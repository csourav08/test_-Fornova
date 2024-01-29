import time
import requests
from playwright.sync_api import sync_playwright
import json
import csv
from faker import Faker
from datetime import datetime, timedelta

def main():

    page_url = "https://www.qantas.com/hotels/properties/18482?adults=2&checkIn=2024-02-01&checkOut=2024-02-02&children=0&infants=0&location=London%2C%20England%2C%20United%20Kingdom&page=1&payWith=cash&searchType=list&sortBy=popularity"
    response = requests.get(page_url)


    if response.status_code != 200:
        print(f"Error: Unable to fetch the page. Status code: {response.status_code}")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(page_url, timeout=60000)

        page.wait_for_load_state('load')

        time.sleep(4)

        offer_cards = page.query_selector_all('[data-testid="offer-card"]')
        for card in offer_cards:
            card.click()
        time.sleep(3)
        rooms = page.locator('.css-o4ex2l-Box-Flex.e1yh5p90').all()
        print(f'There are: {len(rooms)} rooms.')

        rates = {}
        for room in rooms:
            room_name = room.locator('.css-vknzmc-Heading-Heading-Text.e13es6xl3').inner_text()
            offer_cards = room.locator('[data-testid="offer-card"]').all()

            room_rates = []
            for card in offer_cards:
                room_rate = card.locator('.css-n8sys9-Box-Flex.e1pfwvfi0').inner_text().split('\n')
                room_rate = [part.strip() for part in room_rate if part.strip()]
                room_rate_str = ' '.join(room_rate)

                cancellation_policy = card.locator('.css-70zr7a-Box-Flex.e1pfwvfi0').inner_text().replace('\n', ' ')

                number_of_guests_elements = card.locator('[data-testid="offer-guest-text"]').all()
                number_of_guests = ', '.join([guest.inner_text().replace('\u2022', ' ') for guest in number_of_guests_elements])

                top_deal_element = card.locator('.css-1jr3e3z-Text-BadgeText.e34cw120').all()
                is_top_deal = True if top_deal_element else False

                room_rates.append({
                    'number_of_guests': number_of_guests,
                    'room_rate': room_rate_str,
                    'cancellation_policy': cancellation_policy,
                    'top_deal': is_top_deal
                })

            rates[room_name] = room_rates

        print(json.dumps(rates, indent=2))

        with open('room_details.json', 'w') as json_file:
            json.dump(rates, json_file, indent=2)

        fake = Faker()
        Faker.seed(42)
        hotel_id = "18482"
        date_combinations = []
        for _ in range(25):
            check_in_date = (datetime.now() + timedelta(days=fake.random_int(min=1, max=30))).strftime('%Y-%m-%d')
            check_out_date = (datetime.strptime(check_in_date, '%Y-%m-%d') + timedelta(days=fake.random_int(min=1, max=5))).strftime('%Y-%m-%d')
            date_combinations.append((check_in_date, check_out_date))

        all_room_details = []

        for index, (check_in, check_out) in enumerate(date_combinations, start=1):
            print(f"Processing combination {index}: Check-in: {check_in}, Check-out: {check_out}")

            page_url = f"https://www.qantas.com/hotels/properties/{hotel_id}?adults=2&checkIn={check_in}&checkOut={check_out}&children=0&infants=0&location=London%2C%20England%2C%20United%20Kingdom&page=1&payWith=cash&searchType=list&sortBy=popularity"

            response = requests.get(page_url)

            if response.status_code != 200:
                print(f"Error: Unable to fetch the page. Status code: {response.status_code}")
                continue

            page.content = response.text

            page.wait_for_load_state('load')

            time.sleep(7)

            offer_cards = page.query_selector_all('[data-testid="offer-card"]')
            for card in offer_cards:
                card.click()

            time.sleep(3)

            rooms = page.locator('.css-o4ex2l-Box-Flex.e1yh5p90').all()
            print(f'There are: {len(rooms)} rooms.')

            for room in rooms:
                room_name = room.locator('.css-vknzmc-Heading-Heading-Text.e13es6xl3').inner_text()
                offer_cards = room.locator('[data-testid="offer-card"]').all()

                for card in offer_cards:
                    room_rate = card.locator('.css-n8sys9-Box-Flex.e1pfwvfi0').inner_text().split('\n')
                    room_rate = [part.strip() for part in room_rate if part.strip()]
                    room_rate_str = ' '.join(room_rate)

                    cancellation_policy = card.locator('.css-70zr7a-Box-Flex.e1pfwvfi0').inner_text().replace('\n', ' ')

                    number_of_guests_elements = card.locator('[data-testid="offer-guest-text"]').all()
                    number_of_guests = ', '.join([guest.inner_text().replace('\u2022', ' ') for guest in number_of_guests_elements])

                    top_deal_element = card.locator('.css-1jr3e3z-Text-BadgeText.e34cw120').all()
                    is_top_deal = True if top_deal_element else False

                    all_room_details.append({
                        'hotels_id': hotel_id,
                        'check_in': check_in,
                        'check_out': check_out,
                        'room_name': room_name,
                        'number_of_guests': number_of_guests,
                        'room_rate': room_rate_str,
                        'cancellation_policy': cancellation_policy,
                        'top_deal': is_top_deal
                    })

        csv_filename = "combinations.csv"
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            fieldnames = ['hotels_id', 'check_in', 'check_out', 'room_name', 'number_of_guests', 'room_rate', 'cancellation_policy', 'top_deal']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for room_detail in all_room_details:
                writer.writerow(room_detail)

        print(f"CSV file '{csv_filename}' saved successfully.")

        page.screenshot(path='full_page_screenshot.png', full_page=True)

        page.context.clear_cookies()

        browser.close()

if __name__ == '__main__':
    main()
