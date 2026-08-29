import csv
import json
import re

from playwright.sync_api import Playwright, sync_playwright


def save_data(data: list[dict], filename: str = "gymshark_products") -> None:
    if not data:
        print("No data to save.")
        return

    with open(f"{filename}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    keys = data[0].keys()
    with open(f"{filename}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

    print(f"Successfully saved {len(data)} items to CSV and JSON.")


def extract_total_products(page) -> int:
    data = page.evaluate(
        """
        () => {
            const tag = document.querySelector('script#__NEXT_DATA__');
            if (!tag) return 0;
            try {
                const payload = JSON.parse(tag.textContent);
                return Number(payload?.props?.pageProps?.ssrQuery?.nbHits || 0);
            } catch (error) {
                return 0;
            }
        }
        """
    )
    return int(data) if isinstance(data, (int, float)) else 0


def extract_page_products(page):
    return page.evaluate(
        """
        () => {
            const tag = document.querySelector('script#__NEXT_DATA__');
            if (!tag) return { nbHits: 0, nbPages: 0, hits: [] };
            try {
                const payload = JSON.parse(tag.textContent);
                const query = payload?.props?.pageProps?.ssrQuery || {};
                return {
                    nbHits: Number(query.nbHits || 0),
                    nbPages: Number(query.nbPages || 0),
                    hits: Array.isArray(query.hits) ? query.hits : []
                };
            } catch (error) {
                return { nbHits: 0, nbPages: 0, hits: [] };
            }
        }
        """
    )


def parse_product(hit: dict) -> dict | None:
    title = (hit.get("title") or "").strip()
    if not title:
        return None

    product_id = hit.get("id") or hit.get("handle") or title
    price = hit.get("price")
    if isinstance(price, (int, float)):
        price_text = f"${price:,.2f}" if price % 1 else f"${price:,.0f}"
    elif isinstance(price, str):
        price_text = price.strip()
    else:
        price_text = ""

    media = hit.get("featuredMedia") or hit.get("media") or []
    image_url = None
    if isinstance(media, list) and media:
        first = media[0]
        image_url = first.get("url") or first.get("src") or first.get("image")
        if isinstance(image_url, dict):
            image_url = image_url.get("url") or image_url.get("src")
    elif isinstance(media, dict):
        image_url = media.get("url") or media.get("src") or media.get("image")
        if isinstance(image_url, dict):
            image_url = image_url.get("url") or image_url.get("src")

    return {"id": product_id, "name": title, "price": price_text, "image url": image_url}


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()

    try:
        base_url = "https://www.gymshark.com/collections/all-products/mens?sortBy=sortLTH"
        page.goto(base_url, wait_until="domcontentloaded", timeout=120000)

        cookie = page.locator("#onetrust-accept-btn-handler, button:has-text('Accept All'), button:has-text('Continue')").first
        try:
            cookie.wait_for(state="visible", timeout=5000)
            cookie.click()
            print("Accepted cookies/banner.")
        except Exception:
            print("No cookie banner appeared.")

        close_store = page.get_by_test_id("storeSelector-close-select")
        try:
            close_store.wait_for(state="visible", timeout=5000)
            close_store.click()
            print("Closed store selector.")
        except Exception:
            print("No store selector appeared.")

        initial_page = extract_page_products(page)
        total_needed = initial_page.get("nbHits") or extract_total_products(page)
        total_pages = initial_page.get("nbPages") or 1
        seen_ids = set()
        all_products = []

        # Gymshark uses a zero-based page index in the collection payload.
        # Base URL = page 0, &page=1 = page 1, ..., &page=15 = final page.
        # Visiting &page=16 is invalid and returns no results.
        for page_num in range(0, total_pages):
            url = base_url if page_num == 0 else f"{base_url}&page={page_num}"
            page.goto(url, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(1500)

            payload = extract_page_products(page)
            hits = payload.get("hits") or []
            if not hits:
                print(f"Page {page_num}: no payload products found; stopping.")
                break

            page_items = []
            for hit in hits:
                parsed = parse_product(hit)
                if not parsed:
                    continue
                product_id = parsed["id"]
                if product_id in seen_ids:
                    continue
                seen_ids.add(product_id)
                page_items.append(parsed)

            print(f"Page {page_num}: loaded {len(page_items)} new products.")
            all_products.extend(page_items)

            if total_needed and len(all_products) >= total_needed:
                print(f"Reached target total of {total_needed} products.")
                break

        print(f"Total collected products: {len(all_products)}")
        save_data(all_products, filename="gymshark_products")
    finally:
        context.close()
        browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)

