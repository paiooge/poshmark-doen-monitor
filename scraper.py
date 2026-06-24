import json
import os
import re
import time
from datetime import datetime

from playwright.sync_api import sync_playwright


KEYWORD = "doen"

SEARCH_URL = (
    f"https://poshmark.com/search?query={KEYWORD}"
)

DATA_FILE = "poshmark_data.json"


def load_data():
    """
    读取已有商品数据
    """
    if not os.path.exists(DATA_FILE):
        return {}

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    return {
        item["url"]: item
        for item in items
        if item.get("url")
    }


def save_data(data):
    """
    保存数据
    """

    items = list(data.values())

    items.sort(
        key=lambda x: x.get("first_seen", ""),
        reverse=True
    )

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            items,
            f,
            ensure_ascii=False,
            indent=2
        )


def clean(text):
    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def get_listing_links(page):

    print("Opening search page...")

    page.goto(
        SEARCH_URL,
        timeout=60000
    )

    page.wait_for_timeout(4000)

    # 滚动加载更多商品
    for _ in range(10):
        page.mouse.wheel(0, 5000)
        page.wait_for_timeout(2000)

    links = page.locator("a")

    urls = set()

    count = links.count()

    for i in range(count):
        try:
            href = links.nth(i).get_attribute("href")

            if href and "/listing/" in href:

                if href.startswith("/"):
                    href = (
                        "https://poshmark.com"
                        + href
                    )

                urls.add(
                    href.split("?")[0]
                )

        except:
            continue

    print(
        f"Found {len(urls)} listings"
    )

    return list(urls)
def get_listing_detail(page, url):
    """
    获取商品详情
    """

    try:
        print(f"Scraping: {url}")

        page.goto(
            url,
            timeout=60000
        )

        page.wait_for_timeout(3000)

        title = ""
        price = ""
        description = ""
        seller = ""
        images = []

        # 页面文字
        body_text = page.locator("body").inner_text()

        # 尝试获取标题
        try:
            title = page.locator("h1").first.inner_text()
        except:
            pass

        # 尝试获取价格
        try:
            prices = page.locator("span").all_inner_texts()

            for text in prices:
                text = text.strip()

                if text.startswith("$"):
                    price = text
                    break
        except:
            pass


        # 商品描述
        try:
            description = (
                page.locator(
                    "[data-et-name='description']"
                )
                .inner_text()
            )
        except:
            # 如果选择器失效，备用方案
            description = body_text[:1500]


        # 商品图片
        try:
            imgs = page.locator("img")

            for i in range(imgs.count()):
                src = imgs.nth(i).get_attribute("src")

                if src and "http" in src:
                    if src not in images:
                        images.append(src)

        except:
            pass


        # 卖家名称（可能因页面变化失效）
        try:
            links = page.locator("a").all_inner_texts()

            for text in links:
                if (
                    "@" in text
                    or "closet" in text.lower()
                ):
                    seller = text
                    break

        except:
            pass


        item = {
            "title": clean(title),
            "price": clean(price),
            "description": clean(description),
            "seller": clean(seller),
            "images": images[:5],
            "url": url,
            "first_seen": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }


        return item


    except Exception as e:
        print(
            "Failed:",
            url,
            str(e)
        )

        return None
def main():

    existing = load_data()

    print(
        f"Existing listings: {len(existing)}"
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled"
            ]
        )

        context = browser.new_context(
            viewport={
                "width": 1280,
                "height": 900
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124 Safari/537.36"
            )
        )

        page = context.new_page()

        # 获取搜索结果商品链接
        urls = get_listing_links(page)

        print(
            f"Start checking {len(urls)} listings"
        )

        for url in urls:

            # 已经抓过，跳过
            if url in existing:
                print(
                    "Already exists:",
                    url
                )
                continue

            item = get_listing_detail(
                page,
                url
            )

            if (
                item
                and item.get("title")
            ):
                existing[url] = item

                print(
                    "New item found:",
                    item["title"]
                )

            # 减慢访问速度
            page.wait_for_timeout(2000)

        browser.close()

    save_data(existing)

    print(
        f"Finished. Total items: {len(existing)}"
    )


if __name__ == "__main__":
    main()
