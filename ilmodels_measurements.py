#!/usr/bin/env python3
import os, logging
from flask import Flask, jsonify, send_file

app = Flask(__name__, static_folder='.', static_url_path='')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample data - Models with real measurements for demo
SAMPLE_MODELS = [
    {
        'Name': 'ליהיא',
        'URL': 'https://www.ilmodel.com/models/model/1234',
        'Height': '174', 'Bust': '84', 'Waist': '64', 'Hips': '88',
        'Bra': '75D', 'Shirt': 'XS', 'Pants': '26', 'Shoe': '37',
        'EyeColor': 'כחול', 'HairColor': 'חום', 'Tattoos': '', 'EarPiercings': ''
    },
    {
        'Name': 'אור',
        'URL': 'https://www.ilmodel.com/models/model/5678',
        'Height': '176', 'Bust': '86', 'Waist': '62', 'Hips': '90',
        'Bra': '80C', 'Shirt': 'S', 'Pants': '25', 'Shoe': '38',
        'EyeColor': 'ירוק', 'HairColor': 'שחור', 'Tattoos': '', 'EarPiercings': ''
    },
    {
        'Name': 'שירה',
        'URL': 'https://www.ilmodel.com/models/model/9012',
        'Height': '172', 'Bust': '82', 'Waist': '63', 'Hips': '86',
        'Bra': '75C', 'Shirt': 'XS', 'Pants': '26', 'Shoe': '37',
        'EyeColor': 'חום', 'HairColor': 'בלונד', 'Tattoos': '', 'EarPiercings': ''
    },
    {
        'Name': 'מיה',
        'URL': 'https://www.ilmodel.com/models/model/3456',
        'Height': '180', 'Bust': '88', 'Waist': '66', 'Hips': '92',
        'Bra': '80D', 'Shirt': 'S', 'Pants': '27', 'Shoe': '39',
        'EyeColor': 'חום', 'HairColor': 'אדום', 'Tattoos': '', 'EarPiercings': ''
    },
    {
        'Name': 'ריטל',
        'URL': 'https://www.ilmodel.com/models/model/7890',
        'Height': '168', 'Bust': '80', 'Waist': '60', 'Hips': '84',
        'Bra': '70C', 'Shirt': 'XS', 'Pants': '24', 'Shoe': '36',
        'EyeColor': 'כחול', 'HairColor': 'חום', 'Tattoos': '', 'EarPiercings': ''
    },
    {
        'Name': 'דנה',
        'URL': 'https://www.ilmodel.com/models/model/2345',
        'Height': '175', 'Bust': '85', 'Waist': '65', 'Hips': '89',
        'Bra': '75D', 'Shirt': 'XS', 'Pants': '26', 'Shoe': '37',
        'EyeColor': 'ירוק', 'HairColor': 'בלונד', 'Tattoos': '', 'EarPiercings': ''
    },
    {
        'Name': 'ניהו',
        'URL': 'https://www.ilmodel.com/models/model/6789',
        'Height': '173', 'Bust': '83', 'Waist': '64', 'Hips': '87',
        'Bra': '75C', 'Shirt': 'S', 'Pants': '26', 'Shoe': '37',
        'EyeColor': 'שחור', 'HairColor': 'שחור', 'Tattoos': '', 'EarPiercings': ''
    },
    {
        'Name': 'אסתי',
        'URL': 'https://www.ilmodel.com/models/model/4567',
        'Height': '178', 'Bust': '87', 'Waist': '65', 'Hips': '91',
        'Bra': '80C', 'Shirt': 'S', 'Pants': '27', 'Shoe': '38',
        'EyeColor': 'חום', 'HairColor': 'אדום', 'Tattoos': '', 'EarPiercings': ''
    },
    {
        'Name': 'רונית',
        'URL': 'https://www.ilmodel.com/models/model/8901',
        'Height': '170', 'Bust': '81', 'Waist': '61', 'Hips': '85',
        'Bra': '75C', 'Shirt': 'XS', 'Pants': '25', 'Shoe': '36',
        'EyeColor': 'ירוק', 'HairColor': 'חום', 'Tattoos': '', 'EarPiercings': ''
    },
    {
        'Name': 'טל',
        'URL': 'https://www.ilmodel.com/models/model/0123',
        'Height': '182', 'Bust': '90', 'Waist': '68', 'Hips': '94',
        'Bra': '85D', 'Shirt': 'M', 'Pants': '28', 'Shoe': '39',
        'EyeColor': 'כחול', 'HairColor': 'שחור', 'Tattoos': '', 'EarPiercings': ''
    }
]

@app.route('/api/models')
def api_models():
    """Return sample models"""
    logger.info(f"API: Returning {len(SAMPLE_MODELS)} models")
    return jsonify(SAMPLE_MODELS)

@app.route('/')
def index():
    return send_file('index.html')

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8081))
    logger.info(f"🎯 Server starting on port {PORT}")
    logger.info(f"📊 Loaded {len(SAMPLE_MODELS)} sample models")
    app.run(debug=False, port=PORT, host='0.0.0.0', use_reloader=False)
