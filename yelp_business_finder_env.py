#!/usr/bin/env python3
"""
Yelp Business Finder (auto‑loads API key from .env)
"""

import argparse
import asyncio
import os
import re
import requests
from typing import List, Dict, Optional
import pandas as pd
from playwright.async_api import async_playwright, Browser
from bs4 import BeautifulSoup
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

class YelpBusinessFinder:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.browser: Optional[Browser] = None
        self.context = None
        self.base_url = "https://api.yelp.com/v3"

    def search_businesses(self, location: str, category: str, limit: int = 50) -> List[Dict]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"location": location, "term": category, "limit": min(limit, 50), "sort_by": "best_match"}
        try:
            r = requests.get(f"{self.base_url}/businesses/search", headers=headers, params=params, timeout=10)
            if r.status_code == 200:
                return r.json().get("businesses", [])
            else:
                logger.error(f"Yelp API error: {r.status_code} - {r.text}")
                return []
        except Exception as e:
            logger.error(f"Error calling Yelp API: {e}")
            return []

    def parse_yelp_business(self, yelp_data: dict, category: str) -> Dict:
        loc = yelp_data.get("location", {})
        address = " ".join(filter(None, [loc.get("address1"), loc.get("address2")]))
        city_state_zip = f"{loc.get('city','')}, {loc.get('state','')} {loc.get('zip_code','')}".strip()
        return {
            "category": category,
            "name": yelp_data.get("name", "N/A"),
            "phone": yelp_data.get("display_phone", "N/A"),
            "email": "N/A",
            "address": address or "N/A",
            "city_state_zip": city_state_zip or "N/A",
            "website": yelp_data.get("url", "N/A"),
            "yelp_url": yelp_data.get("url", "N/A"),
            "rating": yelp_data.get("rating", "N/A"),
            "review_count": yelp_data.get("review_count", 0),
            "facebook": "N/A",
            "instagram": "N/A",
        }

    async def init_browser(self):
        pw = await async_playwright().start()
        self.browser = await pw.chromium.launch(headless=True)
        self.context = await self.browser.new_context()

    async def get_business_website(self, business_name: str, location: str) -> Optional[str]:
        page = await self.context.new_page()
        try:
            query = f"{business_name} {location} official website"
            await page.goto(f"https://www.bing.com/search?q={query.replace(' ', '+')}", wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(1)
            soup = BeautifulSoup(await page.content(), "html.parser")
            res = soup.find("li", class_="b_algo")
            if res:
                link = res.find("a")
                if link and link.get("href", "").startswith("http"):
                    return link["href"]
        except Exception as e:
            logger.debug(f"Error finding website for {business_name}: {e}")
        finally:
            await page.close()
        return None

    async def extract_email_and_social(self, url: str) -> Dict[str, str]:
        result = {"email": "N/A", "facebook": "N/A", "instagram": "N/A"}
        if not url or "yelp.com" in url:
            return result
        page = await self.context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(1)
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", content)
            valid = [e for e in emails if not any(x in e for x in ["example", "schema", "png", "jpg"])]
            if valid:
                result["email"] = valid[0]
            for a in soup.find_all("a", href=True):
                h = a["href"].lower()
                if "facebook.com" in h and result["facebook"] == "N/A":
                    result["facebook"] = a["href"]
                if "instagram.com" in h and result["instagram"] == "N/A":
                    result["instagram"] = a["href"]
        except Exception as e:
            logger.debug(f"Error scraping {url}: {e}")
        finally:
            await page.close()
        return result

    async def enrich_businesses(self, businesses: List[Dict]) -> List[Dict]:
        await self.init_browser()
        try:
            for biz in businesses:
                logger.info(f"Enriching {biz['name']}")
                site = await self.get_business_website(biz["name"], biz["city_state_zip"])
                if site:
                    contact = await self.extract_email_and_social(site)
                    biz.update(contact)
            return businesses
        finally:
            if self.browser:
                await self.browser.close()

    def export_to_excel(self, businesses: List[Dict], out: str):
        df = pd.DataFrame(businesses)
        df.to_excel(out, index=False)
        logger.info(f"Saved results to {out}")


async def main():
    p = argparse.ArgumentParser(description="Yelp Business Finder")
    p.add_argument("--location", default="Monroe, LA")
    p.add_argument("--categories", nargs="+", required=True)
    p.add_argument("--max-per-category", type=int, default=50)
    p.add_argument("--out", default="yelp_results.xlsx")
    p.add_argument("--no-enrich", action="store_true")
    a = p.parse_args()

    api_key = os.getenv("YELP_API_KEY")
    if not api_key:
        print("❌ No Yelp API key found in .env or environment!")
        return

    finder = YelpBusinessFinder(api_key)
    all_biz = []
    for c in a.categories:
        results = finder.search_businesses(a.location, c, a.max_per_category)
        parsed = [finder.parse_yelp_business(r, c) for r in results]
        if not a.no_enrich:
            parsed = await finder.enrich_businesses(parsed)
        all_biz.extend(parsed)

    finder.export_to_excel(all_biz, a.out)
    print(f"✅ Completed. {len(all_biz)} results written to {a.out}")


if __name__ == "__main__":
    asyncio.run(main())
