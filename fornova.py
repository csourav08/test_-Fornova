import time
import requests
from playwright.sync_api import sync_playwright
import json


def main():
    page_url = "https://www.qantas.com/hotels/properties/18482?adults=2&checkIn=2024-02-01&checkOut=2024-02-02&children=0&infants=0&location=London%2C%20England%2C%20United%20Kingdom&page=1&payWith=cash&searchType=list&sortBy=popularity"
    response = requests.get(page_url)

    if response.status_code != 200:
        print(f"Error: Unable to fetch the page. Status code: {response.status_code}")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Open the URL in the browser
        page.goto(page_url, timeout=60000)

        # Wait for the page to fully load
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

        page.screenshot(path='full_page_screenshot.png', full_page=True)

        page.context.clear_cookies()

        browser.close()


if __name__ == '__main__':
    main()
