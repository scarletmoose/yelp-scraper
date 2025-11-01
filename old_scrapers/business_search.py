#!/usr/bin/env python3
"""
Business Search Tool for Ouachita Parish, Louisiana
Uses web search and intelligent scraping to find business information
"""

import argparse
import asyncio
import re
import json
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
import pandas as pd
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BusinessSearchTool:
    """Simple business search tool using direct web access"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context = None
        self.businesses: List[Dict] = []
        self.seen_businesses: Set[str] = set()
        
    async def init_browser(self):
        """Initialize browser"""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        logger.info("Browser initialized")
    
    async def search_bing(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search Bing for businesses"""
        logger.info(f"Searching Bing for: {query}")
        
        page = await self.context.new_page()
        businesses = []
        
        try:
            # Bing search URL
            search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
            
            await page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract search results
            results = soup.find_all('li', class_='b_algo')
            
            logger.info(f"Found {len(results)} search results")
            
            for result in results[:max_results]:
                try:
                    # Extract title and URL
                    title_elem = result.find('h2')
                    if not title_elem:
                        continue
                    
                    link_elem = title_elem.find('a')
                    if not link_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url = link_elem.get('href', '')
                    
                    # Extract description
                    desc_elem = result.find('p')
                    description = desc_elem.get_text(strip=True) if desc_elem else ''
                    
                    # Try to extract phone from description
                    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', description)
                    phone = phone_match.group() if phone_match else 'N/A'
                    
                    if url and url.startswith('http'):
                        businesses.append({
                            'name': title,
                            'url': url,
                            'phone': phone,
                            'description': description
                        })
                
                except Exception as e:
                    logger.debug(f"Error parsing result: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error searching Bing: {e}")
        finally:
            await page.close()
        
        return businesses
    
    async def extract_contact_info(self, url: str, business_name: str) -> Dict[str, str]:
        """Extract contact information from a business website"""
        contact_info = {
            'phone': 'N/A',
            'email': 'N/A',
            'address': 'N/A',
            'facebook': 'N/A',
            'instagram': 'N/A'
        }
        
        if not url or not url.startswith('http'):
            return contact_info
        
        page = await self.context.new_page()
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=10000)
            await asyncio.sleep(1)
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            text_content = soup.get_text()
            
            # Extract phone
            phone_patterns = [
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                r'\d{3}[-.\s]?\d{4}'
            ]
            for pattern in phone_patterns:
                match = re.search(pattern, text_content)
                if match:
                    contact_info['phone'] = match.group()
                    break
            
            # Extract email (prioritize decision-maker emails)
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, content)
            
            # Filter and prioritize emails
            filtered_emails = [
                email for email in emails
                if not any(x in email.lower() for x in [
                    'example.com', 'wix.com', 'wordpress', 'schema.org',
                    '.png', '.jpg', 'sentry', 'analytics'
                ])
            ]
            
            priority_prefixes = ['owner', 'ceo', 'president', 'manager', 'director',
                               'info', 'contact', 'hello', 'admin']
            
            for email in filtered_emails:
                prefix = email.split('@')[0].lower()
                if any(p in prefix for p in priority_prefixes):
                    contact_info['email'] = email
                    break
            
            if contact_info['email'] == 'N/A' and filtered_emails:
                contact_info['email'] = filtered_emails[0]
            
            # Extract address (simple pattern)
            address_pattern = r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Circle|Cir|Place|Pl)[.,\s]+(?:Monroe|West Monroe|Louisiana|LA)'
            address_match = re.search(address_pattern, text_content, re.IGNORECASE)
            if address_match:
                contact_info['address'] = address_match.group().strip()
            
            # Extract social media
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href'].lower()
                if 'facebook.com' in href and contact_info['facebook'] == 'N/A':
                    contact_info['facebook'] = link['href']
                if 'instagram.com' in href and contact_info['instagram'] == 'N/A':
                    contact_info['instagram'] = link['href']
            
        except Exception as e:
            logger.debug(f"Error extracting from {url}: {e}")
        finally:
            await page.close()
        
        return contact_info
    
    async def find_businesses(self, location: str, categories: List[str], max_per_category: int = 20) -> List[Dict]:
        """Find businesses in specified categories"""
        all_businesses = []
        
        await self.init_browser()
        
        try:
            for category in categories:
                logger.info(f"\n{'='*70}\nSearching: {category} in {location}\n{'='*70}")
                
                # Search query
                query = f"{category} in {location} phone email"
                
                # Get search results
                search_results = await self.search_bing(query, max_per_category * 2)
                
                logger.info(f"Processing {len(search_results)} results for {category}")
                
                found_count = 0
                for idx, result in enumerate(search_results, 1):
                    if found_count >= max_per_category:
                        break
                    
                    # Skip if already seen
                    business_key = f"{result['name']}_{result['url']}"
                    if business_key in self.seen_businesses:
                        continue
                    
                    self.seen_businesses.add(business_key)
                    
                    logger.info(f"  [{found_count + 1}/{max_per_category}] Processing: {result['name']}")
                    
                    # Extract detailed contact info
                    contact_info = await self.extract_contact_info(result['url'], result['name'])
                    
                    # Combine information
                    business = {
                        'category': category,
                        'name': result['name'],
                        'phone': contact_info['phone'] if contact_info['phone'] != 'N/A' else result.get('phone', 'N/A'),
                        'email': contact_info['email'],
                        'address': contact_info['address'],
                        'website': result['url'],
                        'facebook': contact_info['facebook'],
                        'instagram': contact_info['instagram']
                    }
                    
                    # Only add if we have meaningful data
                    if business['phone'] != 'N/A' or business['email'] != 'N/A':
                        all_businesses.append(business)
                        found_count += 1
                        
                        if business['email'] != 'N/A':
                            logger.info(f"    ✓ Found email: {business['email']}")
                        if business['phone'] != 'N/A':
                            logger.info(f"    ✓ Found phone: {business['phone']}")
                    
                    await asyncio.sleep(1)
                
                logger.info(f"Found {found_count} businesses with contact info in {category}")
                await asyncio.sleep(2)
            
        finally:
            if self.browser:
                await self.browser.close()
        
        return all_businesses
    
    def export_to_excel(self, businesses: List[Dict], output_file: str):
        """Export to Excel"""
        if not businesses:
            logger.warning("No businesses to export")
            return
        
        logger.info(f"Exporting {len(businesses)} businesses to {output_file}")
        
        df = pd.DataFrame(businesses)
        
        # Reorder columns
        column_order = ['category', 'name', 'phone', 'email', 'address',  
                       'website', 'facebook', 'instagram']
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
        print(f"SEARCH COMPLETE!")
        print(f"{'='*70}")
        print(f"Total businesses found: {len(businesses)}")
        print(f"Businesses with emails: {len(df[df['email'] != 'N/A'])}")
        print(f"Businesses with phones: {len(df[df['phone'] != 'N/A'])}")
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
    parser = argparse.ArgumentParser(description='Business Search Tool for Ouachita Parish, LA')
    parser.add_argument('--location', type=str, default='Monroe Louisiana',
                       help='Location to search (default: Monroe Louisiana)')
    parser.add_argument('--categories', nargs='+', required=True,
                       help='Categories to search')
    parser.add_argument('--max-per-category', type=int, default=20,
                       help='Maximum businesses per category (default: 20)')
    parser.add_argument('--out', type=str, default='ouachita_businesses.xlsx',
                       help='Output Excel file')
    
    args = parser.parse_args()
    
    logger.info(f"Starting business search for {args.location}")
    logger.info(f"Categories: {', '.join(args.categories)}")
    logger.info(f"Max per category: {args.max_per_category}")
    
    tool = BusinessSearchTool()
    
    businesses = await tool.find_businesses(
        location=args.location,
        categories=args.categories,
        max_per_category=args.max_per_category
    )
    
    tool.export_to_excel(businesses, args.out)


if __name__ == '__main__':
    asyncio.run(main())
