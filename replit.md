# Business Finder for Ouachita Parish, Louisiana

## Project Overview
This project contains multiple Python-based tools to find business contact information in Ouachita Parish, Louisiana. The goal is to collect comprehensive business data including contact details, email addresses (especially decision-makers), and social media profiles for advertising outreach purposes.

## Recent Changes
- **2025-11-01**: Initial project setup and iterations
  - Created `yp_scraper.py` - Yellow Pages scraper (encountering anti-bot blocks)
  - Created `business_finder.py` - Google Maps-based scraper (encountering anti-bot blocks)
  - Created `business_search.py` - Bing search-based finder (simplest approach)
  - Implemented comprehensive email extraction prioritizing decision-makers
  - Added social media profile detection (Facebook, Instagram)
  - Set up Excel export with category organization
  - Configured command-line interfaces for all tools

## Key Features
1. **Multi-Source Search**: Three different tools targeting different sources
2. **Email Extraction**: Visits business websites to find owner/decision-maker email addresses
3. **Email Prioritization**: Prioritizes owner@, ceo@, president@, manager@, info@ addresses
4. **Social Media Detection**: Automatically finds Facebook and Instagram profiles
5. **Multi-Category Support**: Can search multiple business categories in one run
6. **Excel Export**: Organizes results by category in separate sheets
7. **Stealth Mode**: Anti-detection measures to avoid blocking
8. **Deduplication**: Automatically removes duplicate businesses

## Available Tools

### 1. business_search.py (Recommended - Simplest)
Uses Bing search + website scraping. Most straightforward approach.
```bash
python business_search.py --categories "Lawyers" "Restaurants" --max-per-category 20
```

### 2. business_finder.py 
Uses Google Maps scraping. More comprehensive but may face blocking.
```bash
python business_finder.py --categories "Coffee Shops" --max-per-category 30
```

### 3. yp_scraper.py
Uses Yellow Pages scraping. Alternative source.
```bash
python yp_scraper.py --categories "Plumbers" --pages 3
```

## ✅ RECOMMENDED SOLUTION: Yelp Business Finder

**NEW Tool**: `yelp_business_finder.py` - Uses Yelp's FREE API (5,000 calls/day)

This is the best approach because:
- ✅ 100% FREE (no cost, no credit card)
- ✅ 5,000 API calls per day
- ✅ Verified, high-quality business data from Yelp
- ✅ Includes ratings and review counts
- ✅ Automatically enriches with emails and social media
- ✅ No anti-bot blocking issues
- ✅ Legal and compliant

**Setup**: See `YELP_SETUP.md` for step-by-step instructions to get your free API key.

## Other Tools (Web Scraping - Currently Blocked)

The web scraping tools (Yellow Pages, Google Maps, Bing) encounter anti-bot protections that block automated access. These are available as fallback options but currently return empty results without proxy/CAPTCHA services.

## Project Architecture
- **business_search.py**: Bing search + website scraping (simplest)
- **business_finder.py**: Google Maps-based search
- **yp_scraper.py**: Yellow Pages scraper
- **Dependencies**: Playwright, pandas, beautifulsoup4, openpyxl, fake-useragent
- **Output**: Excel files with organized business data

## Usage Examples

### Search for professional services:
```bash
python business_search.py \
  --location "Monroe Louisiana" \
  --categories "Lawyers" "Accountants" "Insurance Agents" \
  --max-per-category 25 \
  --out professional_services.xlsx
```

### Search for restaurants:
```bash
python business_search.py \
  --categories "Restaurants" "Coffee Shops" "Bars" \
  --max-per-category 30 \
  --out food_businesses.xlsx
```

## Technical Details
- Uses async/await patterns for efficient scraping
- Implements random delays to mimic human behavior
- Prioritizes decision-maker emails (owner@, ceo@, manager@, etc.)
- Handles errors gracefully with detailed logging
- Exports to Excel with multiple sheets per category
- Deduplicates businesses across sources

## User Preferences
- Need email addresses (especially decision-makers)
- Need social media profiles (Facebook, Instagram)
- Need contact info organized by business category
- Target: Ouachita Parish, Louisiana businesses
- Purpose: Advertising outreach
