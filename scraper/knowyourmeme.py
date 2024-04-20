import asyncio
from playwright.async_api import async_playwright
from tinydb import TinyDB, Query


SBR_WS_CDP = 'wss://brd-customer-hl_4a5981ec-zone-marketdatascrape:0ypz3p358tae@brd.superproxy.io:9222'

# https://knowyourmeme.com/categories/meme
async def main():
    async with async_playwright() as p:
        # Get highest number of pages
        db = TinyDB('db.json')
        pages = []
        q = Query()
        for item in db.search(q.page > 1):
            pages.append(item['page'])



        browser = await p.chromium.connect_over_cdp(SBR_WS_CDP)
        # browser = await p.chromium.launch(headless=False)

        context = await browser.new_context()
        # Block unnecessary requests
        await context.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico,css,ttf,woff,woff2,js}", lambda route: route.abort())

        page = await context.new_page()
        page_num = max(pages) + 1 if pages else 1
        await page.goto(f"https://knowyourmeme.com/categories/meme/page/{page_num}")
        print(f"Scraping page {page_num}")
        while True:
            meme_links = []
            # Get all the links to meme pages on the current page
            links = await page.query_selector_all(".entry-grid-body a")
            for link in links:
                href = await link.get_attribute("href")
                if href and "/memes/" in href:
                    meme_links.append(href)

            # Scroll to the bottom of the page to load more memes
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)  # Wait for new memes to load

            for meme in meme_links:
                db.insert({
                    'meme': meme,
                    'page': page_num
                })

            # Check if there are more memes to load
            has_more = await page.query_selector(".next_page") is not None

            # Move to the next page
            await page.click(".next_page")

            await page.wait_for_url(f"https://knowyourmeme.com/categories/meme/page/{page_num + 1}")
            page_num += 1
            print(f"Moving to page {page_num}")
            if not has_more:
                break

        print(f"Found {len(meme_links)} meme links:")
        for link in meme_links:
            print(link)

        await browser.close()

asyncio.run(main())