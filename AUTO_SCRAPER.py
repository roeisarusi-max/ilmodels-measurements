#!/usr/bin/env python3
"""
AUTOMATIC SCRAPER - Run on your Mac
Scrapes ALL 60 models from ilmodel.com
No manual work needed!
"""

import json
import time
import re
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
    print("✅ Playwright installed!")
except ImportError:
    print("❌ Playwright not installed")
    print("\n📦 Install it:")
    print("   pip install playwright")
    print("   playwright install")
    exit(1)

def scrape_all_models():
    """Scrape ALL models from ilmodel.com"""

    print("=" * 80)
    print(f"🚀 AUTO-SCRAPING ILMODEL.COM - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    all_models = []

    with sync_playwright() as p:
        print("\n🌐 Starting browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Go to main page
            print("📄 Loading ilmodel.com/models...")
            page.goto('https://www.ilmodel.com/models', wait_until='domcontentloaded')
            page.wait_for_load_state('networkidle')
            time.sleep(2)

            # Get ALL model links from the page
            print("🔗 Finding all model links...")
            links = page.query_selector_all('a[href*="#/"]')
            print(f"   Found {len(links)} total links")

            model_links = []
            for link in links:
                try:
                    href = link.get_attribute('href')
                    text = link.inner_text()
                    if href and '#/' in href and text and len(text) > 1:
                        full_url = 'https://www.ilmodel.com/models' + href
                        if (full_url, text) not in model_links:
                            model_links.append((full_url, text))
                except:
                    pass

            print(f"   ✅ Found {len(model_links)} unique models")

            # Scrape each model
            print(f"\n👥 Scraping {len(model_links)} models...\n")

            for idx, (url, name) in enumerate(model_links):
                try:
                    print(f"[{idx+1}/{len(model_links)}] {name}...", end=" ", flush=True)

                    page.goto(url, wait_until='domcontentloaded')
                    page.wait_for_load_state('networkidle')
                    time.sleep(0.5)

                    # Get page text
                    page_text = page.inner_text()

                    # Find measurements line
                    # Pattern: "Height XXX | Bust XX | ... | Ear Piercings X"
                    pattern = r'Height\s+(\d+)\s*\|\s*Bust\s+(\d+)\s*\|\s*Waist\s+(\d+)\s*\|\s*Hips\s+(\d+)\s*\|\s*Bra\s+([^\|]+)\s*\|\s*Shirt\s+([^\|]+)\s*\|\s*Pants\s+([^\|]+)\s*\|\s*Shoe\s+([^\|]+)\s*\|\s*Eye Color\s+([^\|]+)\s*\|\s*Hair Color\s+([^\|]+)\s*\|\s*Tattoos\s+([^\|]+)\s*\|\s*Ear Piercings\s+(.+?)(?:\||$)'

                    match = re.search(pattern, page_text, re.IGNORECASE)

                    if match:
                        groups = match.groups()
                        model = {
                            'Name': name,
                            'URL': url,
                            'Height': groups[0],
                            'Bust': groups[1],
                            'Waist': groups[2],
                            'Hips': groups[3],
                            'Bra': groups[4].strip(),
                            'Shirt': groups[5].strip(),
                            'Pants': groups[6].strip(),
                            'Shoe': groups[7].strip(),
                            'EyeColor': groups[8].strip(),
                            'HairColor': groups[9].strip(),
                            'Tattoos': groups[10].strip(),
                            'EarPiercings': groups[11].strip()
                        }
                        all_models.append(model)
                        print("✅")
                    else:
                        print("⚠️ (no measurements)")

                except Exception as e:
                    print(f"❌ {str(e)[:30]}")

            browser.close()

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            browser.close()
            return []

    # Save to file
    print(f"\n💾 Saving {len(all_models)} models to models_data.json...")

    with open('models_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_models, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print(f"✅ SUCCESS: {len(all_models)} MODELS SAVED")
    print(f"📝 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return all_models

if __name__ == '__main__':
    models = scrape_all_models()

    if models:
        print("\n📝 Next steps:")
        print("1. git add models_data.json")
        print("2. git commit -m 'Real models from ilmodel.com'")
        print("3. git push")
        print("4. Railway will auto-reload!")
    else:
        print("\n❌ No models scraped. Check your internet connection.")
