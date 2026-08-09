#!/usr/bin/env python3
import os, threading, logging, requests, time
from flask import Flask, jsonify, send_file
from bs4 import BeautifulSoup

app = Flask(__name__, static_folder='.', static_url_path='')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

models_cache = []
cache_lock = threading.Lock()
scraping_status = {'status': 'initializing', 'count': 0}

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

def fetch_models():
    """Scrape models from ilmodel.com"""
    global scraping_status
    try:
        scraping_status['status'] = 'starting'
        logger.info("=" * 50)
        logger.info("🚀 SCRAPE START")
        logger.info("=" * 50)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        all_models = []

        # Step 1: Fetch model list page
        logger.info("📄 Step 1: Fetching model list page...")
        try:
            response = requests.get(
                'https://www.ilmodel.com/models',
                headers=headers,
                timeout=20,
                allow_redirects=True
            )
            logger.info(f"   Status: {response.status_code}")
            logger.info(f"   Content length: {len(response.text)} bytes")

            if response.status_code != 200:
                logger.error(f"   ❌ Bad status code: {response.status_code}")
                raise Exception(f"Status {response.status_code}")

            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # Step 2: Extract model links
            logger.info("🔗 Step 2: Extracting model links...")
            model_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                name = link.get_text(strip=True)

                if name and len(name) > 1:
                    if 'model' in href.lower():
                        if not href.startswith('http'):
                            href = 'https://www.ilmodel.com' + href if href.startswith('/') else 'https://www.ilmodel.com/models/' + href
                        model_links.append((name, href))

            model_links = list(dict.fromkeys(model_links))
            logger.info(f"   ✅ Found {len(model_links)} model links")

            if len(model_links) == 0:
                logger.warning("   ⚠️ No model links found! Check if website structure changed")

            # Step 3: Fetch each model
            logger.info("👥 Step 3: Fetching model details...")
            scraping_status['status'] = 'fetching'

            for idx, (name, url) in enumerate(model_links[:20]):  # Reduced to 20 for speed
                try:
                    scraping_status['count'] = idx + 1
                    logger.info(f"   [{idx+1}/{min(20, len(model_links))}] {name}")

                    response = requests.get(url, headers=headers, timeout=10)
                    logger.info(f"       Status: {response.status_code}")

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        page_text = soup.get_text()

                        model = {
                            'Name': name,
                            'URL': url,
                            'Height': '', 'Bust': '', 'Waist': '', 'Hips': '',
                            'Bra': '', 'Shirt': '', 'Pants': '', 'Shoe': '',
                            'EyeColor': '', 'HairColor': '', 'Tattoos': '', 'EarPiercings': ''
                        }

                        all_models.append(model)
                        logger.info(f"       ✅ Added")

                    time.sleep(0.2)

                except requests.exceptions.Timeout:
                    logger.warning(f"       ⏱ Timeout")
                except Exception as e:
                    logger.warning(f"       ❌ Error: {str(e)[:50]}")

        except requests.exceptions.Timeout:
            logger.error("   ❌ Timeout fetching model list")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"   ❌ Connection error: {str(e)[:100]}")
        except Exception as e:
            logger.error(f"   ❌ Error: {str(e)[:100]}")

        # Step 4: Update cache
        logger.info("💾 Step 4: Updating cache...")
        with cache_lock:
            models_cache.clear()
            models_cache.extend(all_models if all_models else DUMMY_MODELS)

        scraping_status['status'] = 'complete'
        logger.info("=" * 50)
        logger.info(f"✅ SCRAPE COMPLETE: {len(all_models)} models")
        logger.info("=" * 50)

    except Exception as e:
        logger.error("=" * 50)
        logger.error(f"❌ FATAL ERROR: {str(e)}")
        logger.error("=" * 50)
        scraping_status['status'] = 'error'
        with cache_lock:
            models_cache.clear()
            models_cache.extend(DUMMY_MODELS)

@app.route('/api/models')
def api_models():
    with cache_lock:
        data = models_cache if models_cache else DUMMY_MODELS
    logger.info(f"API request: returning {len(data)} models (status: {scraping_status.get('status')})")
    return jsonify(data)

@app.route('/')
def index():
    return send_file('index.html')

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8081))

    logger.info("🎯 Flask server starting...")
    with cache_lock:
        models_cache.clear()
        models_cache.extend(DUMMY_MODELS)

    logger.info("🚀 Starting scrape thread...")
    scrape_thread = threading.Thread(target=fetch_models, daemon=True)
    scrape_thread.start()

    logger.info(f"🌐 Listening on port {PORT}")
    app.run(debug=False, port=PORT, host='0.0.0.0', use_reloader=False)
