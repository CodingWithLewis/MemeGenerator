import asyncio
from playwright.async_api import async_playwright
from tinydb import TinyDB, Query


SBR_WS_CDP = 'wss://brd-customer-hl_4a5981ec-zone-marketdatascrape:0ypz3p358tae@brd.superproxy.io:9222'

# https://knowyourmeme.com/categories/meme
# Database we are saving to
db = TinyDB('memes.json')

links_db = TinyDB('db.json')
Links = Query()

texts = [link.get('meme') for link in links_db.search(Links.meme.exists())]

urls = set(texts)


def clear_unsuccessful_db_entries(db):
    Memes = Query()
    db.remove(Memes.success == False)


def get_existing_meme_urls(db):
    Memes = Query()
    return set([meme['url'] for meme in db.search(Memes.success == True)])

async def get_image_links(page, url):
    photos_page_num = 1
    await page.goto(f"{url}/photos/page/{photos_page_num}", timeout=2*60*1000)
    # https://knowyourmeme.com/photos/2795320-wifejak
    photo_links = []
    while True:
        links = await page.query_selector_all("#photo_gallery a")
        for link in links:
            href = await link.get_attribute("href")
            photo_links.append(href)

        # Scroll to the bottom of the page to load more memes
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)  # Wait for new memes to load

        # Check if there are more memes to load
        has_more = await page.query_selector(".next_page") is not None
        # Move to the next page
        if has_more:
            if await page.query_selector(".next_page.disabled") is not None:
                # element is there but not clickable. We are at the last page
                break
            await page.click(".next_page")
            photos_page_num += 1
            await page.wait_for_url(f"{url}/photos/page/{photos_page_num}")
        else:
            break
    return photo_links


async def scrape_page(url):
    async with async_playwright() as p:
        try:

            browser = await p.chromium.connect_over_cdp(SBR_WS_CDP)
            context = await browser.new_context()

            await context.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico,css,ttf,woff,woff2,js}", lambda route: route.abort())
            page = await context.new_page()
            await page.goto(url, timeout=2*60*1000)
            await page.wait_for_timeout(3000)
            # Extract data from the page using Playwright selectors
            title = await page.title()
            # Extract other relevant data from the page
            posted = page.locator(".timeago").first
            posted_date = await posted.get_attribute("title")
            body_selector = "#content"
            if await page.query_selector(body_selector) is None:
                body_selector = "article"

            content_element = page.locator(body_selector).first
            content = await content_element.inner_text()

            photo_links = await get_image_links(page, url)

            db.insert({
                'url': url,
                'success': True,
                'title': title,
                'content': content,
                'photo_links': photo_links,
                "posted_date": posted_date
            })
        except Exception as e:
            print(e)
            db.insert({
                'url': url,
                'success': False,
                'error': str(e)
            })
        finally:
            await browser.close()


async def worker(queue):
    while True:
        url = await queue.get()
        await scrape_page(url)
        queue.task_done()


async def scrape_urls(urls, batch_size=100):
    queue = asyncio.Queue()
    workers = []

    # Create worker tasks
    for _ in range(batch_size):
        worker_task = asyncio.create_task(worker(queue))
        workers.append(worker_task)

    # Put URLs into the queue
    for url in urls:
        await queue.put(url)

    # Wait for all URLs to be processed
    await queue.join()

    # Cancel worker tasks
    for worker_task in workers:
        worker_task.cancel()

    # Wait for worker tasks to finish
    await asyncio.gather(*workers, return_exceptions=True)

clear_unsuccessful_db_entries(db)

successful_urls = get_existing_meme_urls(db)
urls = list(urls)
for link in urls:
    if link in successful_urls:
        urls.remove(link)


print(f"Found {len(successful_urls)} successful URLs in the database")
print(f"Scraping {len(urls)} URLs")
# Run the scraper
scraped_data = asyncio.run(scrape_urls(urls))
