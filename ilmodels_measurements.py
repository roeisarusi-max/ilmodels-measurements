#!/usr/bin/env python3
import os, logging, json
from flask import Flask, jsonify, send_file

app = Flask(__name__, static_folder='.', static_url_path='')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODELS_FILE = 'models_data.json'

def load_models():
    """Load models from JSON file"""
    try:
        if os.path.exists(MODELS_FILE):
            with open(MODELS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            count = len(data)
            logger.info(f"✅ Loaded {count} models from {MODELS_FILE}")
            return data
    except Exception as e:
        logger.error(f"❌ Error loading file: {e}")
    return []

@app.route('/api/models')
def api_models():
    """Return models"""
    models = load_models()
    logger.info(f"📊 API: Returning {len(models)} models")
    return jsonify(models)

@app.route('/')
def index():
    return send_file('index.html')

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8081))
    logger.info(f"🎯 Starting server on port {PORT}")
    app.run(debug=False, port=PORT, host='0.0.0.0', use_reloader=False)
