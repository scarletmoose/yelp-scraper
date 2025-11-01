#!/usr/bin/env python3
"""
Yelp Business Finder for Ouachita Parish, Louisiana
Uses Yelp Fusion API (FREE) to find businesses, then enriches with emails and social media
"""

import argparse
import asyncio
import os
import re
import requests
from typing import List, Dict, Optional
from urllib.parse import urljoin
import pandas as pd
from playwright.async_api import async_playwright, Browser
from bs4 import BeautifulSoup
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YelpBusinessFinder:
    """Find businesses using Yelp API and enrich with email/social media"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.browser: Optional[Browser] = None
        self.context = None
        self.base_url = "https://api.yelp.com/v3"
        
    def search_businesses(self, location: str, category: str, limit: int = 50) -> List[Dict]:
        """Search Yelp for businesses"""
        logger.info(f"Searching Yelp API for: {category} in {location}")
        
        headers = {
            'Authorization': f'Bearer {self.api_key}'
        }
        
        params = {
            'location': location,
            'term': category,
            'limit': min(limit, 50),  # Yelp max is 50 per request
            'sort_by': 'best_match'
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/businesses/search",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                businesses = data.get('businesses', [])
                logger.info(f"Found {len(businesses)} businesses from Yelp")
                return businesses
            elif response.status_code == 401:
                logger.error("Invalid Yelp API key. Please check your API key.")
                return []
            else:
                logger.error(f"Yelp API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error calling Yelp API: {str(e)}")
            return []
    
    def parse_yelp_business(self, yelp_data: dict, category: str) -> Dict:
        """Parse Yelp business data into our format"""
        # Extract address
        address = ''
        city_state_zip = ''
        
        if yelp_data.get('location'):
            loc = yelp_data['location']
            if loc.get('address1'):
                address = loc['address1']
                if loc.get('address2'):
                    address += f" {loc['address2']}"
            
            city = loc.get('city', '')
            state = loc.get('state', '')
            zip_code = loc.get('zip_code', '')
            city_state_zip = f"{city}, {state} {zip_code}".strip()
        
        # Format phone number
        phone = yelp_data.get('display_phone', 'N/A')
        if not phone:
            phone = yelp_data.get('phone', 'N/A')
        
        return {
            'category': category,
            'name': yelp_data.get('name', 'N/A'),
            'phone': phone,
            'email': 'N/A',  # Will be enriched
            'address': address or 'N/A',
            'city_state_zip': city_state_zip or 'N/A',
            'website': yelp_data.get('url', 'N/A'),  # Yelp URL
            'yelp_url': yelp_data.get('url', 'N/A'),
            'rating': yelp_data.get('rating', 'N/A'),
            'review_count': yelp_data.get('review_count', 0),
            'facebook': 'N/A',  # Will be enriched
            'instagram': 'N/A',  # Will be enriched
        }
    
    async def init_browser(self):
        """Initialize browser for website scraping"""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        logger.info("Browser initialized for email/social extraction")
    
    async def get_business_website(self, business_name: str, location: str) -> Optional[str]:
        """Search for business website"""
        page = await self.context.new_page()
        
        try:
            # Search for business website
            query = f"{business_name} {location} official website"
            search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
            
            await page.goto(search_url, wait_until='domcontentloaded', timeout=10000)
            await asyncio.sleep(1)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find first result
            result = soup.find('li', class_='b_algo')
            if result:
                link = result.find('a')
                if link and link.get('href'):
                    url = link.get('href')
                    if url.startswith('http'):
                        return url
            
        except Exception as e:
            logger.debug(f"Error finding website for {business_name}: {e}")
        finally:
            await page.close()
        
        return None
    
    async def extract_email_and_social(self, url: str) -> Dict[str, str]:
        """Extract email and social media from website"""
        result = {
            'email': 'N/A',
            'facebook': 'N/A',
            'instagram': 'N/A'
        }
        
        if not url or url == 'N/A' or 'yelp.com' in url:
            return result
        
        page = await self.context.new_page()
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=10000)
            await asyncio.sleep(1)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract email (prioritize decision-makers)
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, content)
            
            filtered_emails = [
                email for email in emails
                if not any(x in email.lower() for x in [
                    'example.com', 'wix.com', 'wordpress', 'schema.org',
                    '.png', '.jpg', 'sentry', 'analytics', 'privacy'
                ])
            ]
            
            # Prioritize decision-maker emails
            priority_prefixes = ['owner', 'ceo', 'president', 'manager', 'director',
                               'info', 'contact', 'hello', 'admin', 'sales']
            
            for email in filtered_emails:
                prefix = email.split('@')[0].lower()
                if any(p in prefix for p in priority_prefixes):
                    result['email'] = email
                    break
            
            if result['email'] == 'N/A' and filtered_emails:
                result['email'] = filtered_emails[0]
            
            # Extract social media
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href'].lower()
                if 'facebook.com' in href and result['facebook'] == 'N/A':
                    result['facebook'] = link['href']
                if 'instagram.com' in href and result['instagram'] == 'N/A':
                    result['instagram'] = link['href']
            
        except Exception as e:
            logger.debug(f"Error extracting from {url}: {e}")
        finally:
            await page.close()
        
        return result
    
    async def enrich_businesses(self, businesses: List[Dict]) -> List[Dict]:
        """Enrich business data with emails and social media"""
        logger.info(f"Enriching {len(businesses)} businesses with email/social data...")
        
        await self.init_browser()
        
        try:
            for idx, business in enumerate(businesses, 1):
                logger.info(f"[{idx}/{len(businesses)}] Enriching: {business['name']}")
                
                # First, try to find actual business website (not Yelp URL)
                website = await self.get_business_website(
                    business['name'],
                    business['city_state_zip']
                )
                
                if website:
                    business['website'] = website
                    logger.info(f"  Found website: {website}")
                    
                    # Extract email and social
                    contact_info = await self.extract_email_and_social(website)
                    business['email'] = contact_info['email']
                    business['facebook'] = contact_info['facebook']
                    business['instagram'] = contact_info['instagram']
                    
                    if contact_info['email'] != 'N/A':
                        logger.info(f"  ✓ Found email: {contact_info['email']}")
                    if contact_info['facebook'] != 'N/A':
                        logger.info(f"  ✓ Found Facebook")
                    if contact_info['instagram'] != 'N/A':
                        logger.info(f"  ✓ Found Instagram")
                else:
                    logger.info(f"  No website found")
                
                await asyncio.sleep(1)
        
        finally:
            if self.browser:
                await self.browser.close()
        
        return businesses
    
    async def find_businesses(self, location: str, categories: List[str], 
                            max_per_category: int = 50, 
                            enrich: bool = True) -> List[Dict]:
        """Find businesses using Yelp API and optionally enrich"""
        all_businesses = []
        
        for category in categories:
            logger.info(f"\n{'='*70}\nSearching Yelp: {category} in {location}\n{'='*70}")
            
            # Get businesses from Yelp
            yelp_results = self.search_businesses(location, category, max_per_category)
            
            # Parse Yelp data
            businesses = [self.parse_yelp_business(b, category) for b in yelp_results]
            
            if businesses and enrich:
                # Enrich with emails and social media
                businesses = await self.enrich_businesses(businesses)
            
            all_businesses.extend(businesses)
            logger.info(f"Total businesses for {category}: {len(businesses)}")
        
        return all_businesses
    
    def export_to_excel(self, businesses: List[Dict], output_file: str):
        """Export to Excel"""
        if not businesses:
            logger.warning("No businesses to export")
            return
        
        logger.info(f"Exporting {len(businesses)} businesses to {output_file}")
        
        df = pd.DataFrame(businesses)
        
        # Reorder columns
        column_order = ['category', 'name', 'phone', 'email', 'address', 'city_state_zip',
                       'website', 'yelp_url', 'rating', 'review_count', 
                       'facebook', 'instagram']
        column_order = [col for col in column_order if col in df.columns]
        df = df[column_order]
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='All Businesses', index=False)
            
            for category in df['category'].unique():
                category_df = df[df['category'] == category]
                safe_name = category[:31]
                category_df.to_excel(writer, sheet_name=safe_name, index=False)
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"✅ SEARCH COMPLETE!")
        print(f"{'='*70}")
        print(f"Total businesses found: {len(businesses)}")
        print(f"Businesses with emails: {len(df[df['email'] != 'N/A'])}")
        print(f"Businesses with websites: {len(df[df['website'] != 'N/A'])}")
        print(f"Businesses with Facebook: {len(df[df['facebook'] != 'N/A'])}")
        print(f"Businesses with Instagram: {len(df[df['instagram'] != 'N/A'])}")
        print(f"Average Yelp rating: {df['rating'].mean():.1f}")
        print(f"\nBreakdown by category:")
        for category in df['category'].unique():
            count = len(df[df['category'] == category])
            with_email = len(df[(df['category'] == category) & (df['email'] != 'N/A')])
            avg_rating = df[df['category'] == category]['rating'].mean()
            print(f"  {category}: {count} businesses ({with_email} with emails, avg rating: {avg_rating:.1f})")
        print(f"\n📁 Results saved to: {output_file}")
        print(f"{'='*70}\n")


async def main():
    parser = argparse.ArgumentParser(
        description='Yelp Business Finder for Ouachita Parish, LA (FREE API)'
    )
    parser.add_argument('--location', type=str, default='Monroe, LA',
                       help='Location to search (default: Monroe, LA)')
    parser.add_argument('--categories', nargs='+', required=True,
                       help='Categories to search (e.g., "Restaurants" "Lawyers")')
    parser.add_argument('--max-per-category', type=int, default=50,
                       help='Max businesses per category (default: 50, max: 50)')
    parser.add_argument('--out', type=str, default='yelp_businesses.xlsx',
                       help='Output Excel file (default: yelp_businesses.xlsx)')
    parser.add_argument('--no-enrich', action='store_true',
                       help='Skip email/social extraction (faster, Yelp data only)')
    
    args = parser.parse_args()
    
    # Get API key from environment
    api_key = 'quf_p0UY4Obo0VgCVy-14RKpJEzy1g43nwbIc-b1azFb9P3inZ3xhuJJnek850pys6NMH415DsTM42fApN9bBtPcuWB2OOEcnNccehB_6rHvOT2ma9Rmax7Vg0sGaXYx'
    
    if not api_key:
        print("\n" + "="*70)
        print("⚠️  YELP API KEY NOT FOUND")
        print("="*70)
        print("\nTo use this tool, you need a FREE Yelp API key.")
        print("\n📝 How to get your FREE Yelp API key:")
        print("   1. Go to: https://www.yelp.com/developers")
        print("   2. Click 'Get Started' or 'Create App'")
        print("   3. Sign up or log in (free)")
        print("   4. Create an app (any name works)")
        print("   5. Copy your API Key")
        print("\n🔐 Once you have your key, add it as a secret:")
        print("   - Click the 'Secrets' tool in the left sidebar (🔒)")
        print("   - Add a new secret:")
        print("     Key: YELP_API_KEY")
        print("     Value: <paste your API key here>")
        print("\nThen run this script again!")
        print("="*70 + "\n")
        return
    
    logger.info(f"Starting Yelp business search for {args.location}")
    logger.info(f"Categories: {', '.join(args.categories)}")
    logger.info(f"Max per category: {args.max_per_category}")
    
    if args.no_enrich:
        logger.info("Email/social enrichment DISABLED (faster)")
    else:
        logger.info("Email/social enrichment ENABLED")
    
    finder = YelpBusinessFinder(api_key)
    
    businesses = await finder.find_businesses(
        location=args.location,
        categories=args.categories,
        max_per_category=args.max_per_category,
        enrich=not args.no_enrich
    )
    
    finder.export_to_excel(businesses, args.out)


if __name__ == '__main__':
    asyncio.run(main())
