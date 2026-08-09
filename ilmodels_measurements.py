#!/usr/bin/env python3
"""
IL Models – Measurements Search Tool with Link Export
"""
import os, threading, webbrowser, logging, requests
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
    ("MEN", "https://www.ilmodel.com/men"),
    ("CURVE", "https://www.ilmodel.com/plus-size"),
    ("INFLUENCER", "https://www.ilmodel.com/influencer"),
    ("DEVELOPMENT", "https://www.ilmodel.com/development"),
    ("CLASSIC WOMEN", "https://www.ilmodel.com/classic-women"),
]

def fetch_category_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        model_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href.startswith('#/'):
                model_name = link.get_text(strip=True)
                if model_name:
                    model_url = f"https://www.ilmodel.com/models{href}"
                    model_links.append((model_name, model_url))
        return model_links
    except Exception as e:
        logger.error(f"Error fetching category: {e}")
        return []

def fetch_model_details(model_url, model_name, category):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(model_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        measurements = {}
        measurements_text = None
        for div in soup.find_all('div'):
            text = div.get_text(strip=True)
            if 'Height' in text and 'Bust' in text and 'Waist' in text:
                measurements_text = text
                break
        if measurements_text:
            parts = measurements_text.split('|')
            for part in parts:
                part = part.strip()
                tokens = part.split()
                if len(tokens) >= 2:
                    key = tokens[0]
                    value = ' '.join(tokens[1:])
                    measurements[key] = value
        instagram = ""
        tiktok = ""
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text(strip=True).lower()
            if 'instagram' in href or 'instagram' in text:
                instagram = link.get('href', '')
            if 'tiktok' in href or 'tiktok' in text:
                tiktok = link.get('href', '')
        model = {
            "שם": model_name, "Name": model_name, "URL": model_url, "Category": category,
            "Height": measurements.get("Height", ""), "גובה": measurements.get("Height", ""),
            "Bust": measurements.get("Bust", ""), "חזה": measurements.get("Bust", ""),
            "Waist": measurements.get("Waist", ""), "מותן": measurements.get("Waist", ""),
            "Hips": measurements.get("Hips", ""), "אגן": measurements.get("Hips", ""),
            "Bra": measurements.get("Bra", ""), "חזייה": measurements.get("Bra", ""),
            "Shirt": measurements.get("Shirt", ""), "חולצה": measurements.get("Shirt", ""),
            "Pants": measurements.get("Pants", ""), "מכנסיים": measurements.get("Pants", ""),
            "Shoe": measurements.get("Shoe", ""), "נעליים": measurements.get("Shoe", ""),
            "Eye Color": measurements.get("Eye", ""), "עיניים": measurements.get("Eye", ""),
            "Hair Color": measurements.get("Hair", ""), "שיער": measurements.get("Hair", ""),
            "Tattoos": measurements.get("Tattoos", ""), "קעקוע": measurements.get("Tattoos", ""),
            "Ear Piercings": measurements.get("Piercings", ""), "עגילים": measurements.get("Piercings", ""),
            "Instagram": instagram, "אינסטגרם": instagram, "TikTok": tiktok, "טיקטוק": tiktok,
        }
        return model
    except Exception as e:
        logger.warning(f"Error fetching model: {e}")
        return None

def scrape_all_data():
    global models_cache
    logger.info("Starting scrape...")
    all_models = []
    for category_name, category_url in CATEGORIES:
        try:
            logger.info(f"Scraping: {category_name}")
            model_links = fetch_category_page(category_url)
            logger.info(f"Found {len(model_links)} models")
            for idx, (model_name, model_url) in enumerate(model_links):
                try:
                    model_data = fetch_model_details(model_url, model_name, category_name)
                    if model_data:
                        all_models.append(model_data)
                    time.sleep(0.2)
                except:
                    continue
        except Exception as e:
            logger.error(f"Category error: {e}")
            continue
        time.sleep(1)
    with cache_lock:
        models_cache = all_models
    logger.info(f"Complete. Total: {len(models_cache)}")

@app.route("/api/models")
def api_models():
    with cache_lock:
        if not models_cache:
            return jsonify({"error": "Loading..."}), 503
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
.sidebar { width: 270px; background: white; border-left: 1px solid #e0e0e0; padding: 18px 16px; overflow-y: auto; max-height: calc(100vh - 56px); position: sticky; top: 0; }
.sidebar h2 { font-size: 12px; color: #aaa; margin-bottom: 14px; }
.filter-group { margin-bottom: 14px; }
.filter-group label { display: block; font-size: 12px; font-weight: 700; color: #555; margin-bottom: 5px; }
.filter-group input, .filter-group select { width: 100%; padding: 7px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; font-family: inherit; }
.btn-search { width: 100%; padding: 10px; background: #1a1a2e; color: white; border: none; border-radius: 8px; font-size: 14px; cursor: pointer; margin-top: 4px; }
.btn-search:hover { background: #2d2d5e; }
.btn-reset { width: 100%; padding: 8px; background: #f0f0f0; color: #666; border: none; border-radius: 8px; font-size: 13px; cursor: pointer; margin-top: 6px; }
.btn-export { width: 100%; padding: 8px; background: #2e7d32; color: white; border: none; border-radius: 8px; font-size: 13px; cursor: pointer; margin-top: 6px; }
.btn-export:hover { background: #1b5e20; }
.btn-export:disabled { background: #ccc; cursor: not-allowed; }
.results { flex: 1; padding: 20px; overflow-y: auto; }
.results-header { font-size: 13px; color: #888; margin-bottom: 14px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(270px, 1fr)); gap: 14px; }
.card { background: white; border-radius: 10px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.07); border: 2px solid #ececec; position: relative; }
.card-checkbox { position: absolute; top: 12px; left: 12px; width: 20px; height: 20px; cursor: pointer; }
.card-name { font-size: 15px; font-weight: 700; color: #1a1a2e; margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid #f0f0f0; margin-top: 20px; }
.card-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.card-field .lbl { font-size: 11px; color: #aaa; margin-bottom: 1px; }
.card-field .val { font-size: 13px; font-weight: 600; color: #333; }
.state-msg { text-align: center; padding: 60px 20px; color: #aaa; font-size: 15px; }
.modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; align-items: center; justify-content: center; }
.modal.show { display: flex; }
.modal-content { background: white; padding: 30px; border-radius: 12px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto; }
.modal-close { float: right; font-size: 24px; cursor: pointer; font-weight: bold; }
.modal-title { font-size: 18px; font-weight: 700; margin-bottom: 20px; clear: both; }
.modal-links { font-family: monospace; font-size: 12px; line-height: 1.8; background: #f5f5f5; padding: 15px; border-radius: 6px; border: 1px solid #ddd; }
.copy-btn { margin-top: 15px; padding: 10px 20px; background: #1a73e8; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
.copy-btn:hover { background: #1565c0; }
</style>
</head>
<body>
<header><h1>🗂 IL Models – מאגר מידות</h1></header>
<div class="main">
  <div class="sidebar">
    <h2>סינון לפי מידות</h2>
    <div class="filter-group">
      <label>שם</label>
      <input type="text" id="f-name" placeholder="חיפוש לפי שם...">
    </div>
    <div class="filter-group">
      <label>גובה</label>
      <input type="number" id="f-height" placeholder="1.74 או 174" step="0.01">
    </div>
    <div class="filter-group">
      <label>חזה (ס"מ)</label>
      <input type="number" id="f-bust" placeholder="88">
    </div>
    <div class="filter-group">
      <label>מותן (ס"מ)</label>
      <input type="number" id="f-waist" placeholder="68">
    </div>
    <button class="btn-search" onclick="applyFilters()">🔍 חפש</button>
    <button class="btn-reset" onclick="resetFilters()">איפוס סינון</button>
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
  const results = allModels.filter(m => true);
  const grid = document.getElementById('grid');
  if (results.length === 0) {
    grid.innerHTML = '<div class="state-msg">טוען...</div>';
    return;
  }
  document.getElementById('results-header').textContent = results.length + ' דוגמניות נמצאו';
  grid.innerHTML = results.map((m, idx) => `
    <div class="card">
      <input type="checkbox" class="card-checkbox" data-idx="${idx}" onchange="updateSelection()">
      <div class="card-name">${m.Name || m.שם || '—'}</div>
      <div class="card-grid">
        <div class="card-field"><div class="lbl">גובה</div><div class="val">${m.Height || m.גובה || '—'}</div></div>
        <div class="card-field"><div class="lbl">חזה</div><div class="val">${m.Bust || m.חזה || '—'}</div></div>
        <div class="card-field"><div class="lbl">מותן</div><div class="val">${m.Waist || m.מותן || '—'}</div></div>
        <div class="card-field"><div class="lbl">אגן</div><div class="val">${m.Hips || m.אגן || '—'}</div></div>
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
    const model = allModels[idx];
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
  navigator.clipboard.writeText(text).then(() => {
    alert('✅ הועתק בהצלחה!');
  });
}

function resetFilters() {
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
