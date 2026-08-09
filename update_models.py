#!/usr/bin/env python3
"""
Daily updater: Scrapes ALL categories from ilmodel.com
Saves to models_data.json
Runs automatically via GitHub Actions every day
"""

import requests
import json
import time
from bs4 import BeautifulSoup
from datetime import datetime

def scrape_all_categories():
    """Scrape models from all categories on ilmodel.com"""

    print("=" * 80)
    print(f"🚀 SCRAPING ALL CATEGORIES - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    all_models = []
    base_url = 'https://www.ilmodel.com'

    try:
        # Step 1: Get main models page to find all categories
        print("\n📂 Step 1: Finding all categories...")
        response = requests.get(f'{base_url}/models', headers=headers, timeout=20)

        if response.status_code != 200:
            print(f"   ❌ Error: {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all category links
        category_links = {}
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)

            # Look for category links (WOMEN, MEN, KIDS, etc)
            if href and '/models' in href and len(text) > 0:
                full_url = base_url + href if href.startswith('/') else href
                if text not in category_links and text.upper() in ['WOMEN', 'MEN', 'KIDS', 'COUPLES']:
                    category_links[text] = full_url

        print(f"   ✅ Found {len(category_links)} categories")
        for cat_name in category_links:
            print(f"      - {cat_name}")

        # Step 2: For each category, find all models
        print("\n🔗 Step 2: Finding all model links in each category...")
        model_links = {}

        for category, cat_url in category_links.items():
            print(f"\n   📍 Category: {category}")
            try:
                response = requests.get(cat_url, headers=headers, timeout=20)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Find all model links in this category
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        name = link.get_text(strip=True)

                        if name and len(name) > 1 and 'model' in href.lower():
                            full_url = base_url + href if href.startswith('/') else href

                            # Avoid duplicates
                            if name not in model_links and len(name) < 50:
                                model_links[name] = {'url': full_url, 'category': category}

                    print(f"      ✅ Found {len([m for m in model_links if model_links[m]['category'] == category])} models")

                time.sleep(1)

            except Exception as e:
                print(f"      ❌ Error: {str(e)[:50]}")

        print(f"\n   📊 Total unique models found: {len(model_links)}")

        # Step 3: Fetch each model's details
        print("\n👥 Step 3: Fetching model details...")
        model_count = 0

        for idx, (name, info) in enumerate(list(model_links.items())[:100]):  # Limit to 100
            try:
                url = info['url']
                category = info['category']

                if model_count % 10 == 0:
                    print(f"   [{model_count+1}] Fetching details...", end=" ")

                response = requests.get(url, headers=headers, timeout=15)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_text = soup.get_text()

                    # Extract measurements
                    model = {
                        'Name': name,
                        'URL': url,
                        'Category': category,
                        'Height': '',
                        'Bust': '',
                        'Waist': '',
                        'Hips': '',
                        'Bra': '',
                        'Shirt': '',
                        'Pants': '',
                        'Shoe': '',
                        'EyeColor': '',
                        'HairColor': '',
                        'Tattoos': '',
                        'EarPiercings': ''
                    }

                    # Simple text parsing
                    lines = page_text.split('\n')
                    for line in lines:
                        line_clean = line.strip()
                        # Try to extract measurements from visible text
                        for key in ['Height', 'Bust', 'Waist', 'Hips', 'Bra', 'Shoe']:
                            if key in line_clean and len(line_clean) < 100:
                                parts = line_clean.split()
                                for i, part in enumerate(parts):
                                    if key in part and i+1 < len(parts):
                                        model[key] = parts[i+1]
                                        break

                    all_models.append(model)
                    model_count += 1

                    if model_count % 10 == 0:
                        print(f"✅ ({model_count})")

                time.sleep(0.5)

            except Exception as e:
                if model_count % 10 == 0:
                    print(f"⚠️")

        # Step 4: Save to file
        print(f"\n💾 Step 4: Saving {len(all_models)} models to models_data.json...")

        with open('models_data.json', 'w', encoding='utf-8') as f:
            json.dump(all_models, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 80)
        print(f"✅ SUCCESS: {len(all_models)} REAL MODELS SAVED")
        print(f"📝 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        return all_models

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        return []

if __name__ == '__main__':
    scrape_all_categories()
