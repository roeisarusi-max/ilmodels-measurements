#!/usr/bin/env python3
import os, logging, threading, time, json
from flask import Flask, jsonify, send_file

app = Flask(__name__, static_folder='.', static_url_path='')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

MODELS_FILE = 'models_data.json'
models_cache = []
cache_lock = threading.Lock()

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

def scrape_with_selenium():
    """Scrape ilmodel.com using Selenium"""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from bs4 import BeautifulSoup

        logger.info("=" * 70)
        logger.info("🚀 STARTING REAL DATA SCRAPE WITH SELENIUM")
        logger.info("=" * 70)

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('user-agent=Mozilla/5.0')

        driver = None
        all_models = []

        try:
            logger.info("🔧 Starting Chrome...")
            driver = webdriver.Chrome(options=chrome_options)

            logger.info("📄 Loading ilmodel.com/models...")
            driver.get('https://www.ilmodel.com/models')
            time.sleep(3)

            # Wait for page to load
            logger.info("⏳ Waiting for models to load...")
            wait = WebDriverWait(driver, 15)

            # Try to find model containers
            try:
                elements = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="/model"]'))
                )
                logger.info(f"✅ Found {len(elements)} model links")
            except:
                logger.warning("⚠️ Could not find model links, scraping page content...")
                elements = []

            # Extract models
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Find all links
            model_links = {}
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)

                # Look for model links
                if text and len(text) > 1 and any(x in href.lower() for x in ['model', '/models/']):
                    if not href.startswith('http'):
                        href = 'https://www.ilmodel.com' + (href if href.startswith('/') else '/' + href)

                    # Avoid duplicates
                    if text not in model_links and text not in ['', 'Next', 'Back', '>>']:
                        model_links[text] = href

            logger.info(f"✅ Extracted {len(model_links)} unique model links")

            # Fetch each model
            for idx, (name, url) in enumerate(list(model_links.items())[:20]):  # Limit to 20
                try:
                    logger.info(f"[{idx+1}] Fetching: {name}")
                    driver.get(url)
                    time.sleep(1)

                    page_text = driver.page_source
                    soup = BeautifulSoup(page_text, 'html.parser')
                    full_text = soup.get_text()

                    # Try to extract measurements
                    model = {
                        'Name': name,
                        'URL': url,
                        'Height': '', 'Bust': '', 'Waist': '', 'Hips': '',
                        'Bra': '', 'Shirt': '', 'Pants': '', 'Shoe': '',
                        'EyeColor': '', 'HairColor': '', 'Tattoos': '', 'EarPiercings': ''
                    }

                    # Simple extraction from text
                    for line in full_text.split('\n'):
                        if 'Height' in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if 'Height' in part and i+1 < len(parts):
                                    model['Height'] = parts[i+1]
                                    break

                    all_models.append(model)
                    logger.info(f"   ✅ Added {name}")

                except Exception as e:
                    logger.warning(f"   ⚠️ Error: {str(e)[:50]}")

            if driver:
                driver.quit()

            # Save to file
            if all_models:
                with open(MODELS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(all_models, f, ensure_ascii=False, indent=2)
                logger.info(f"💾 Saved {len(all_models)} models to file")

                with cache_lock:
                    globals()['models_cache'].clear()
                    globals()['models_cache'].extend(all_models)

                logger.info("=" * 70)
                logger.info(f"✅ SCRAPE COMPLETE: {len(all_models)} REAL models")
                logger.info("=" * 70)
            else:
                logger.warning("⚠️ No models found, using file data")

        except Exception as e:
            logger.error(f"❌ Selenium error: {str(e)}")
            if driver:
                driver.quit()

            # Fallback to file
            saved = load_models_from_file()
            with cache_lock:
                globals()['models_cache'].clear()
                globals()['models_cache'].extend(saved)

    except ImportError:
        logger.error("❌ Selenium not available, using file data")
        saved = load_models_from_file()
        with cache_lock:
            globals()['models_cache'].clear()
            globals()['models_cache'].extend(saved)

@app.route('/api/models')
def api_models():
    """Return models"""
    with cache_lock:
        data = models_cache if models_cache else load_models_from_file()
    logger.info(f"📊 API: {len(data)} models")
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

    # Start scraping in background
    logger.info("🚀 Starting Selenium scraper...")
    scrape_thread = threading.Thread(target=scrape_with_selenium, daemon=True)
    scrape_thread.start()

    logger.info(f"🌐 Listening on port {PORT}")
    app.run(debug=False, port=PORT, host='0.0.0.0', use_reloader=False)
