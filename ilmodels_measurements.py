#!/usr/bin/env python3
import os, threading, logging, time
from flask import Flask, jsonify, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

app = Flask(__name__, static_folder='.', static_url_path='')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

models_cache = []
cache_lock = threading.Lock()

# Dummy data
DUMMY_MODELS = [
    {
        'Name': 'טוען דוגמניות...',
        'URL': '#',
        'Height': '—', 'Bust': '—', 'Waist': '—', 'Hips': '—',
        'Bra': '—', 'Shirt': '—', 'Pants': '—', 'Shoe': '—',
        'EyeColor': '—', 'HairColor': '—', 'Tattoos': '', 'EarPiercings': ''
    }
]

def get_chrome_options():
    """Configure Chrome options for Railway/headless environment"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
    return chrome_options

def fetch_models():
    """Scrape models using Selenium"""
    global models_cache
    driver = None
    try:
        logger.info("=" * 60)
        logger.info("🚀 SCRAPE START - Using Selenium")
        logger.info("=" * 60)

        # Initialize Chrome driver
        logger.info("🔧 Initializing Chrome WebDriver...")
        chrome_options = get_chrome_options()

        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            logger.error(f"❌ Failed to init Chrome: {str(e)}")
            logger.info("⚠️ Falling back to dummy data")
            with cache_lock:
                models_cache.clear()
                models_cache.extend(DUMMY_MODELS)
            return

        all_models = []

        # Step 1: Load models page
        logger.info("📄 Loading models page...")
        try:
            driver.get('https://www.ilmodel.com/models')
            logger.info("✅ Page loaded")

            # Wait for model links to appear
            logger.info("⏳ Waiting for models to load...")
            wait = WebDriverWait(driver, 10)
            model_elements = wait.until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'a'))
            )
            logger.info(f"✅ Found {len(model_elements)} link elements")

            # Extract model links
            logger.info("🔗 Extracting model links...")
            model_links = []
            for elem in model_elements:
                try:
                    href = elem.get_attribute('href')
                    text = elem.text.strip()
                    if href and text and len(text) > 1 and 'model' in href.lower():
                        if not href.startswith('http'):
                            href = 'https://www.ilmodel.com' + href
                        model_links.append((text, href))
                except:
                    pass

            model_links = list(dict.fromkeys(model_links))
            logger.info(f"✅ Found {len(model_links)} models")

            # Step 2: Fetch each model
            logger.info("👥 Fetching model details...")
            for idx, (name, url) in enumerate(model_links[:15]):  # Limit to 15
                try:
                    logger.info(f"[{idx+1}/15] {name}")
                    driver.get(url)
                    time.sleep(1)  # Let page load

                    # Parse page with BeautifulSoup
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    page_text = soup.get_text()

                    model = {
                        'Name': name,
                        'URL': url,
                        'Height': '', 'Bust': '', 'Waist': '', 'Hips': '',
                        'Bra': '', 'Shirt': '', 'Pants': '', 'Shoe': '',
                        'EyeColor': '', 'HairColor': '', 'Tattoos': '', 'EarPiercings': ''
                    }

                    all_models.append(model)
                    logger.info(f"   ✅ Added")

                except Exception as e:
                    logger.warning(f"   ❌ {str(e)[:50]}")

        except Exception as e:
            logger.error(f"❌ Error during scraping: {str(e)}")

        finally:
            if driver:
                driver.quit()
                logger.info("🛑 Driver closed")

        # Update cache
        logger.info("💾 Updating cache...")
        with cache_lock:
            models_cache.clear()
            models_cache.extend(all_models if all_models else DUMMY_MODELS)

        logger.info("=" * 60)
        logger.info(f"✅ COMPLETE: {len(all_models)} models loaded")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ FATAL: {str(e)}")
        logger.error("=" * 60)
        with cache_lock:
            models_cache.clear()
            models_cache.extend(DUMMY_MODELS)

@app.route('/api/models')
def api_models():
    with cache_lock:
        data = models_cache if models_cache else DUMMY_MODELS
    return jsonify(data)

@app.route('/')
def index():
    return send_file('index.html')

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8081))

    logger.info("🎯 Starting server...")
    with cache_lock:
        models_cache.clear()
        models_cache.extend(DUMMY_MODELS)

    logger.info("🚀 Starting scrape in background...")
    scrape_thread = threading.Thread(target=fetch_models, daemon=True)
    scrape_thread.start()

    logger.info(f"🌐 Listening on port {PORT}")
    app.run(debug=False, port=PORT, host='0.0.0.0', use_reloader=False)
