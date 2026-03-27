import asyncio
from playwright.async_api import async_playwright
import os

async def verify_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1280, 'height': 1200})
        page = await context.new_page()

        # Navigate to the app
        await page.goto("http://localhost:8501", timeout=60000)
        await page.wait_for_load_state("networkidle")

        # 1. Verify Call Summarization Metadata
        # Click the tab
        await page.click("text=Call Summarization")
        # Click "Laden" to load the mock call
        await page.click("text=Laden")
        # Wait for the specific field to appear
        await page.wait_for_selector("text=Antragsberechtigt_Details:", timeout=10000)
        await page.screenshot(path="/home/jules/verification/screenshots/call_summarization_fixed_v2.png", full_page=True)

        # 2. Verify Matching Filters (Dropdowns)
        await page.click("text=Matching & Hybrid Search")
        # Check if selectboxes exist
        await page.wait_for_selector("text=Land filtern")
        await page.wait_for_selector("text=Bundesland filtern")
        await page.screenshot(path="/home/jules/verification/screenshots/matching_filters_fixed_v2.png", full_page=True)

        # 3. Verify Database View Selection
        await page.click("text=Database View")
        await page.wait_for_selector("text=Indexed Companies Database")
        # Ensure the "Select" column is present in the table
        await page.wait_for_selector("text=Select")
        await page.screenshot(path="/home/jules/verification/screenshots/db_view_fixed_table_v2.png", full_page=True)

        await browser.close()

if __name__ == "__main__":
    os.makedirs("/home/jules/verification/screenshots", exist_ok=True)
    asyncio.run(verify_ui())
