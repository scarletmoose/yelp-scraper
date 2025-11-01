#!/usr/bin/env python3
"""
Yellow Pages Business Scraper for Ouachita Parish, Louisiana
Collects business information including contact details, emails, and social media profiles
"""

import argparse
import asyncio
import re
import time
import random
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import pandas as pd
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YellowPagesScraper:
    """Scraper for Yellow Pages with stealth capabilities and email extraction"""
    
    def __init__(self, headless: bool = True, debug: bool = False):
        self.headless = headless
        self.debug = debug
        self.ua = UserAgent()
        self.browser: Optional[Browser] = None
        self.context = None
        self.businesses: List[Dict] = []
        
    async def init_browser(self):
        """Initialize Playwright browser with stealth settings"""
        playwright = await async_playwright().start()
        
        # Launch browser with stealth settings
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            user_agent=self.ua.random,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/Chicago',
        )
        
        # Add stealth scripts
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)
        
        logger.info("Browser initialized with stealth settings")
    
    async def random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
    
    async def scrape_yellow_pages(self, location: str, category: str, pages: int = 3) -> List[Dict]:
        """Scrape Yellow Pages for a specific category and location"""
        logger.info(f"Scraping Yellow Pages: {category} in {location}")
        
        page = await self.context.new_page()
        businesses = []
        
        try:
            for page_num in range(1, pages + 1):
                logger.info(f"Scraping page {page_num} for {category}")
                
                # Construct Yellow Pages URL
                search_term = category.replace(' ', '+')
                location_term = location.replace(' ', '+').replace(',', '%2C')
                url = f"https://www.yellowpages.com/search?search_terms={search_term}&geo_location_terms={location_term}&page={page_num}"
                
                try:
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    await self.random_delay(2, 4)
                    
                    # Extract business listings
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Find all business listings
                    listings = soup.find_all('div', class_='result')
                    
                    if not listings:
                        # Try alternative selectors
                        listings = soup.find_all('div', class_='search-results organic')
                        if listings:
                            listings = listings[0].find_all('div', class_='info')
                    
                    logger.info(f"Found {len(listings)} listings on page {page_num}")
                    
                    for listing in listings:
                        business = await self.extract_business_info(listing, category)
                        if business:
                            businesses.append(business)
                    
                    if not listings:
                        logger.warning(f"No listings found on page {page_num}. Possible blocking or end of results.")
                        break
                        
                except Exception as e:
                    logger.error(f"Error scraping page {page_num}: {str(e)}")
                    continue
                
                await self.random_delay(3, 6)
            
        finally:
            await page.close()
        
        return businesses
    
    async def extract_business_info(self, listing, category: str) -> Optional[Dict]:
        """Extract business information from a listing"""
        try:
            business = {'category': category}
            
            # Business name
            name_elem = listing.find('a', class_='business-name')
            if not name_elem:
                name_elem = listing.find('h2', class_='n')
            business['name'] = name_elem.get_text(strip=True) if name_elem else 'N/A'
            
            # Phone number
            phone_elem = listing.find('div', class_='phones')
            if not phone_elem:
                phone_elem = listing.find('div', class_='phone')
            business['phone'] = phone_elem.get_text(strip=True) if phone_elem else 'N/A'
            
            # Address
            address_elem = listing.find('div', class_='street-address')
            if address_elem:
                business['address'] = address_elem.get_text(strip=True)
            else:
                address_elem = listing.find('p', class_='adr')
                business['address'] = address_elem.get_text(strip=True) if address_elem else 'N/A'
            
            # City, State, ZIP
            locality_elem = listing.find('div', class_='locality')
            if locality_elem:
                business['city_state_zip'] = locality_elem.get_text(strip=True)
            else:
                business['city_state_zip'] = 'N/A'
            
            # Website
            website_elem = listing.find('a', class_='track-visit-website')
            if not website_elem:
                website_elem = listing.find('a', href=re.compile(r'http'))
            business['website'] = website_elem.get('href', 'N/A') if website_elem else 'N/A'
            
            # Initialize email and social media fields
            business['email'] = 'N/A'
            business['facebook'] = 'N/A'
            business['instagram'] = 'N/A'
            
            if business['name'] != 'N/A':
                return business
            
        except Exception as e:
            logger.error(f"Error extracting business info: {str(e)}")
        
        return None
    
    async def extract_email_from_website(self, url: str) -> Optional[str]:
        """Visit business website and extract email address"""
        if not url or url == 'N/A' or not url.startswith('http'):
            return None
        
        page = await self.context.new_page()
        
        try:
            logger.info(f"Visiting {url} to find email")
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await self.random_delay(1, 2)
            
            # Get page content
            content = await page.content()
            
            # Email regex patterns (prioritize business/owner emails)
            email_patterns = [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            ]
            
            emails = []
            for pattern in email_patterns:
                found_emails = re.findall(pattern, content)
                emails.extend(found_emails)
            
            # Filter out common non-business emails
            filtered_emails = [
                email for email in emails
                if not any(x in email.lower() for x in [
                    'example.com', 'yourdomain', 'yourname', 'wix.com',
                    'wordpress.com', 'squarespace', 'sentry', 'google-analytics'
                ])
            ]
            
            # Prioritize certain email prefixes (owner, info, contact, etc.)
            priority_prefixes = ['owner', 'ceo', 'president', 'manager', 'director', 'info', 'contact', 'hello']
            
            for email in filtered_emails:
                prefix = email.split('@')[0].lower()
                if any(p in prefix for p in priority_prefixes):
                    return email
            
            # Return first valid email if no priority email found
            if filtered_emails:
                return filtered_emails[0]
            
            # Try to find contact page
            try:
                contact_links = await page.query_selector_all('a[href*="contact"], a:has-text("Contact")')
                if contact_links and len(contact_links) > 0:
                    contact_url = await contact_links[0].get_attribute('href')
                    if contact_url:
                        full_url = urljoin(url, contact_url)
                        await page.goto(full_url, wait_until='domcontentloaded', timeout=10000)
                        await self.random_delay(1, 2)
                        
                        content = await page.content()
                        found_emails = re.findall(email_patterns[0], content)
                        filtered_emails = [
                            email for email in found_emails
                            if not any(x in email.lower() for x in [
                                'example.com', 'yourdomain', 'yourname', 'wix.com'
                            ])
                        ]
                        
                        if filtered_emails:
                            return filtered_emails[0]
            except:
                pass
            
        except Exception as e:
            logger.debug(f"Error extracting email from {url}: {str(e)}")
        finally:
            await page.close()
        
        return None
    
    async def extract_social_media(self, url: str) -> Dict[str, str]:
        """Extract social media links from business website"""
        social = {'facebook': 'N/A', 'instagram': 'N/A'}
        
        if not url or url == 'N/A' or not url.startswith('http'):
            return social
        
        page = await self.context.new_page()
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await self.random_delay(1, 2)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all links
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href'].lower()
                
                if 'facebook.com' in href and social['facebook'] == 'N/A':
                    social['facebook'] = link['href']
                
                if 'instagram.com' in href and social['instagram'] == 'N/A':
                    social['instagram'] = link['href']
                
                if social['facebook'] != 'N/A' and social['instagram'] != 'N/A':
                    break
            
        except Exception as e:
            logger.debug(f"Error extracting social media from {url}: {str(e)}")
        finally:
            await page.close()
        
        return social
    
    async def enrich_business_data(self, businesses: List[Dict]) -> List[Dict]:
        """Visit each business website to extract emails and social media"""
        logger.info(f"Enriching data for {len(businesses)} businesses...")
        
        for idx, business in enumerate(businesses, 1):
            logger.info(f"Enriching {idx}/{len(businesses)}: {business['name']}")
            
            if business['website'] and business['website'] != 'N/A':
                # Extract email
                email = await self.extract_email_from_website(business['website'])
                if email:
                    business['email'] = email
                    logger.info(f"  Found email: {email}")
                
                # Extract social media
                social = await self.extract_social_media(business['website'])
                business['facebook'] = social['facebook']
                business['instagram'] = social['instagram']
                
                await self.random_delay(2, 4)
            
        return businesses
    
    async def scrape_all_categories(self, location: str, categories: List[str], pages: int = 3) -> List[Dict]:
        """Scrape all specified categories"""
        all_businesses = []
        
        await self.init_browser()
        
        try:
            for category in categories:
                logger.info(f"\n{'='*60}\nScraping category: {category}\n{'='*60}")
                businesses = await self.scrape_yellow_pages(location, category, pages)
                logger.info(f"Found {len(businesses)} businesses in {category}")
                
                # Enrich with emails and social media
                enriched = await self.enrich_business_data(businesses)
                all_businesses.extend(enriched)
                
                await self.random_delay(3, 5)
            
        finally:
            if self.browser:
                await self.browser.close()
        
        return all_businesses
    
    def export_to_excel(self, businesses: List[Dict], output_file: str = 'business_results.xlsx'):
        """Export results to Excel file organized by category"""
        if not businesses:
            logger.warning("No businesses to export")
            return
        
        logger.info(f"Exporting {len(businesses)} businesses to {output_file}")
        
        # Create DataFrame
        df = pd.DataFrame(businesses)
        
        # Reorder columns
        column_order = ['category', 'name', 'phone', 'email', 'address', 'city_state_zip', 
                       'website', 'facebook', 'instagram']
        
        # Only include columns that exist
        column_order = [col for col in column_order if col in df.columns]
        df = df[column_order]
        
        # Create Excel writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Write all data to one sheet
            df.to_excel(writer, sheet_name='All Businesses', index=False)
            
            # Create separate sheet for each category
            for category in df['category'].unique():
                category_df = df[df['category'] == category]
                safe_name = category[:31]  # Excel sheet name limit
                category_df.to_excel(writer, sheet_name=safe_name, index=False)
        
        logger.info(f"✅ Results exported to {output_file}")
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"SCRAPING COMPLETE!")
        print(f"{'='*60}")
        print(f"Total businesses found: {len(businesses)}")
        print(f"Businesses with emails: {len(df[df['email'] != 'N/A'])}")
        print(f"Businesses with Facebook: {len(df[df['facebook'] != 'N/A'])}")
        print(f"Businesses with Instagram: {len(df[df['instagram'] != 'N/A'])}")
        print(f"\nBreakdown by category:")
        for category in df['category'].unique():
            count = len(df[df['category'] == category])
            print(f"  {category}: {count} businesses")
        print(f"\n📁 Results saved to: {output_file}")
        print(f"{'='*60}\n")


async def main():
    """Main function to run the scraper"""
    parser = argparse.ArgumentParser(description='Yellow Pages Business Scraper for Ouachita Parish, LA')
    parser.add_argument('--location', type=str, default='Monroe, LA',
                       help='Location to search (default: Monroe, LA)')
    parser.add_argument('--categories', nargs='+', required=True,
                       help='Categories to scrape (e.g., "Lawyers" "Coffee Shops" "Restaurants")')
    parser.add_argument('--pages', type=int, default=3,
                       help='Number of pages to scrape per category (default: 3)')
    parser.add_argument('--out', type=str, default='ouachita_businesses.xlsx',
                       help='Output Excel file name (default: ouachita_businesses.xlsx)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    
    args = parser.parse_args()
    
    logger.info(f"Starting scraper for {args.location}")
    logger.info(f"Categories: {', '.join(args.categories)}")
    logger.info(f"Pages per category: {args.pages}")
    
    scraper = YellowPagesScraper(headless=args.headless)
    
    businesses = await scraper.scrape_all_categories(
        location=args.location,
        categories=args.categories,
        pages=args.pages
    )
    
    scraper.export_to_excel(businesses, args.out)


if __name__ == '__main__':
    asyncio.run(main())
