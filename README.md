# Business Finder for Ouachita Parish, Louisiana

## 🎉 NEW: Yelp Business Finder (100% FREE - RECOMMENDED!)

**Use `yelp_business_finder.py` for the best results!**

This tool uses Yelp's FREE API (5,000 calls/day) to find verified business data, then automatically extracts emails and social media from their websites.

### Quick Start:
1. Get a FREE Yelp API key (see `YELP_SETUP.md`)
2. Add it as a secret in Replit
3. Run: `python yelp_business_finder.py --categories "Restaurants" "Lawyers"`

**See `YELP_SETUP.md` for complete setup instructions.**

---

# Alternative Tools (Web Scraping - Currently Blocked)

A powerful Python tool that finds business contact information using web search and multiple online sources. Automatically extracts email addresses (prioritizing decision-makers), phone numbers, addresses, and social media profiles.

## Features

✅ **Multi-Source Search**: Uses Google Maps and web search for comprehensive results  
✅ **Email Extraction**: Automatically finds email addresses by visiting business websites  
✅ **Decision-Maker Emails**: Prioritizes owner@, ceo@, manager@, president@ addresses  
✅ **Social Media Detection**: Finds Facebook and Instagram profiles  
✅ **Multi-Category Support**: Search multiple business categories at once  
✅ **Excel Export**: Results organized by category in separate sheets  
✅ **Smart Deduplication**: Prevents duplicate businesses in results  
✅ **Stealth Mode**: Advanced anti-detection measures

## Quick Start

### Basic Usage

Find lawyers and coffee shops in Ouachita Parish:

```bash
python business_finder.py --categories "Lawyers" "Coffee Shops"
```

### Advanced Usage

```bash
python business_finder.py \
  --location "Monroe, LA" \
  --categories "Restaurants" "Plumbers" "Real Estate Agents" \
  --max-per-category 50 \
  --out my_results.xlsx
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--location` | Location to search | "Ouachita Parish, LA" |
| `--categories` | List of categories (required) | - |
| `--max-per-category` | Max businesses per category | 30 |
| `--out` | Output Excel filename | "ouachita_businesses.xlsx" |
| `--debug` | Enable debug mode (saves HTML/screenshots) | False |
| `--headless` | Run browser in headless mode | True |

## Examples

### Example 1: Get all restaurants with contact info
```bash
python business_finder.py --categories "Restaurants" --max-per-category 50
```

### Example 2: Professional services outreach list
```bash
python business_finder.py \
  --categories "Accountants" "Lawyers" "Financial Advisors" "Insurance Agents" \
  --max-per-category 40 \
  --out professional_services.xlsx
```

### Example 3: Home services contractors
```bash
python business_finder.py \
  --categories "Plumbers" "Electricians" "HVAC" "Roofers" "Landscaping" \
  --out home_services.xlsx
```

### Example 4: Retail businesses
```bash
python business_finder.py \
  --categories "Clothing Stores" "Furniture Stores" "Hardware Stores" \
  --out retail_businesses.xlsx
```

### Example 5: Debug mode to troubleshoot
```bash
python business_finder.py --categories "Dentists" --debug
```

## Output Format

The tool creates an Excel file with:

- **All Businesses** sheet: Complete list of all found businesses
- **Category sheets**: Separate sheet for each category

### Excel Columns:
| Column | Description |
|--------|-------------|
| Category | Business category |
| Name | Business name |
| Phone | Phone number |
| Email | Email address (prioritizes decision-makers) |
| Address | Street address |
| City, State, ZIP | Location details |
| Website | Business website URL |
| Facebook | Facebook profile URL |
| Instagram | Instagram profile URL |

## Popular Business Categories

**Professional Services:**
- Lawyers, Attorneys, Law Firms
- Accountants, CPAs, Bookkeepers
- Real Estate Agents, Realtors
- Insurance Agents, Insurance Agencies
- Financial Advisors, Financial Planners
- Consultants, Business Consultants

**Home Services:**
- Plumbers, Plumbing Services
- Electricians, Electrical Contractors
- HVAC, Air Conditioning, Heating
- Roofers, Roofing Contractors
- Landscaping Services, Lawn Care
- Pest Control
- House Cleaning Services

**Retail:**
- Clothing Stores, Boutiques
- Furniture Stores
- Hardware Stores
- Auto Dealers, Car Dealerships
- Jewelry Stores
- Sporting Goods

**Food & Beverage:**
- Restaurants
- Coffee Shops, Cafes
- Bars, Nightclubs
- Catering Services
- Food Trucks

**Health & Wellness:**
- Dentists, Dental Clinics
- Physicians, Doctors
- Chiropractors
- Fitness Centers, Gyms
- Beauty Salons, Hair Salons
- Spa Services
- Physical Therapists

**Automotive:**
- Auto Repair, Mechanics
- Car Wash Services
- Tire Shops
- Auto Body Shops

**Construction:**
- General Contractors
- Home Builders
- Remodeling Contractors
- Painters

## Tips for Best Results

1. **Be Specific**: Use specific categories like "Italian Restaurants" instead of just "Restaurants"
2. **Start Small**: Test with 1-2 categories first to see the data quality
3. **Check Websites**: Businesses with websites yield better email/social results
4. **Use Debug Mode**: If results seem off, enable `--debug` to see what's being scraped
5. **Increase Max**: For comprehensive lists, increase `--max-per-category` to 50+
6. **Review Results**: Always review the Excel file for accuracy before outreach

## Legal & Ethical Use

⚠️ **Important**: 
- This tool is for legitimate business purposes only
- Respect anti-spam laws (CAN-SPAM Act, GDPR, etc.)
- Only contact businesses with relevant, valuable offers
- Honor opt-out requests immediately
- Use collected data responsibly and ethically

## Troubleshooting

### No Results Found
- Try different category names (e.g., "Attorneys" instead of "Lawyers")
- Verify the location has businesses in that category
- Check your internet connection

### Few Emails Found
- Many businesses don't list emails publicly
- Ensure businesses have websites (no website = no email extraction)
- Some websites hide emails behind contact forms

### Debug Mode
Enable debug mode to see what's happening:
```bash
python business_finder.py --categories "Test Category" --debug
```
This saves HTML files and screenshots for inspection.

## How It Works

1. **Search**: Queries Google Maps for businesses in the specified category and location
2. **Extract**: Collects business name, phone, address, and website from listings
3. **Enrich**: Visits each business website to find:
   - Email addresses (prioritizing decision-maker emails)
   - Facebook and Instagram profiles
4. **Deduplicate**: Removes duplicate entries
5. **Export**: Organizes everything in an Excel file by category

## Installation

Dependencies are automatically installed. Manual installation:

```bash
pip install -r requirements.txt
playwright install chromium
```

## Project Structure

```
.
├── business_finder.py     # Main search tool (NEW - recommended)
├── yp_scraper.py         # Legacy Yellow Pages scraper
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Support

Check the console output for detailed logging. The tool provides progress updates and error messages to help diagnose issues.

## Pro Tips

- **Batch Processing**: Search related categories together for efficiency
- **Data Validation**: Cross-reference important contacts before outreach
- **CRM Import**: Most CRMs can import Excel files directly
- **Follow-up**: Keep track of who you've contacted in a separate spreadsheet
