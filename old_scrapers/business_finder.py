#!/usr/bin/env python3
"""
Multi-Source Business Finder for Ouachita Parish, Louisiana
Searches for businesses using Google Maps and web search to collect contact information
"""

import argparse
import asyncio
import re
import time
import random
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse, quote_plus
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


class BusinessFinder:
    """Multi-source business finder with email and social media extraction"""
    
    def __init__(self, headless: bool = True, debug: bool = False):
        self.headless = headless
        self.debug = debug
        self.ua = UserAgent()
        self.browser: Optional[Browser] = None
        self.context = None
        self.businesses: List[Dict] = []
        self.seen_businesses: Set[str] = set()  # Deduplication
        
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
        
        # Create context with realistic settings and rotate user agent
        self.context = await self.browser.new_context(
            user_agent=self.ua.random,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/Chicago',
        )
        
        # Add comprehensive stealth scripts
        await self.context.add_init_script("""
            // Hide webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Set languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Mock permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mock chrome object
            window.chrome = {
                runtime: {}
            };
        """)
        
        logger.info("Browser initialized with enhanced stealth settings")
    
    async def random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
    
    async def save_debug_info(self, page: Page, filename_prefix: str):
        """Save HTML and screenshot for debugging"""
        if not self.debug:
            return
        
        try:
            # Save HTML
            content = await page.content()
            with open(f"debug_{filename_prefix}.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            # Save screenshot
            await page.screenshot(path=f"debug_{filename_prefix}.png")
            logger.info(f"Debug info saved: debug_{filename_prefix}.{{html,png}}")
        except Exception as e:
            logger.error(f"Failed to save debug info: {str(e)}")
    
    async def scrape_google_maps(self, location: str, category: str, max_results: int = 30) -> List[Dict]:
        """Scrape Google Maps for business listings"""
        logger.info(f"Searching Google Maps: {category} in {location}")
        
        page = await self.context.new_page()
        businesses = []
        
        try:
            # Construct Google Maps search URL
            query = f"{category} in {location}"
            search_url = f"https://www.google.com/maps/search/{quote_plus(query)}"
            
            logger.info(f"Navigating to: {search_url}")
            await page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            await self.random_delay(3, 5)
            
            # Wait for results to load
            try:
                await page.wait_for_selector('a[href*="/maps/place/"]', timeout=10000)
                logger.info("Google Maps results loaded")
            except:
                logger.warning("Timeout waiting for Google Maps results")
                await self.save_debug_info(page, f"gmaps_{category.replace(' ', '_')}")
            
            # Scroll to load more results
            for i in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.random_delay(1, 2)
            
            # Extract business cards
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find business listings - Google Maps uses various selectors
            business_links = soup.find_all('a', href=re.compile(r'/maps/place/'))
            
            logger.info(f"Found {len(business_links)} potential business links")
            
            # Extract unique business names and URLs
            business_urls = set()
            for link in business_links[:max_results]:
                href = link.get('href', '')
                if '/maps/place/' in href:
                    # Extract business name from URL or aria-label
                    aria_label = link.get('aria-label', '')
                    if aria_label:
                        business_urls.add((aria_label, href))
            
            logger.info(f"Found {len(business_urls)} unique businesses")
            
            # Visit each business page to get details
            for idx, (name, url) in enumerate(list(business_urls)[:max_results], 1):
                logger.info(f"  Extracting details for {idx}/{min(len(business_urls), max_results)}: {name}")
                
                business_data = await self.extract_google_maps_business(page, name, url, category)
                if business_data:
                    businesses.append(business_data)
                
                await self.random_delay(2, 4)
            
        except Exception as e:
            logger.error(f"Error scraping Google Maps: {str(e)}")
            await self.save_debug_info(page, f"gmaps_error_{category.replace(' ', '_')}")
        finally:
            await page.close()
        
        return businesses
    
    async def extract_google_maps_business(self, page: Page, name: str, url: str, category: str) -> Optional[Dict]:
        """Extract detailed business information from Google Maps listing"""
        try:
            # Navigate to business page
            full_url = f"https://www.google.com{url}" if url.startswith('/') else url
            await page.goto(full_url, wait_until='domcontentloaded', timeout=15000)
            await self.random_delay(2, 3)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            business = {
                'category': category,
                'name': name,
                'phone': 'N/A',
                'address': 'N/A',
                'city_state_zip': 'N/A',
                'website': 'N/A',
                'email': 'N/A',
                'facebook': 'N/A',
                'instagram': 'N/A'
            }
            
            # Extract phone number
            phone_button = soup.find('button', {'data-item-id': re.compile(r'phone')})
            if phone_button:
                phone_text = phone_button.get_text(strip=True)
                phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', phone_text)
                if phone_match:
                    business['phone'] = phone_match.group()
            
            # Extract address
            address_button = soup.find('button', {'data-item-id': re.compile(r'address')})
            if address_button:
                business['address'] = address_button.get_text(strip=True)
                # Try to split into address and city/state/zip
                parts = business['address'].split(',')
                if len(parts) >= 2:
                    business['city_state_zip'] = ', '.join(parts[-2:]).strip()
                    business['address'] = ', '.join(parts[:-2]).strip()
            
            # Extract website
            website_link = soup.find('a', {'data-item-id': re.compile(r'authority')})
            if not website_link:
                website_link = soup.find('a', href=re.compile(r'^https?://'), attrs={'aria-label': re.compile(r'[Ww]ebsite', re.I)})
            
            if website_link:
                business['website'] = website_link.get('href', 'N/A')
            
            # Deduplicate by name + phone
            business_key = f"{business['name']}_{business['phone']}"
            if business_key in self.seen_businesses:
                logger.debug(f"Skipping duplicate: {business['name']}")
                return None
            
            self.seen_businesses.add(business_key)
            
            return business
            
        except Exception as e:
            logger.error(f"Error extracting Google Maps business details: {str(e)}")
            return None
    
    async def extract_email_from_website(self, url: str) -> Optional[str]:
        """Visit business website and extract email address"""
        if not url or url == 'N/A' or not url.startswith('http'):
            return None
        
        page = await self.context.new_page()
        
        try:
            logger.debug(f"Visiting {url} to find email")
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await self.random_delay(1, 2)
            
            # Get page content
            content = await page.content()
            
            # Email regex pattern
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            
            emails = re.findall(email_pattern, content)
            
            # Filter out common non-business emails
            filtered_emails = [
                email for email in emails
                if not any(x in email.lower() for x in [
                    'example.com', 'yourdomain', 'yourname', 'wix.com',
                    'wordpress.com', 'squarespace', 'sentry', 'google-analytics',
                    'schema.org', 'w3.org', 'png', 'jpg', 'jpeg', 'gif'
                ])
            ]
            
            # Prioritize decision-maker email prefixes
            priority_prefixes = ['owner', 'ceo', 'president', 'manager', 'director', 
                               'admin', 'info', 'contact', 'hello', 'sales']
            
            for email in filtered_emails:
                prefix = email.split('@')[0].lower()
                if any(p in prefix for p in priority_prefixes):
                    return email
            
            # Return first valid email if no priority email found
            if filtered_emails:
                return filtered_emails[0]
            
            # Try to find contact page
            try:
                contact_links = await page.query_selector_all('a[href*="contact" i], a:has-text("Contact")')
                if contact_links and len(contact_links) > 0:
                    contact_url = await contact_links[0].get_attribute('href')
                    if contact_url:
                        full_url = urljoin(url, contact_url)
                        await page.goto(full_url, wait_until='domcontentloaded', timeout=10000)
                        await self.random_delay(1, 2)
                        
                        content = await page.content()
                        found_emails = re.findall(email_pattern, content)
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
                    logger.info(f"  ✓ Found email: {email}")
                
                # Extract social media
                social = await self.extract_social_media(business['website'])
                business['facebook'] = social['facebook']
                business['instagram'] = social['instagram']
                
                if social['facebook'] != 'N/A':
                    logger.info(f"  ✓ Found Facebook")
                if social['instagram'] != 'N/A':
                    logger.info(f"  ✓ Found Instagram")
                
                await self.random_delay(2, 4)
        
        return businesses
    
    async def search_all_categories(self, location: str, categories: List[str], max_per_category: int = 30) -> List[Dict]:
        """Search all specified categories"""
        all_businesses = []
        
        await self.init_browser()
        
        try:
            for category in categories:
                logger.info(f"\n{'='*70}\nSearching category: {category}\n{'='*70}")
                
                # Search Google Maps
                businesses = await self.scrape_google_maps(location, category, max_per_category)
                logger.info(f"Found {len(businesses)} businesses in {category}")
                
                # Enrich with emails and social media
                if businesses:
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
        print(f"\n{'='*70}")
        print(f"SEARCH COMPLETE!")
        print(f"{'='*70}")
        print(f"Total businesses found: {len(businesses)}")
        print(f"Businesses with emails: {len(df[df['email'] != 'N/A'])}")
        print(f"Businesses with websites: {len(df[df['website'] != 'N/A'])}")
        print(f"Businesses with Facebook: {len(df[df['facebook'] != 'N/A'])}")
        print(f"Businesses with Instagram: {len(df[df['instagram'] != 'N/A'])}")
        print(f"\nBreakdown by category:")
        for category in df['category'].unique():
            count = len(df[df['category'] == category])
            with_email = len(df[(df['category'] == category) & (df['email'] != 'N/A')])
            print(f"  {category}: {count} businesses ({with_email} with emails)")
        print(f"\n📁 Results saved to: {output_file}")
        print(f"{'='*70}\n")


async def main():
    """Main function to run the business finder"""
    parser = argparse.ArgumentParser(description='Multi-Source Business Finder for Ouachita Parish, LA')
    parser.add_argument('--location', type=str, default='Ouachita Parish, LA',
                       help='Location to search (default: Ouachita Parish, LA)')
    parser.add_argument('--categories', nargs='+', required=True,
                       help='Categories to search (e.g., "Lawyers" "Coffee Shops" "Restaurants")')
    parser.add_argument('--max-per-category', type=int, default=30,
                       help='Maximum businesses per category (default: 30)')
    parser.add_argument('--out', type=str, default='ouachita_businesses.xlsx',
                       help='Output Excel file name (default: ouachita_businesses.xlsx)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode (saves HTML and screenshots)')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    
    args = parser.parse_args()
    
    logger.info(f"Starting business search for {args.location}")
    logger.info(f"Categories: {', '.join(args.categories)}")
    logger.info(f"Max per category: {args.max_per_category}")
    if args.debug:
        logger.info("Debug mode enabled")
    
    finder = BusinessFinder(headless=args.headless, debug=args.debug)
    
    businesses = await finder.search_all_categories(
        location=args.location,
        categories=args.categories,
        max_per_category=args.max_per_category
    )
    
    finder.export_to_excel(businesses, args.out)


if __name__ == '__main__':
    asyncio.run(main())
