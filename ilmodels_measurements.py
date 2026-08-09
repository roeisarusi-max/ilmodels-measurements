#!/usr/bin/env python3
import os, threading, logging, requests, re, time
from flask import Flask, jsonify, send_file
from bs4 import BeautifulSoup

app = Flask(__name__, static_folder='.', static_url_path='')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models_cache = []
cache_lock = threading.Lock()

def extract_measurements(text):
    """Extract all measurement fields from model page text"""
    measurements = {
        'Height': '', 'Bust': '', 'Waist': '', 'Hips': '',
        'Bra': '', 'Shirt': '', 'Pants': '', 'Shoe': '',
        'EyeColor': '', 'HairColor': '', 'Tattoos': '', 'EarPiercings': ''
    }

    lines = text.split('\n')
    for line in lines:
        line_clean = line.strip()

        # Look for measurement patterns
        if 'Height' in line and '|' in line:
            parts = line.split('|')
            for part in parts:
                part = part.strip()
                if part.startswith('Height'):
                    val = part.replace('Height', '').strip()
                    measurements['Height'] = val.split()[0] if val else ''
                elif part.startswith('Bust'):
                    val = part.replace('Bust', '').strip()
                    measurements['Bust'] = val.split()[0] if val else ''
                elif part.startswith('Waist'):
                    val = part.replace('Waist', '').strip()
                    measurements['Waist'] = val.split()[0] if val else ''
                elif part.startswith('Hips'):
                    val = part.replace('Hips', '').strip()
                    measurements['Hips'] = val.split()[0] if val else ''

        # Single line patterns
        if line_clean.startswith('Bra'):
            measurements['Bra'] = line_clean.replace('Bra', '').strip()
        elif line_clean.startswith('Shirt'):
            measurements['Shirt'] = line_clean.replace('Shirt', '').strip()
        elif line_clean.startswith('Pants'):
            measurements['Pants'] = line_clean.replace('Pants', '').strip()
        elif line_clean.startswith('Shoe'):
            measurements['Shoe'] = line_clean.replace('Shoe', '').strip()
        elif 'Eye Color' in line_clean or 'Eye' in line_clean and 'color' in line_clean.lower():
            measurements['EyeColor'] = line_clean.split(':', 1)[-1].strip() if ':' in line_clean else line_clean.replace('Eye', '').replace('color', '').strip()
        elif 'Hair Color' in line_clean or 'Hair' in line_clean and 'color' in line_clean.lower():
            measurements['HairColor'] = line_clean.split(':', 1)[-1].strip() if ':' in line_clean else line_clean.replace('Hair', '').replace('color', '').strip()
        elif 'Tattoo' in line_clean:
            measurements['Tattoos'] = 'כן' if any(x in line_clean.lower() for x in ['yes', 'כן', 'true', '✓']) else 'אין'
        elif 'Piercing' in line_clean or ('Ear' in line_clean and 'Piercing' in line_clean):
            measurements['EarPiercings'] = 'כן' if any(x in line_clean.lower() for x in ['yes', 'כן', 'true', '✓']) else 'אין'

    return measurements

def fetch_models():
    """Scrape models from ilmodel.com"""
    try:
        logger.info("🚀 Starting scrape...")
        all_models = []

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        # Get list of models
        logger.info("📄 Fetching models page...")
        response = requests.get('https://www.ilmodel.com/models', headers=headers, timeout=30)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all model links
        model_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'model/' in href or '/models/' in href:
                name = link.get_text(strip=True)
                if name and len(name) > 1:
                    if not href.startswith('http'):
                        href = 'https://www.ilmodel.com' + href if href.startswith('/') else 'https://www.ilmodel.com/models/' + href
                    model_links.append((name, href))

        # Remove duplicates
        model_links = list(dict.fromkeys(model_links))
        logger.info(f"✅ Found {len(model_links)} models")

        # Fetch each model's details
        for idx, (name, url) in enumerate(model_links[:50]):  # Limit to 50 for speed
            try:
                logger.info(f"[{idx+1}/{min(50, len(model_links))}] {name}")

                response = requests.get(url, headers=headers, timeout=30)
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
                time.sleep(0.5)  # Rate limit
            except Exception as e:
                logger.warning(f"⚠️ Failed {name}: {str(e)[:50]}")

        with cache_lock:
            globals()['models_cache'] = all_models

        logger.info(f"✅ Scrape complete. Total: {len(all_models)} models")
    except Exception as e:
        logger.error(f"❌ Scrape error: {str(e)[:100]}")

@app.route('/api/models')
def api_models():
    with cache_lock:
        if not models_cache:
            return jsonify({'error': 'טוען...'}), 503
        return jsonify(models_cache)

@app.route('/')
def index():
    return send_file('index.html')

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8081))

    logger.info('🎯 Starting Flask server...')
    threading.Thread(target=fetch_models, daemon=True).start()

    app.run(debug=False, port=PORT, host='0.0.0.0')
