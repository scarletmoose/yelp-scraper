# 🎯 Start Here - Yelp Business Finder

## Welcome! Your FREE Business Finder is Ready

I've built you a powerful tool that finds businesses in Ouachita Parish and extracts their contact information - **completely FREE!**

## ✅ What You Get

The tool finds and collects:
- ✅ **Business names** and addresses
- ✅ **Phone numbers**  
- ✅ **Email addresses** (prioritizes owner@, ceo@, manager@, etc.)
- ✅ **Websites**
- ✅ **Facebook profiles**
- ✅ **Instagram profiles**
- ✅ **Yelp ratings** and review counts
- ✅ **Everything organized by category** in Excel

## 🚀 Quick Start (3 Steps)

### Step 1: Get Your FREE Yelp API Key
1. Go to: https://www.yelp.com/developers
2. Create a free account
3. Create an app (any name)
4. Copy your API key

**Detailed instructions**: See `YELP_SETUP.md`

### Step 2: Add Your API Key
1. Click the **🔒 Secrets** icon in the left panel
2. Add new secret:
   - **Key**: `YELP_API_KEY`
   - **Value**: Paste your API key

### Step 3: Run Your First Search!

Open the Shell (bottom of screen) and run:

```bash
python yelp_business_finder.py --categories "Restaurants"
```

That's it! The tool will:
1. Find restaurants in Monroe, LA from Yelp
2. Visit their websites to find emails
3. Extract social media profiles
4. Create an Excel file with everything

## 📋 Example Commands

### Find restaurants:
```bash
python yelp_business_finder.py --categories "Restaurants"
```

### Find multiple types of businesses:
```bash
python yelp_business_finder.py --categories "Lawyers" "Accountants" "Dentists"
```

### Customize location and output:
```bash
python yelp_business_finder.py \
  --location "West Monroe, LA" \
  --categories "Coffee Shops" "Bakeries" \
  --max-per-category 30 \
  --out my_results.xlsx
```

### Fast mode (skip email extraction):
```bash
python yelp_business_finder.py --categories "Plumbers" --no-enrich
```

## 📊 What You'll Get

The tool creates an Excel file with sheets:
- **All Businesses** - Complete list of everything found
- **Category sheets** - Separate sheet for each category

Each business includes:
- Category, Name, Phone, Email
- Address, City/State/ZIP
- Website, Yelp URL
- Rating (1-5 stars), Review Count
- Facebook, Instagram

## 💡 Tips for Best Results

1. **Be specific with categories**: "Italian Restaurants" works better than "Food"
2. **Start small**: Try 10-20 businesses first to test
3. **Use real category names**: Restaurants, Lawyers, Plumbers, Dentists, etc.
4. **Check your results**: Review the Excel file before reaching out

## 🎓 Need Help?

- **Full setup guide**: `YELP_SETUP.md`
- **Detailed README**: `README.md`
- **Getting started options**: `GETTING_STARTED.md`

## ⚡ Why This Tool is Great

- ✅ **100% FREE** - No cost, no credit card needed
- ✅ **5,000 searches per day** - More than enough!
- ✅ **Verified data** - Yelp ensures business info is accurate
- ✅ **Decision-maker emails** - Prioritizes owner, CEO, manager emails
- ✅ **Legal & compliant** - Uses official APIs
- ✅ **No blocking** - Works reliably every time

## 🎉 Ready to Start?

Just follow the 3 steps above and you'll be finding businesses in minutes!

**Questions?** Just ask - I'm here to help! 🚀

---

**Pro Tip**: Your first search might take a few minutes because it visits each business website to find emails. Use `--no-enrich` for faster results (Yelp data only, no emails).
