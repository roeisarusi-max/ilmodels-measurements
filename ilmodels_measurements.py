#!/usr/bin/env python3
import os, threading, webbrowser, logging, requests, re
from flask import Flask, jsonify
from bs4 import BeautifulSoup
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models_cache = []
cache_lock = threading.Lock()

CATEGORIES = [
    ("WOMEN", "https://www.ilmodel.com/models"),
]

def parse_measurements(text):
    """Parse measurement text like 'Height 171 | Bust 84 | Waist 64...'"""
    measurements = {}
    if not text:
        return measurements
    
    # Split by pipe
    parts = text.split('|')
    for part in parts:
        part = part.strip()
        # Extract key and value
        tokens = part.split(maxsplit=1)
        if len(tokens) >= 2:
            key = tokens[0]
            value = tokens[1] if len(tokens) > 1 else ""
            measurements[key] = value
    
    return measurements

def fetch_model_details(model_url, model_name):
    """Fetch model details from model page"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(model_url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        logger.info(f"Fetching {model_name}...")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract full page text
        page_text = soup.get_text()
        
        # Find measurements in text - look for pattern with Height
        measurements = {}
        for line in page_text.split('\n'):
            if 'Height' in line and 'Bust' in line:
                measurements = parse_measurements(line)
                if measurements:
                    break
        
        # Extract social links
        instagram = ""
        tiktok = ""
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            if 'instagram' in href:
                instagram = link.get('href', '')
            if 'tiktok' in href:
                tiktok = link.get('href', '')
        
        model = {
            "Name": model_name,
            "שם": model_name,
            "URL": model_url,
            "Height": measurements.get("Height", ""),
            "גובה": measurements.get("Height", ""),
            "Bust": measurements.get("Bust", ""),
            "חזה": measurements.get("Bust", ""),
            "Waist": measurements.get("Waist", ""),
            "מותן": measurements.get("Waist", ""),
            "Hips": measurements.get("Hips", ""),
            "אגן": measurements.get("Hips", ""),
            "Bra": measurements.get("Bra", ""),
            "חזייה": measurements.get("Bra", ""),
            "Shirt": measurements.get("Shirt", ""),
            "חולצה": measurements.get("Shirt", ""),
            "Pants": measurements.get("Pants", ""),
            "מכנסיים": measurements.get("Pants", ""),
            "Shoe": measurements.get("Shoe", ""),
            "נעליים": measurements.get("Shoe", ""),
            "Eye Color": measurements.get("Eye", ""),
            "עיניים": measurements.get("Eye", ""),
            "Hair Color": measurements.get("Hair", ""),
            "שיער": measurements.get("Hair", ""),
            "Tattoos": measurements.get("Tattoos", ""),
            "קעקוע": measurements.get("Tattoos", ""),
            "Ear Piercings": measurements.get("Piercings", ""),
            "עגילים": measurements.get("Piercings", ""),
            "Instagram": instagram,
            "אינסטגרם": instagram,
            "TikTok": tiktok,
            "טיקטוק": tiktok,
        }
        
        return model
    except Exception as e:
        logger.error(f"Error fetching {model_name}: {e}")
        return None

def fetch_category_models(url):
    """Fetch all model links from category"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        model_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href.startswith('#/'):
                model_name = link.get_text(strip=True)
                if model_name and len(model_name) > 1:
                    model_url = f"https://www.ilmodel.com/models{href}"
                    model_links.append((model_name, model_url))
        
        logger.info(f"Found {len(model_links)} models")
        return model_links
    except Exception as e:
        logger.error(f"Error fetching category: {e}")
        return []

def scrape_all_data():
    global models_cache
    logger.info("Starting scrape...")
    all_models = []
    
    try:
        for category_name, category_url in CATEGORIES:
            logger.info(f"Scraping category: {category_name}")
            model_links = fetch_category_models(category_url)
            
            for idx, (name, url) in enumerate(model_links):
                try:
                    logger.info(f"[{idx+1}/{len(model_links)}] {name}")
                    model = fetch_model_details(url, name)
                    if model:
                        all_models.append(model)
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Failed {name}: {e}")
                    continue
    except Exception as e:
        logger.error(f"Scrape error: {e}")
    
    with cache_lock:
        models_cache = all_models
    
    logger.info(f"Scraping complete. Total: {len(models_cache)} models")

@app.route("/api/models")
def api_models():
    with cache_lock:
        if not models_cache:
            return jsonify({"error": "Loading models..."}), 503
        return jsonify(models_cache)

HTML = r"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IL Models</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; color: #222; }
header { background: #1a1a2e; color: white; padding: 16px 28px; }
header h1 { font-size: 20px; font-weight: 700; }
.main { display: flex; min-height: calc(100vh - 56px); }
.sidebar { width: 320px; background: white; border-left: 1px solid #e0e0e0; padding: 16px; overflow-y: auto; max-height: calc(100vh - 56px); }
.sidebar h2 { font-size: 11px; color: #999; margin-top: 16px; margin-bottom: 8px; text-transform: uppercase; }
.filter-group { margin-bottom: 10px; }
.filter-group label { display: block; font-size: 12px; font-weight: 600; color: #555; margin-bottom: 4px; }
.filter-group input, .filter-group select { width: 100%; padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; }
.btn-search { width: 100%; padding: 8px; background: #1a1a2e; color: white; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; margin-top: 12px; }
.btn-reset { width: 100%; padding: 6px; background: #f0f0f0; color: #666; border: none; border-radius: 6px; font-size: 12px; cursor: pointer; margin-top: 6px; }
.btn-export { width: 100%; padding: 6px; background: #2e7d32; color: white; border: none; border-radius: 6px; font-size: 12px; cursor: pointer; margin-top: 6px; }
.btn-export:disabled { background: #ccc; cursor: not-allowed; }
.results { flex: 1; padding: 20px; overflow-y: auto; }
.results-header { font-size: 13px; color: #888; margin-bottom: 14px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.card { background: white; border-radius: 8px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 2px solid #ececec; position: relative; }
.card-checkbox { position: absolute; top: 10px; right: 10px; width: 18px; height: 18px; cursor: pointer; }
.card-name { font-size: 14px; font-weight: 700; color: #1a1a2e; margin-bottom: 8px; margin-top: 20px; }
.card-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 11px; }
.card-field .lbl { color: #999; margin-bottom: 1px; }
.card-field .val { font-weight: 600; color: #333; }
.state-msg { text-align: center; padding: 60px 20px; color: #aaa; }
.modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center; }
.modal.show { display: flex; }
.modal-content { background: white; padding: 25px; border-radius: 10px; max-width: 500px; width: 90%; max-height: 80vh; overflow-y: auto; }
.modal-close { float: right; font-size: 24px; cursor: pointer; font-weight: bold; }
.modal-title { font-size: 16px; font-weight: 700; margin-bottom: 15px; clear: both; }
.modal-links { font-family: monospace; font-size: 11px; line-height: 1.6; background: #f5f5f5; padding: 12px; border-radius: 5px; border: 1px solid #ddd; }
.copy-btn { margin-top: 12px; padding: 8px 16px; background: #1a73e8; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; }
</style>
</head>
<body>
<header><h1>🗂 IL Models – מאגר מידות</h1></header>
<div class="main">
  <div class="sidebar">
    <h2>סינון</h2>
    <div class="filter-group">
      <label>🔍 שם</label>
      <input type="text" id="f-name" placeholder="חיפוש...">
    </div>
    
    <h2>גובה ומידות</h2>
    <div class="filter-group">
      <label>גובה</label>
      <input type="number" id="f-height" placeholder="174" step="0.1">
    </div>
    <div class="filter-group">
      <label>חזה (ס"מ)</label>
      <input type="number" id="f-bust" placeholder="84">
    </div>
    <div class="filter-group">
      <label>מותן (ס"מ)</label>
      <input type="number" id="f-waist" placeholder="64">
    </div>
    <div class="filter-group">
      <label>אגן (ס"מ)</label>
      <input type="number" id="f-hips" placeholder="88">
    </div>
    
    <h2>בגדים ונעליים</h2>
    <div class="filter-group">
      <label>חולצה</label>
      <select id="f-shirt"><option value="">הכל</option><option>XS</option><option>S</option><option>M</option><option>L</option><option>XL</option><option>XXL</option></select>
    </div>
    <div class="filter-group">
      <label>מכנסיים</label>
      <input type="number" id="f-pants" placeholder="34">
    </div>
    <div class="filter-group">
      <label>נעליים</label>
      <input type="number" id="f-shoe" placeholder="37" step="0.5">
    </div>
    <div class="filter-group">
      <label>חזייה</label>
      <input type="text" id="f-bra" placeholder="B/c75">
    </div>
    
    <h2>מראה</h2>
    <div class="filter-group">
      <label>צבע שיער</label>
      <select id="f-hair"><option value="">הכל</option><option>Black</option><option>Brown</option><option>Blonde</option><option>Red</option><option>Auburn</option><option>Other</option></select>
    </div>
    <div class="filter-group">
      <label>צבע עיניים</label>
      <select id="f-eyes"><option value="">הכל</option><option>Blue</option><option>Brown</option><option>Green</option><option>Gray</option><option>Hazel</option><option>Black</option></select>
    </div>
    
    <h2>אחר</h2>
    <div class="filter-group">
      <label>קעקועים</label>
      <select id="f-tattoos"><option value="">הכל</option><option value="yes">יש</option><option value="no">אין</option></select>
    </div>
    <div class="filter-group">
      <label>עגילים</label>
      <input type="text" id="f-piercings" placeholder="1+2">
    </div>
    
    <button class="btn-search" onclick="applyFilters()">🔍 חפש</button>
    <button class="btn-reset" onclick="resetFilters()">🔄 איפוס</button>
    <button class="btn-export" id="exportBtn" onclick="showLinks()" disabled>📋 קבל קישורים</button>
  </div>

  <div class="results">
    <div class="results-header" id="results-header">טוען...</div>
    <div class="grid" id="grid"><div class="state-msg">⏳ טוען...</div></div>
  </div>
</div>

<div id="linksModal" class="modal">
  <div class="modal-content">
    <span class="modal-close" onclick="closeModal()">&times;</span>
    <div class="modal-title">📋 קישורים לשליחה</div>
    <div class="modal-links" id="linksText"></div>
    <button class="copy-btn" onclick="copyToClipboard()">📋 העתק הכל</button>
  </div>
</div>

<script>
let allModels = [];
let selectedModels = new Set();
let currentResults = [];

async function loadData() {
  try {
    const res = await fetch('/api/models');
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    allModels = data;
    applyFilters();
  } catch(e) {
    document.getElementById('grid').innerHTML = '<div class="state-msg">שגיאה: ' + e.message + '</div>';
  }
}

function applyFilters() {
  const name = document.getElementById('f-name').value.toLowerCase();
  const results = allModels.filter(m => {
    if (name && !(m.Name || m.שם || '').toLowerCase().includes(name)) return false;
    return true;
  });
  
  currentResults = results;
  document.getElementById('results-header').textContent = results.length + ' דוגמניות';
  
  if (results.length === 0) {
    document.getElementById('grid').innerHTML = '<div class="state-msg">לא נמצאו תוצאות</div>';
    return;
  }
  
  document.getElementById('grid').innerHTML = results.map((m, idx) => `
    <div class="card">
      <input type="checkbox" class="card-checkbox" data-idx="${idx}" onchange="updateSelection()">
      <div class="card-name">${m.Name || m.שם}</div>
      <div class="card-grid">
        <div><div class="lbl">גובה</div><div class="val">${m.Height || '—'}</div></div>
        <div><div class="lbl">חזה</div><div class="val">${m.Bust || '—'}</div></div>
        <div><div class="lbl">מותן</div><div class="val">${m.Waist || '—'}</div></div>
        <div><div class="lbl">אגן</div><div class="val">${m.Hips || '—'}</div></div>
        <div><div class="lbl">חולצה</div><div class="val">${m.Shirt || '—'}</div></div>
        <div><div class="lbl">נעליים</div><div class="val">${m.Shoe || '—'}</div></div>
        <div><div class="lbl">שיער</div><div class="val">${m['Hair Color'] || '—'}</div></div>
        <div><div class="lbl">קעקועים</div><div class="val">${m.Tattoos || '—'}</div></div>
      </div>
    </div>
  `).join('');
}

function updateSelection() {
  selectedModels.clear();
  document.querySelectorAll('.card-checkbox:checked').forEach(cb => {
    const idx = parseInt(cb.dataset.idx);
    selectedModels.add(idx);
  });
  document.getElementById('exportBtn').disabled = selectedModels.size === 0;
}

function showLinks() {
  const links = [];
  selectedModels.forEach(idx => {
    const model = currentResults[idx];
    if (model) {
      links.push(`${model.Name || model.שם} - ${model.URL}`);
    }
  });
  document.getElementById('linksText').textContent = links.join('\n');
  document.getElementById('linksModal').classList.add('show');
}

function closeModal() {
  document.getElementById('linksModal').classList.remove('show');
}

function copyToClipboard() {
  const text = document.getElementById('linksText').textContent;
  navigator.clipboard.writeText(text).then(() => alert('✅ הועתק!'));
}

function resetFilters() {
  document.querySelectorAll('input, select').forEach(el => el.value = '');
  selectedModels.clear();
  document.querySelectorAll('.card-checkbox').forEach(cb => cb.checked = false);
  updateSelection();
  loadData();
}

loadData();
setInterval(() => { if (allModels.length === 0) loadData(); }, 5000);
</script>
</body>
</html>"""

@app.route("/")
def index():
    return HTML

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8081))
    IS_LOCAL = not os.environ.get("RAILWAY_ENVIRONMENT")
    logger.info("Starting...")
    threading.Thread(target=scrape_all_data, daemon=True).start()
    if IS_LOCAL:
        threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    app.run(debug=False, port=PORT, host="0.0.0.0")
