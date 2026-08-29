# Gymshark-Product-Scraper
A fast, resilient Python web scraper built with Playwright that extracts product catalog data directly from Gymshark's Next.js hydration payload (`__NEXT_DATA__`), bypassing fragile DOM elements and dynamic rendering delays.
---

## Key Highlights

- **State Extraction Architecture:** Pulls raw data directly from the embedded `<script id="__NEXT_DATA__">` JSON payload inside the DOM instead of parsing HTML visual elements.
- **Fast & Lightweight:** Avoids waiting for image loads, infinite scroll animations, or layout renders.
- **URL-Based Pagination:** Dynamically iterates through page index parameters (`&page=N`) to systematically parse the entire collection catalog.
- **Data Deduplication:** Tracks unique product identifiers in a Python `set()` to ensure no duplicate entries are recorded across overlapping queries.
- **Multi-Format Export:** Standardizes output into clean, structured `.json` and `.csv` files using native Python libraries (UTF-8 encoded).

---

## Tech Stack

- **Language:** Python 3.10+
- **Browser Automation:** [Playwright for Python](https://playwright.dev/python/)
- **Data Formatting:** Native `json` and `csv` modules

---
