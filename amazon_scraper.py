import csv
from playwright.sync_api import sync_playwright
import os
import sys

CSV_FILE = "amazon_prices.csv"

def search_amazon(keyword, country_code="com", max_results=10):
    url = f"https://www.amazon.{country_code}/s?k={keyword.replace(' ', '+')}+for+office"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Realistic headers to reduce bot detection
        page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
        })

        page.goto(url, timeout=60000)
        page.wait_for_timeout(3000)  # wait for products to load
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(page.content())

        items = page.query_selector_all("div.s-main-slot [data-asin]:not([data-asin=''])")

        for item in items:
            asin = item.get_attribute("data-asin")
            title_elem = item.query_selector("h2 a span")
            price_elem = item.query_selector("span.a-price span.a-offscreen")

            title = title_elem.inner_text().strip() if title_elem else "N/A"
            price = price_elem.inner_text().strip() if price_elem else "N/A"

            print(asin, title, price)  # debug line

            if price != "N/A":
                results.append({
                    "product_name": keyword.lower(),
                    "asin": asin,
                    "title": title,
                    "price": price
                })

            if len(results) >= max_results:
                break

        browser.close()
        print(results)
    return results


def save_to_csv(products):
    # Check if CSV already exists
    file_exists = os.path.isfile(CSV_FILE)

    # Open CSV in append mode
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["product_name", "asin", "title", "price"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header if file is new
        if not file_exists:
            writer.writeheader()

        # Append all products
        for product in products:
            writer.writerow(product)

if __name__ == "__main__":
    # Get inputs from command-line arguments
    keyword = sys.argv[1]
    max_results = int(sys.argv[2])

    products = search_amazon(keyword, max_results=max_results)
    if products:
        save_to_csv(products)
        print(f"Saved {len(products)} products to {CSV_FILE}")
    else:
        print("No products found.")