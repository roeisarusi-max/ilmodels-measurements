#!/usr/bin/env python3
"""
Scrapes real models from ilmodel.com
Extracts: Name, Height, Bust, Waist, Hips, Bra, Shirt, Pants, Shoe,
          Eye Color, Hair Color, Tattoos, Ear Piercings
Saves to models_data.json - updates daily
"""

import json
import time
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    print("❌ Playwright not installed. Install: pip install playwright")
    print("   Then run: playwright install")

def extract_measurements(text):
    """Extract measurements from model page text"""
    data = {
        'Height': '', 'Bust': '', 'Waist': '', 'Hips': '',
        'Bra': '', 'Shirt': '', 'Pants': '', 'Shoe': '',
        'EyeColor': '', 'HairColor': '', 'Tattoos': '', 'EarPiercings': ''
    }

    # Look for patterns like "Height 171" or "Height | 171"
    lines = text.split('\n')
    for line in lines:
        line_strip = line.strip()

        # Parse measurement lines
        if 'Height' in line_strip:
            try:
                val = line_strip.split('Height')[-1].split('|')[0].strip().split()[0]
                data['Height'] = val
            except:
                pass
        elif 'Bust' in line_strip:
            try:
                val = line_strip.split('Bust')[-1].split('|')[0].strip().split()[0]
                data['Bust'] = val
            except:
                pass
        elif 'Waist' in line_strip:
            try:
                val = line_strip.split('Waist')[-1].split('|')[0].strip().split()[0]
                data['Waist'] = val
            except:
                pass
        elif 'Hips' in line_strip:
            try:
                val = line_strip.split('Hips')[-1].split('|')[0].strip().split()[0]
                data['Hips'] = val
            except:
                pass
        elif 'Bra' in line_strip or 'bra' in line_strip:
            try:
                val = line_strip.split('Bra')[-1].split('|')[0].split('bra')[-1].strip().split()[0]
                data['Bra'] = val
            except:
                pass
        elif 'Shirt' in line_strip:
            try:
                val = line_strip.split('Shirt')[-1].split('|')[0].strip().split()[0]
                data['Shirt'] = val
            except:
                pass
        elif 'Pants' in line_strip:
            try:
                val = line_strip.split('Pants')[-1].split('|')[0].strip().split()[0]
                data['Pants'] = val
            except:
                pass
        elif 'Shoe' in line_strip:
            try:
                val = line_strip.split('Shoe')[-1].split('|')[0].strip().split()[0]
                data['Shoe'] = val
            except:
                pass
        elif 'Eye Color' in line_strip or 'eye color' in line_strip:
            try:
                val = line_strip.split('Eye Color')[-1].split('eye color')[-1].split('|')[0].strip().split()[0]
                data['EyeColor'] = val
            except:
                pass
        elif 'Hair Color' in line_strip or 'hair color' in line_strip:
            try:
                val = line_strip.split('Hair Color')[-1].split('hair color')[-1].split('|')[0].strip().split()[0]
                data['HairColor'] = val
            except:
                pass
        elif 'Tattoo' in line_strip:
            data['Tattoos'] = 'yes' if any(x in line_strip.lower() for x in ['yes', 'true', '✓']) else 'no'
        elif 'Piercing' in line_strip or 'piercing' in line_strip:
            try:
                val = line_strip.split('Piercing')[-1].split('piercing')[-1].split('|')[0].strip()
                data['EarPiercings'] = val if val else ''
            except:
                pass

    return data

def scrape_with_playwright():
    """Scrape using Playwright (handles JavaScript)"""

    print("=" * 80)
    print(f"🚀 SCRAPING ILMODEL.COM WITH PLAYWRIGHT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    if not HAS_PLAYWRIGHT:
        print("❌ Playwright not available. Cannot proceed.")
        return []

    all_models = []

    try:
        with sync_playwright() as p:
            print("\n🌐 Starting browser...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Go to main models page
            print("📄 Loading https://www.ilmodel.com/models")
            page.goto('https://www.ilmodel.com/models', wait_until='domcontentloaded')
            page.wait_for_load_state('networkidle')
            time.sleep(2)

            # Find all model links
            print("\n🔗 Finding model links...")
            model_links = {}

            # Get all links
            links = page.query_selector_all('a')
            print(f"   Found {len(links)} total links")

            for link in links:
                try:
                    href = link.get_attribute('href')
                    text = link.inner_text()

                    if href and text and len(text) > 1:
                        if 'model' in href.lower() and '/models/' in href:
                            full_url = 'https://www.ilmodel.com' + href if href.startswith('/') else href
                            if text not in model_links and len(text) < 50:
                                model_links[text] = full_url

                except:
                    pass

            print(f"   ✅ Found {len(model_links)} model links")

            # Fetch each model
            print("\n👥 Fetching model details...")
            for idx, (name, url) in enumerate(list(model_links.items())[:50]):  # Limit to 50
                try:
                    print(f"   [{idx+1}] {name}...", end=" ", flush=True)

                    page.goto(url, wait_until='domcontentloaded')
                    page.wait_for_load_state('networkidle')
                    time.sleep(1)

                    # Get page content
                    content = page.content()
                    page_text = page.inner_text()

                    # Extract title (model name) from heading
                    title_elem = page.query_selector('h1, h2, [class*="title"], [class*="name"]')
                    if title_elem:
                        title = title_elem.inner_text().strip()
                    else:
                        title = name

                    # Extract measurements
                    measurements = extract_measurements(page_text)

                    model = {
                        'Name': title,
                        'URL': url,
                        'Height': measurements['Height'],
                        'Bust': measurements['Bust'],
                        'Waist': measurements['Waist'],
                        'Hips': measurements['Hips'],
                        'Bra': measurements['Bra'],
                        'Shirt': measurements['Shirt'],
                        'Pants': measurements['Pants'],
                        'Shoe': measurements['Shoe'],
                        'EyeColor': measurements['EyeColor'],
                        'HairColor': measurements['HairColor'],
                        'Tattoos': measurements['Tattoos'],
                        'EarPiercings': measurements['EarPiercings']
                    }

                    all_models.append(model)
                    print("✅")

                except Exception as e:
                    print(f"❌ {str(e)[:30]}")

            browser.close()

            # Save to file
            print(f"\n💾 Saving {len(all_models)} models to models_data.json...")
            with open('models_data.json', 'w', encoding='utf-8') as f:
                json.dump(all_models, f, ensure_ascii=False, indent=2)

            print("\n" + "=" * 80)
            print(f"✅ SUCCESS: {len(all_models)} MODELS SAVED")
            print(f"📝 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)

            return all_models

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == '__main__':
    if not HAS_PLAYWRIGHT:
        print("\n📦 Installing Playwright...")
        import subprocess
        subprocess.run(['pip', 'install', 'playwright'], check=False)
        subprocess.run(['playwright', 'install'], check=False)
        print("\n✅ Playwright installed. Run script again.")
    else:
        scrape_with_playwright()
