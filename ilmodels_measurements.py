#!/usr/bin/env python3
import os, logging, threading, time, requests
from flask import Flask, jsonify, send_file
from bs4 import BeautifulSoup

app = Flask(__name__, static_folder='.', static_url_path='')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

models_cache = []
cache_lock = threading.Lock()

# Sample fallback data
SAMPLE_MODELS = [
    {'Name': 'סופיה', 'URL': 'https://www.ilmodel.com/models/model/1', 'Height': '174', 'Bust': '84', 'Waist': '64', 'Hips': '88', 'Bra': '75D', 'Shirt': 'XS', 'Pants': '26', 'Shoe': '37', 'EyeColor': 'כחול', 'HairColor': 'חום', 'Tattoos': '', 'EarPiercings': ''},
    {'Name': 'אורית', 'URL': 'https://www.ilmodel.com/models/model/2', 'Height': '176', 'Bust': '86', 'Waist': '62', 'Hips': '90', 'Bra': '80C', 'Shirt': 'S', 'Pants': '25', 'Shoe': '38', 'EyeColor': 'ירוק', 'HairColor': 'שחור', 'Tattoos': '', 'EarPiercings': ''},
    {'Name': 'שרה', 'URL': 'https://www.ilmodel.com/models/model/3', 'Height': '172', 'Bust': '82', 'Waist': '63', 'Hips': '86', 'Bra': '75C', 'Shirt': 'XS', 'Pants': '26', 'Shoe': '37', 'EyeColor': 'חום', 'HairColor': 'בלונד', 'Tattoos': '', 'EarPiercings': ''},
]

def fetch_models_live():
    """Scrape real models from ilmodel.com"""
    try:
        logger.info("🚀 Starting live scrape...")
        all_models = []

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        logger.info("📄 Fetching models page...")
        response = requests.get(
            'https://www.ilmodel.com/models',
            headers=headers,
            timeout=20
        )

        logger.info(f"Status: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all model links
            model_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                name = link.get_text(strip=True)

                if name and len(name) > 1 and ('model' in href.lower() or '/models/' in href):
                    if not href.startswith('http'):
                        href = 'https://www.ilmodel.com' + (href if href.startswith('/') else '/models/' + href)

                    model_links.append((name, href))

            # Remove duplicates
            model_links = list(dict.fromkeys(model_links))
            logger.info(f"✅ Found {len(model_links)} models")

            # Fetch first 10 models
            for idx, (name, url) in enumerate(model_links[:10]):
                try:
                    logger.info(f"[{idx+1}] {name}")
                    response = requests.get(url, headers=headers, timeout=10)

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        page_text = soup.get_text()

                        # Create model entry
                        model = {
                            'Name': name,
                            'URL': url,
                            'Height': '', 'Bust': '', 'Waist': '', 'Hips': '',
                            'Bra': '', 'Shirt': '', 'Pants': '', 'Shoe': '',
                            'EyeColor': '', 'HairColor': '', 'Tattoos': '', 'EarPiercings': ''
                        }
                        all_models.append(model)
                        logger.info(f"   ✅ Added")

                    time.sleep(0.5)

                except Exception as e:
                    logger.warning(f"   ⚠️ {str(e)[:50]}")

            with cache_lock:
                models_cache.clear()
                models_cache.extend(all_models if all_models else SAMPLE_MODELS)

            logger.info(f"✅ Complete: {len(all_models)} models")

        else:
            logger.error(f"❌ Bad status: {response.status_code}")
            with cache_lock:
                models_cache.clear()
                models_cache.extend(SAMPLE_MODELS)

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        with cache_lock:
            models_cache.clear()
            models_cache.extend(SAMPLE_MODELS)

@app.route('/api/models')
def api_models():
    with cache_lock:
        data = models_cache if models_cache else SAMPLE_MODELS
    return jsonify(data)

@app.route('/')
def index():
    return send_file('index.html')

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8081))

    logger.info("🎯 Starting server...")

    # Start with sample data
    with cache_lock:
        models_cache.extend(SAMPLE_MODELS)

    # Start scraping in background
    scrape_thread = threading.Thread(target=fetch_models_live, daemon=True)
    scrape_thread.start()

    logger.info(f"🌐 Listening on port {PORT}")
    app.run(debug=False, port=PORT, host='0.0.0.0', use_reloader=False)
