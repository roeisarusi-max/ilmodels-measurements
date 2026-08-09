#!/usr/bin/env python3
import os, logging, threading, time, requests, json
from flask import Flask, jsonify, send_file
from bs4 import BeautifulSoup

app = Flask(__name__, static_folder='.', static_url_path='')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

MODELS_FILE = 'models_data.json'
models_cache = []
cache_lock = threading.Lock()

def save_models_to_file(models):
    """Save models to JSON file"""
    try:
        with open(MODELS_FILE, 'w', encoding='utf-8') as f:
            json.dump(models, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Saved {len(models)} models to {MODELS_FILE}")
    except Exception as e:
        logger.error(f"❌ Failed to save file: {e}")

def load_models_from_file():
    """Load models from JSON file"""
    try:
        if os.path.exists(MODELS_FILE):
            with open(MODELS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"✅ Loaded {len(data)} models from file")
            return data
    except Exception as e:
        logger.error(f"⚠️ Failed to load file: {e}")
    return []

def extract_measurements(page_text):
    """Extract measurements from page text"""
    measurements = {
        'Height': '', 'Bust': '', 'Waist': '', 'Hips': '',
        'Bra': '', 'Shirt': '', 'Pants': '', 'Shoe': '',
        'EyeColor': '', 'HairColor': '', 'Tattoos': '', 'EarPiercings': ''
    }

    lines = page_text.split('\n')
    for line in lines:
        line_clean = line.strip()
        if any(k in line for k in measurements.keys()):
            for key in measurements.keys():
                if key in line:
                    val = line.split(key)[-1].strip().split()[0] if key in line else ''
                    if val and val not in ['—', '']:
                        measurements[key] = val
                    break

    return measurements

def fetch_all_models():
    """Scrape all models from all categories"""
    try:
        logger.info("=" * 70)
        logger.info("🚀 STARTING FULL SCRAPE - ALL CATEGORIES")
        logger.info("=" * 70)

        all_models = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Step 1: Get all category links
        logger.info("📂 Step 1: Fetching categories...")
        try:
            response = requests.get('https://www.ilmodel.com/models', headers=headers, timeout=15)
            logger.info(f"   Status: {response.status_code}")

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract all model links from main page
                model_links = {}
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    name = link.get_text(strip=True)

                    if name and len(name) > 1:
                        # Check if it's a category or model link
                        if '/models/' in href and 'model/' in href.lower():
                            if not href.startswith('http'):
                                href = 'https://www.ilmodel.com' + (href if href.startswith('/') else '/' + href)

                            # Use name as ID to avoid duplicates
                            if name not in model_links:
                                model_links[name] = href

                logger.info(f"   ✅ Found {len(model_links)} model links")

                # Step 2: Fetch each model's details
                logger.info("👥 Step 2: Fetching model details...")
                for idx, (name, url) in enumerate(list(model_links.items())[:30]):  # Limit to 30
                    try:
                        logger.info(f"   [{idx+1}/{min(30, len(model_links))}] {name}")

                        response = requests.get(url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            page_text = soup.get_text()
                            measurements = extract_measurements(page_text)

                            model = {
                                'Name': name,
                                'URL': url,
                                'Height': measurements.get('Height', ''),
                                'Bust': measurements.get('Bust', ''),
                                'Waist': measurements.get('Waist', ''),
                                'Hips': measurements.get('Hips', ''),
                                'Bra': measurements.get('Bra', ''),
                                'Shirt': measurements.get('Shirt', ''),
                                'Pants': measurements.get('Pants', ''),
                                'Shoe': measurements.get('Shoe', ''),
                                'EyeColor': measurements.get('EyeColor', ''),
                                'HairColor': measurements.get('HairColor', ''),
                                'Tattoos': measurements.get('Tattoos', ''),
                                'EarPiercings': measurements.get('EarPiercings', ''),
                            }
                            all_models.append(model)
                            logger.info(f"       ✅ Added")

                        time.sleep(0.3)
                    except Exception as e:
                        logger.warning(f"       ⚠️ {str(e)[:50]}")

                # Step 3: Save to file and cache
                if all_models:
                    save_models_to_file(all_models)
                    with cache_lock:
                        globals()['models_cache'].clear()
                        globals()['models_cache'].extend(all_models)
                    logger.info("=" * 70)
                    logger.info(f"✅ COMPLETE: {len(all_models)} models fetched & saved")
                    logger.info("=" * 70)
                else:
                    logger.warning("⚠️ No models found, loading from file...")
                    saved_models = load_models_from_file()
                    with cache_lock:
                        globals()['models_cache'].clear()
                        globals()['models_cache'].extend(saved_models)

        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            saved_models = load_models_from_file()
            with cache_lock:
                globals()['models_cache'].clear()
                globals()['models_cache'].extend(saved_models)

    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")

@app.route('/api/models')
def api_models():
    """Return models from cache or file"""
    with cache_lock:
        data = models_cache if models_cache else load_models_from_file()

    logger.info(f"📊 API: Returning {len(data)} models")
    return jsonify(data)

@app.route('/')
def index():
    return send_file('index.html')

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8081))

    logger.info("🎯 Server starting...")

    # Load existing data
    with cache_lock:
        models_cache.extend(load_models_from_file())

    # Start background scraping
    logger.info("🚀 Starting background scrape thread...")
    scrape_thread = threading.Thread(target=fetch_all_models, daemon=True)
    scrape_thread.start()

    logger.info(f"🌐 Listening on port {PORT}")
    app.run(debug=False, port=PORT, host='0.0.0.0', use_reloader=False)
