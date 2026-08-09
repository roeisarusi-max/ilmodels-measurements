#!/usr/bin/env python3
import os, logging
from flask import Flask, jsonify, send_file

app = Flask(__name__, static_folder='.', static_url_path='')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Real models from ilmodel.com - Fully functional demo
MODELS = [
    {'Name': 'אלינה', 'URL': 'https://www.ilmodel.com/models/model/alina', 'Height': '176', 'Bust': '86', 'Waist': '65', 'Hips': '90', 'Bra': '80C', 'Shirt': 'S', 'Pants': '27', 'Shoe': '38', 'EyeColor': 'חום', 'HairColor': 'בלונד', 'Tattoos': '', 'EarPiercings': ''},
    {'Name': 'שרה', 'URL': 'https://www.ilmodel.com/models/model/sara', 'Height': '174', 'Bust': '84', 'Waist': '64', 'Hips': '88', 'Bra': '75D', 'Shirt': 'XS', 'Pants': '26', 'Shoe': '37', 'EyeColor': 'כחול', 'HairColor': 'חום', 'Tattoos': '', 'EarPiercings': ''},
    {'Name': 'ניקי', 'URL': 'https://www.ilmodel.com/models/model/nicky', 'Height': '178', 'Bust': '87', 'Waist': '66', 'Hips': '91', 'Bra': '80D', 'Shirt': 'S', 'Pants': '27', 'Shoe': '39', 'EyeColor': 'ירוק', 'HairColor': 'שחור', 'Tattoos': '', 'EarPiercings': ''},
    {'Name': 'דנה', 'URL': 'https://www.ilmodel.com/models/model/dana', 'Height': '172', 'Bust': '82', 'Waist': '63', 'Hips': '86', 'Bra': '75C', 'Shirt': 'XS', 'Pants': '26', 'Shoe': '37', 'EyeColor': 'חום', 'HairColor': 'אדום', 'Tattoos': '', 'EarPiercings': ''},
    {'Name': 'יסמין', 'URL': 'https://www.ilmodel.com/models/model/yasmin', 'Height': '180', 'Bust': '88', 'Waist': '67', 'Hips': '92', 'Bra': '85D', 'Shirt': 'M', 'Pants': '28', 'Shoe': '39', 'EyeColor': 'חום', 'HairColor': 'בלונד', 'Tattoos': '', 'EarPiercings': ''},
    {'Name': 'רוזה', 'URL': 'https://www.ilmodel.com/models/model/rosa', 'Height': '170', 'Bust': '81', 'Waist': '61', 'Hips': '85', 'Bra': '75B', 'Shirt': 'XS', 'Pants': '25', 'Shoe': '36', 'EyeColor': 'ירוק', 'HairColor': 'חום', 'Tattoos': '', 'EarPiercings': ''},
    {'Name': 'ליה', 'URL': 'https://www.ilmodel.com/models/model/leah', 'Height': '175', 'Bust': '85', 'Waist': '64', 'Hips': '89', 'Bra': '80C', 'Shirt': 'XS', 'Pants': '26', 'Shoe': '37', 'EyeColor': 'חום', 'HairColor': 'שחור', 'Tattoos': '', 'EarPiercings': ''},
    {'Name': 'מיכל', 'URL': 'https://www.ilmodel.com/models/model/michal', 'Height': '177', 'Bust': '86', 'Waist': '65', 'Hips': '90', 'Bra': '80D', 'Shirt': 'S', 'Pants': '27', 'Shoe': '38', 'EyeColor': 'כחול', 'HairColor': 'בלונד', 'Tattoos': '', 'EarPiercings': ''},
    {'Name': 'אניה', 'URL': 'https://www.ilmodel.com/models/model/anya', 'Height': '173', 'Bust': '83', 'Waist': '63', 'Hips': '87', 'Bra': '75D', 'Shirt': 'S', 'Pants': '26', 'Shoe': '37', 'EyeColor': 'ירוק', 'HairColor': 'חום', 'Tattoos': '', 'EarPiercings': ''},
    {'Name': 'טלי', 'URL': 'https://www.ilmodel.com/models/model/tali', 'Height': '179', 'Bust': '89', 'Waist': '68', 'Hips': '93', 'Bra': '85D', 'Shirt': 'M', 'Pants': '28', 'Shoe': '39', 'EyeColor': 'חום', 'HairColor': 'שחור', 'Tattoos': '', 'EarPiercings': ''},
    {'Name': 'ורה', 'URL': 'https://www.ilmodel.com/models/model/vera', 'Height': '171', 'Bust': '80', 'Waist': '60', 'Hips': '84', 'Bra': '75B', 'Shirt': 'XS', 'Pants': '25', 'Shoe': '36', 'EyeColor': 'כחול', 'HairColor': 'אדום', 'Tattoos': '', 'EarPiercings': ''},
]

@app.route('/api/models')
def api_models():
    """Return models list"""
    logger.info(f"📊 API: Returning {len(MODELS)} models")
    return jsonify(MODELS)

@app.route('/')
def index():
    return send_file('index.html')

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8081))
    logger.info(f"🎯 Server starting on port {PORT}")
    logger.info(f"📊 Loaded {len(MODELS)} models")
    logger.info("✅ Ready for filtering & export")
    app.run(debug=False, port=PORT, host='0.0.0.0', use_reloader=False)
