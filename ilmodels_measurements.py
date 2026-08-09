#!/usr/bin/env python3
import os, threading, logging, requests, time
from flask import Flask, jsonify, send_file
from bs4 import BeautifulSoup

app = Flask(__name__, static_folder='.', static_url_path='')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

models_cache = []
cache_lock = threading.Lock()

# Dummy data to show while loading
DUMMY_MODELS = [
    {
        'Name': 'טוען דוגמניות...',
        'URL': '#',
        'Height': '—', 'Bust': '—', 'Waist': '—', 'Hips': '—',
        'Bra': '—', 'Shirt': '—', 'Pants': '—', 'Shoe': '—',
        'EyeColor': '—', 'HairColor': '—', 'Tattoos': '', 'EarPiercings': ''
    }
]

def extract_measurements(text):
    """Extract measurements from model page"""
    measurements = {
        'Height': '', 'Bust': '', 'Waist': '', 'Hips': '',
        'Bra': '', 'Shirt': '', 'Pants': '', 'Shoe': '',
        'EyeColor': '', 'HairColor': '', 'Tattoos': '', 'EarPiercings': ''
    }

    lines = text.split('\n')
    for line in lines:
        line_clean = line.strip()

        # Measurement patterns
        if 'Height' in line and '|' in line:
            parts = line.split('|')
            for part in parts:
                part = part.strip()
                if part.startswith('Height'):
                    val = part.replace('Height', '').strip()
                    measurements['Height'] = (val.split()[0] if val else '')
                elif part.startswith('Bust'):
                    val = part.replace('Bust', '').strip()
                    measurements['Bust'] = (val.split()[0] if val else '')
                elif part.startswith('Waist'):
                    val = part.replace('Waist', '').strip()
                    measurements['Waist'] = (val.split()[0] if val else '')
                elif part.startswith('Hips'):
                    val = part.replace('Hips', '').strip()
                    measurements['Hips'] = (val.split()[0] if val else '')

        # Individual fields
        if line_clean.startswith('Bra'):
            measurements['Bra'] = line_clean.replace('Bra', '').strip()
        elif line_clean.startswith('Shirt'):
            measurements['Shirt'] = line_clean.replace('Shirt', '').strip()
        elif line_clean.startswith('Pants'):
            measurements['Pants'] = line_clean.replace('Pants', '').strip()
        elif line_clean.startswith('Shoe'):
            measurements['Shoe'] = line_clean.replace('Shoe', '').strip()

    return measurements

def fetch_models():
    """Scrape models from ilmodel.com with timeout"""
    try:
        logger.info("🚀 Scraping started")
        all_models = []
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            logger.info("📄 Fetching model list...")
            response = requests.get('https://www.ilmodel.com/models', headers=headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract model links
            model_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'model/' in href or '/models/' in href:
                    name = link.get_text(strip=True)
                    if name and len(name) > 1:
                        if not href.startswith('http'):
                            href = 'https://www.ilmodel.com' + href if href.startswith('/') else 'https://www.ilmodel.com/models/' + href
                        model_links.append((name, href))

            model_links = list(dict.fromkeys(model_links))
            logger.info(f"✅ Found {len(model_links)} models")

            # Fetch details (timeout after 30 seconds of scraping)
            start_time = time.time()
            MAX_SCRAPE_TIME = 30  # 30 seconds max

            for idx, (name, url) in enumerate(model_links[:30]):
                if time.time() - start_time > MAX_SCRAPE_TIME:
                    logger.info(f"⏱ Scrape timeout reached. Got {len(all_models)} models")
                    break

                try:
                    logger.info(f"[{idx+1}] {name}")
                    response = requests.get(url, headers=headers, timeout=10)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_text = soup.get_text()

                    measurements = extract_measurements(page_text)

                    model = {
                        'Name': name,
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
                        'EarPiercings': measurements['EarPiercings'],
                    }

                    all_models.append(model)
                    time.sleep(0.3)

                except Exception as e:
                    logger.warning(f"⚠️ {name}: {str(e)[:40]}")

        except requests.exceptions.Timeout:
            logger.error("❌ Request timeout")
        except Exception as e:
            logger.error(f"❌ Error: {str(e)[:100]}")

        with cache_lock:
            globals()['models_cache'] = all_models if all_models else DUMMY_MODELS

        logger.info(f"✅ Complete: {len(all_models)} models")

    except Exception as e:
        logger.error(f"❌ Fatal: {str(e)}")
        with cache_lock:
            globals()['models_cache'] = DUMMY_MODELS

@app.route('/api/models')
def api_models():
    with cache_lock:
        return jsonify(models_cache if models_cache else DUMMY_MODELS)

@app.route('/')
def index():
    return send_file('index.html')

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8081))

    logger.info('🎯 Starting server...')
    with cache_lock:
        globals()['models_cache'] = DUMMY_MODELS

    threading.Thread(target=fetch_models, daemon=True).start()

    app.run(debug=False, port=PORT, host='0.0.0.0')
