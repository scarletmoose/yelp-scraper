# 🎉 Yelp Business Finder - FREE Setup Guide

## What This Does

This tool uses **Yelp's FREE API** (5,000 calls/day) to find businesses, then automatically visits their websites to extract:
- ✅ Email addresses (especially decision-makers)
- ✅ Facebook profiles  
- ✅ Instagram profiles
- ✅ Phone numbers and addresses (from Yelp)
- ✅ Yelp ratings and reviews

## Step 1: Get Your FREE Yelp API Key (5 minutes)

### Go to Yelp Developers
1. Visit: **https://www.yelp.com/developers**
2. Click **"Get Started"** or **"Create App"**

### Sign Up or Log In
3. Create a free Yelp account or log in

### Create Your App
4. Click **"Create New App"**
5. Fill in the form:
   - **App Name**: "Business Finder" (or any name)
   - **Industry**: Select anything
   - **Contact Email**: Your email
   - **Description**: "Finding local businesses"
   - **Website**: Can be anything (or leave blank)
6. Agree to terms and click **"Create App"**

### Copy Your API Key
7. You'll see your **API Key** - it looks like: `abcDEF123xyz...`
8. **Copy this key** - you'll need it in the next step!

## Step 2: Install Browser (One-Time Setup)

The tool needs a browser to visit websites and extract emails. Run this once:

```bash
playwright install chromium
```

This downloads the browser (takes 1-2 minutes). You only need to do this once.

## Step 3: Add API Key to Replit

### Add as Secret (Secure Method)
1. In Replit, look for the **Tools** panel on the left
2. Click the **🔒 Secrets** icon (lock icon)
3. Click **"New secret"**
4. Enter:
   - **Key**: `YELP_API_KEY`
   - **Value**: Paste your API key from Yelp
5. Click **"Add new secret"**

That's it! Your API key is now securely stored.

## Step 4: Run Your First Search!

Now you can find businesses with a simple command:

### Example 1: Find Restaurants
```bash
python yelp_business_finder.py --categories "Restaurants"
```

### Example 2: Find Multiple Categories
```bash
python yelp_business_finder.py --categories "Lawyers" "Accountants" "Insurance Agents"
```

### Example 3: Customize Everything
```bash
python yelp_business_finder.py \
  --location "Monroe, LA" \
  --categories "Coffee Shops" "Restaurants" "Bars" \
  --max-per-category 30 \
  --out my_businesses.xlsx
```

### Example 4: Fast Mode (Skip Email Extraction)
```bash
python yelp_business_finder.py --categories "Plumbers" --no-enrich
```
This only gets Yelp data (faster) without visiting websites for emails.

## What You'll Get

The tool creates an Excel file with:

| Column | Description | Source |
|--------|-------------|--------|
| Category | Business category | You specify |
| Name | Business name | Yelp |
| Phone | Phone number | Yelp |
| Email | Email address | Website scraping |
| Address | Street address | Yelp |
| City, State, ZIP | Location | Yelp |
| Website | Business website | Web search |
| Yelp URL | Yelp listing | Yelp |
| Rating | Yelp rating (1-5) | Yelp |
| Review Count | Number of reviews | Yelp |
| Facebook | Facebook profile | Website scraping |
| Instagram | Instagram profile | Website scraping |

## Tips for Best Results

### 1. Be Specific with Categories
- ✅ Good: "Italian Restaurants", "Personal Injury Lawyers", "Auto Repair"
- ❌ Too broad: "Food", "Services", "Stores"

### 2. Start Small
Test with 10-20 businesses first:
```bash
python yelp_business_finder.py --categories "Dentists" --max-per-category 20
```

### 3. Use Yelp's Category Names
Yelp works best with standard category names:
- Restaurants, Bars, Coffee Shops
- Lawyers, Attorneys, Accountants
- Plumbers, Electricians, HVAC
- Dentists, Doctors, Chiropractors
- Auto Repair, Car Wash, Tire Shops

### 4. Adjust Location if Needed
```bash
python yelp_business_finder.py --location "West Monroe, LA" --categories "Restaurants"
```

### 5. Speed vs Completeness
- **With enrichment** (default): Slower, but gets emails/social media
- **Without enrichment** (`--no-enrich`): Faster, Yelp data only

## Common Commands

### Get all restaurants with full contact info:
```bash
python yelp_business_finder.py --categories "Restaurants" --max-per-category 50
```

### Get professional services quickly (no email extraction):
```bash
python yelp_business_finder.py \
  --categories "Lawyers" "Accountants" "Real Estate Agents" \
  --max-per-category 30 \
  --no-enrich \
  --out professional_services.xlsx
```

### Get retail businesses:
```bash
python yelp_business_finder.py \
  --categories "Clothing Stores" "Furniture Stores" "Hardware Stores" \
  --out retail.xlsx
```

## Troubleshooting

### "YELP API KEY NOT FOUND"
- Make sure you added the secret exactly as `YELP_API_KEY`
- Check that you pasted the full API key (it's long!)
- Try restarting the workflow

### "Invalid Yelp API key"
- Double-check you copied the API key correctly
- Make sure there are no extra spaces
- Verify your Yelp app is active

### Not finding emails?
- Some businesses don't list emails publicly
- Businesses without websites can't have emails extracted
- Try with `--no-enrich` to see if you get the basic data

### Not many results?
- Try different category names
- Make sure the location has those types of businesses
- Yelp returns up to 50 businesses per category

## API Limits

Yelp's FREE tier gives you:
- **5,000 API calls per day**
- Each category search = 1 API call
- Email/social extraction doesn't count toward Yelp limit

**Example**: Searching 10 categories = only 10 API calls!

## What's Next?

Once you have your business list:
1. Review the Excel file
2. Remove any irrelevant entries
3. Verify important emails before outreach
4. Import into your CRM or email tool
5. Start reaching out!

## Need Help?

If you encounter issues, just ask! I can help you:
- Debug API key problems
- Adjust search parameters
- Filter or organize your results
- Extract specific data

---

**Ready to start?** Just run:
```bash
python yelp_business_finder.py --categories "Your Category Here"
```

Happy business hunting! 🚀
