# scraper.py
import random
import yaml
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from config import HEADLESS, FAKE_USER_AGENTS
import excel_writer

with open("elements.yml", 'r') as f:
    elements = yaml.safe_load(f)

# (Helper functions are correct)
def get_text(element, selector, default="N/A"):
    try: return element.query_selector(selector).text_content().strip()
    except (AttributeError, PlaywrightTimeoutError): return default
def get_attribute(element, selector, attribute, default="N/A"):
    try: return element.query_selector(selector).get_attribute(attribute)
    except (AttributeError, PlaywrightTimeoutError): return default

def scrape_summary_page(page):
    property_cards = page.query_selector_all(elements['property_card'])
    print(f"Found {len(property_cards)} properties on this page.")
    if not property_cards: return
    for card in property_cards:
        urgent_element = card.query_selector(elements['urgent_label'])
        status = "Urgent" if urgent_element else "Normal"
        
        # --- THIS IS THE FIX ---
        # The "image_url" line has been completely removed.
        summary_data = {
            "status": status,
            "title": get_text(card, elements['property_title']),
            "location": get_text(card, elements['location']),
            "price": get_text(card, elements['property_price']),
            "link": get_attribute(card, elements['property_link'], 'href')
        }
        # --- END OF FIX ---

        print(f"Scraped Summary: {summary_data['title']}")
        excel_writer.save_summary(summary_data, list(summary_data.keys()))
        yield summary_data['link']

# (The rest of the file is unchanged and correct)
def scrape_detail_page(context, url):
    if url == "N/A" or not url.startswith('/'): return
    full_url = f"https://www.lankapropertyweb.com{url}"
    page = context.new_page()
    try:
        print(f"Navigating to detail page: {full_url}")
        page.goto(full_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_selector(elements['detail_address'], timeout=30000)
        detail_data = { "url": full_url, "address": get_text(page, elements['detail_address']), "price": get_text(page, elements['detail_price']), "seller": get_text(page, elements['detail_seller_name']), "property_type": get_text(page, f"xpath={elements['detail_property_type']}"), "land_size": get_text(page, f"xpath={elements['detail_land_size']}"), "description": get_text(page, elements['detail_description']), }
        print(f"Scraped Details: {detail_data['address']}")
        excel_writer.save_detail(detail_data, list(detail_data.keys()))
    except Exception as e:
        print(f"Failed to scrape detail page {full_url}: {e}")
    finally:
        page.close()

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(user_agent=random.choice(FAKE_USER_AGENTS))
        page = context.new_page()
        try:
            print("Navigating to lankapropertyweb.com homepage...")
            page.goto("https://www.lankapropertyweb.com/", wait_until='domcontentloaded')
            print("Clicking on the 'Land' link in the main navigation...")
            page.locator(elements['land_link']).click()
            print("Waiting for the Land page to load...")
            page.wait_for_load_state('domcontentloaded', timeout=60000)
            time.sleep(2)
            max_pages = 5
            for i in range(max_pages):
                print(f"\n--- Scraping Page {i+1} ---")
                page.wait_for_selector(elements['property_card'], timeout=30000)
                detail_links = list(scrape_summary_page(page))
                for link in detail_links:
                    scrape_detail_page(context, link)
                    time.sleep(random.uniform(2, 4))
                next_page_button = page.query_selector(elements['pagination_next'])
                if next_page_button:
                    next_url = next_page_button.get_attribute('href')
                    full_next_url = f"https://www.lankapropertyweb.com{next_url}"
                    print(f"Navigating to next page: {full_next_url}")
                    page.goto(full_next_url, wait_until='domcontentloaded')
                    time.sleep(random.uniform(3, 5))
                else:
                    print("No more pages to scrape.")
                    break
        except Exception as e:
            print(f"A critical error occurred: {e}")
            page.screenshot(path='error_screenshot.png')
            print("An error screenshot has been saved as 'error_screenshot.png'")
        finally:
            browser.close()
            print("\nScraping complete.")

if __name__ == "__main__":
    main()