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

        # 1. Verify Matching Filters (KMU logic)
        await page.click("text=Matching & Hybrid Search")
        # Check if selectboxes exist and have KMU
        await page.wait_for_selector("text=Organisationsart filtern")
        # Just a screenshot to see the layout
        await page.screenshot(path="/home/jules/verification/screenshots/matching_kmu_filter.png", full_page=True)

        # 2. Verify Database View (New filter and selection)
        await page.click("text=Database View")
        await page.wait_for_selector("text=Organisationsart filtern")
        await page.screenshot(path="/home/jules/verification/screenshots/db_view_filters_kmu.png", full_page=True)

        await browser.close()

if __name__ == "__main__":
    os.makedirs("/home/jules/verification/screenshots", exist_ok=True)
    asyncio.run(verify_ui())
