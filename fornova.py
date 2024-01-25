import playwright
import requests
import json
import csv
from playwright.sync_api import sync_playwright

def fetch_html_playwright(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, wait_until='domcontentloaded', timeout=60000)

        page.wait_for_selector('.css-du5wmh-Box.e1m6xhuh0')

        html_content = page.content()

        browser.close()

    return html_content

def fetch_html_requests(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to retrieve content. Status code: {response.status_code}")

def main_playwright(url, fetch_html_function):
    html_content = fetch_html_function(url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.set_content(html_content)

        hotels = page.locator('.css-du5wmh-Box.e1m6xhuh0').all()
        print(f'There are: {len(hotels)} rooms.')

        rooms_data = []
        for i, hotel in enumerate(hotels, start=1):
            room_data = {
                'Room_Name': hotel.locator('.css-19vc6se-Heading-Heading-Text.e13es6xl3').inner_text(),
                'Rate_Name': hotel.locator('.css-10yvquw-Heading-Heading-Text.e13es6xl3').inner_text(),
                'Description': hotel.locator('.css-zapqsm-Text.epfmh1m0').inner_text().replace('\u2022', ' '),
                'Prices': [],
            }

            prices_container = hotel.locator('.css-2r3ilu-Box.e1yh5p92')
            prices = prices_container.locator('.css-n8sys9-Box-Flex.e1pfwvfi0').all()

            for price in prices:
                offer_card = price.locator('[data-testid="offer-card"]').first
                cancellation_policy_message_element = offer_card.locator('[data-testid="cancellation-policy-message"]').first
                additional_info_2 = price.locator('.css-70zr7a-Box-Flex.e1pfwvfi0')

                if cancellation_policy_message_element.is_visible():
                    cancellation_policy_message = cancellation_policy_message_element.inner_text().strip()
                else:
                    cancellation_policy_message = additional_info_2.inner_text().strip() if additional_info_2.is_visible() else None

                top_deal_exists = price.locator('.css-8jmuus-Container.e1osk7s0 .css-1jr3e3z-Text-BadgeText.e34cw120').first

                try:
                    cancellation_policy_message_1 = hotel.locator('.css-12hhnd3.e1ucyleq0').inner_text(timeout=5000)
                except playwright._impl._api_types.TimeoutError:
                    cancellation_policy_message_1 = None

                price_data = {
                    'Price': price.inner_text().replace('\n', '').strip(),
                    'Cancellation_Policy_Message_1': cancellation_policy_message_1,
                    'Top_Deal': 'Top Deal=True' if top_deal_exists else 'Top Deal=False',
                }
                room_data['Prices'].append(price_data)

            rooms_data.append(room_data)
            print(json.dumps(room_data, indent=2))

     
        with open('rooms_data.json', 'w') as json_file:
            json.dump(rooms_data, json_file, indent=2)

     
        csv_file = 'fornova.csv'
        with open(csv_file, 'w', newline='') as csvfile:
            fieldnames = ['Room_Name', 'Rate_Name', 'Description', 'Price', 'Cancellation_Policy_Message_1', 'Top_Deal']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for room_data in rooms_data:
                for price_data in room_data['Prices']:
                    writer.writerow({
                        'Room_Name': room_data['Room_Name'],
                        'Rate_Name': room_data['Rate_Name'],
                        'Description': room_data['Description'],
                        'Price': price_data['Price'],
                        'Cancellation_Policy_Message_1': price_data.get('Cancellation_Policy_Message_1', ''),
                        'Top_Deal': price_data['Top_Deal'],
                    })

        browser.close()

if __name__ == '__main__':
    page_url = f'https://www.qantas.com/hotels/properties/18482?adults=2&checkIn=2024-02-06&checkOut=2024-02-07&children=0&infants=0&location=London%2C%20England%2C%20United%20Kingdom&page=1&payWith=cash&searchType=list&sortBy=popularity'

    main_playwright(page_url, fetch_html_playwright)

