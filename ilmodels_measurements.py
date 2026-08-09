#!/usr/bin/env python3
import os, threading, webbrowser, logging, requests
from flask import Flask, jsonify, send_file
from bs4 import BeautifulSoup
import time

app = Flask(__name__, static_folder='.', static_url_path='')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models_cache = []
cache_lock = threading.Lock()

CATEGORIES = [
    ("WOMEN", "https://www.ilmodel.com/models"),
]

def fetch_models():
    """Scrape models from ilmodel.com"""
    try:
        logger.info("Starting scrape...")
        all_models = []
        
        for cat_name, cat_url in CATEGORIES:
            logger.info(f"Fetching category: {cat_name}")
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(cat_url, headers=headers, timeout=30)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all model links
            model_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if href.startswith('#/'):
                    name = link.get_text(strip=True)
                    if name and len(name) > 1:
                        url = f"https://www.ilmodel.com/models{href}"
                        model_links.append((name, url))
            
            logger.info(f"Found {len(model_links)} models")
            
            # Fetch each model
            for idx, (name, url) in enumerate(model_links[:30]):  # Limit to 30
                try:
                    logger.info(f"[{idx+1}/30] {name}")
                    
                    response = requests.get(url, headers=headers, timeout=30)
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract measurements
                    measurements = {}
                    page_text = soup.get_text()
                    
                    for line in page_text.split('\n'):
                        if 'Height' in line and 'Bust' in line and 'Waist' in line:
                            parts = line.split('|')
                            for part in parts:
                                part = part.strip()
                                tokens = part.split()
                                if len(tokens) >= 2:
                                    key = tokens[0]
                                    value = ' '.join(tokens[1:])
                                    measurements[key] = value
                            break
                    
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
                    }
                    
                    if measurements:
                        all_models.append(model)
                    
                    time.sleep(0.3)
                except Exception as e:
                    logger.warning(f"Failed {name}: {e}")
        
        with cache_lock:
            globals()['models_cache'] = all_models
        
        logger.info(f"Complete. Total: {len(all_models)}")
    except Exception as e:
        logger.error(f"Scrape error: {e}")

@app.route('/api/models')
def api_models():
    with cache_lock:
        if not models_cache:
            return jsonify({'error': 'Loading...'}), 503
        return jsonify(models_cache)

@app.route('/')
def index():
    return send_file('index.html')

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8081))
    IS_LOCAL = not os.environ.get('RAILWAY_ENVIRONMENT')
    
    logger.info('Starting...')
    threading.Thread(target=fetch_models, daemon=True).start()
    
    if IS_LOCAL:
        threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{PORT}')).start()
    
    app.run(debug=False, port=PORT, host='0.0.0.0')
