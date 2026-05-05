#!/usr/bin/env python3
"""
IL Models – Measurements Search Tool
Reads from Google Sheets (public CSV export) and provides a searchable/filterable UI
Supports exact match + close-match (within tolerance) highlighting
"""
import os, csv, io, threading, webbrowser
import requests
from flask import Flask, jsonify

app = Flask(__name__)

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSbke0sBlhYRVERSEZf6QrtsBuLCXPLKayrr3jXhAHEkxZ52eV57U1P_rFEFYD0SrVwBFXLtgYGAypo/pub?gid=1662218182&single=true&output=csv"


def fetch_data():
    try:
        r = requests.get(CSV_URL, timeout=15)
        r.encoding = "utf-8"
        reader = csv.DictReader(io.StringIO(r.text))
        rows = []
        for row in reader:
            clean = {k.strip(): (v.strip() if v else '') for k, v in row.items() if k is not None and k != ''}
            rows.append(clean)
        return rows, None
    except Exception as e:
        return [], str(e)


@app.route("/api/models")
def api_models():
    rows, err = fetch_data()
    if err:
        return jsonify({"error": err}), 500
    return jsonify(rows)


HTML = r"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IL Models – מאגר מידות</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; color: #222; }

header {
  background: #1a1a2e;
  color: white;
  padding: 16px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
header h1 { font-size: 20px; font-weight: 700; }
header #count-header { font-size: 13px; opacity: 0.65; }

.main { display: flex; min-height: calc(100vh - 56px); }

/* Sidebar */
.sidebar {
  width: 270px;
  flex-shrink: 0;
  background: white;
  border-left: 1px solid #e0e0e0;
  padding: 18px 16px;
  overflow-y: auto;
  max-height: calc(100vh - 56px);
  position: sticky;
  top: 0;
}
.sidebar h2 { font-size: 12px; color: #aaa; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 1px; }

.filter-group { margin-bottom: 14px; }
.filter-group > label { display: block; font-size: 12px; font-weight: 700; color: #555; margin-bottom: 5px; }

.filter-group input[type=text],
.filter-group input[type=number],
.filter-group select {
  width: 100%;
  padding: 7px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
}

.tolerance-row {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f9f3e8;
  border: 1px solid #f0d9a0;
  border-radius: 6px;
  padding: 8px 10px;
  margin-bottom: 16px;
}
.tolerance-row label { font-size: 12px; color: #7a5c00; font-weight: 600; flex: 1; }
.tolerance-row input {
  width: 55px;
  padding: 4px 6px;
  border: 1px solid #f0d9a0;
  border-radius: 5px;
  font-size: 13px;
  text-align: center;
  background: white;
}

.btn-search {
  width: 100%;
  padding: 10px;
  background: #1a1a2e;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  margin-top: 4px;
  font-family: inherit;
}
.btn-search:hover { background: #2d2d5e; }
.btn-reset {
  width: 100%;
  padding: 8px;
  background: #f0f0f0;
  color: #666;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  margin-top: 6px;
  font-family: inherit;
}
.btn-reset:hover { background: #e0e0e0; }

/* Results */
.results { flex: 1; padding: 20px; overflow-y: auto; }
.results-header { font-size: 13px; color: #888; margin-bottom: 14px; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 14px;
}

/* Card – exact match */
.card {
  background: white;
  border-radius: 10px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  border: 2px solid #ececec;
  transition: border-color 0.2s;
}

/* Card – close match */
.card.close-match {
  border: 2px solid #f0a500;
  background: #fffdf5;
}

.card-name {
  font-size: 15px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.badge-close {
  font-size: 10px;
  font-weight: 700;
  background: #f0a500;
  color: white;
  padding: 2px 7px;
  border-radius: 8px;
  white-space: nowrap;
  flex-shrink: 0;
}

.card-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.card-field .lbl { font-size: 11px; color: #aaa; margin-bottom: 1px; }
.card-field .val { font-size: 13px; font-weight: 600; color: #333; }

/* Highlight fields that are close (not exact) */
.card-field.field-close .val { color: #c07800; }

.card-bottom { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.badge { display: inline-block; padding: 2px 9px; border-radius: 10px; font-size: 11px; font-weight: 600; }
.badge-yes { background: #fde8e8; color: #c0392b; }
.badge-no  { background: #e8f5e9; color: #2e7d32; }
.card-links { display: flex; gap: 10px; }
.card-links a { font-size: 12px; color: #1a73e8; text-decoration: none; }
.card-links a:hover { text-decoration: underline; }

.state-msg { text-align: center; padding: 60px 20px; color: #aaa; font-size: 15px; }
.state-msg.error { color: #c0392b; }

.divider { height: 1px; background: #f0f0f0; margin: 14px 0; }

.legend {
  display: flex;
  gap: 14px;
  margin-bottom: 14px;
  font-size: 12px;
  color: #666;
  align-items: center;
}
.legend-dot {
  width: 12px; height: 12px;
  border-radius: 3px;
  border: 2px solid #ececec;
  display: inline-block;
  flex-shrink: 0;
}
.legend-dot.close { border-color: #f0a500; background: #fffdf5; }
</style>
</head>
<body>

<header>
  <h1>🗂 IL Models – מאגר מידות</h1>
  <span id="count-header">טוען...</span>
</header>

<div class="main">
  <div class="sidebar">
    <h2>סינון לפי מידות</h2>

    <div class="filter-group">
      <label>שם</label>
      <input type="text" id="f-name" placeholder="חיפוש לפי שם...">
    </div>

    <div class="divider"></div>

    <div class="tolerance-row">
      <label>⚡ טווח זליגה (±)<br><small style="font-weight:400;color:#a07000">ס"מ: 2–5 | גובה במטרים: 0.03</small></label>
      <input type="number" id="f-tolerance" value="3" min="0" step="0.01">
    </div>

    <div class="filter-group">
      <label>גובה</label>
      <input type="number" id="f-height" placeholder="לדוגמה: 1.74 או 174" step="0.01">
    </div>

    <div class="filter-group">
      <label>חזה (ס"מ)</label>
      <input type="number" id="f-bust" placeholder="לדוגמה: 88">
    </div>

    <div class="filter-group">
      <label>מותן (ס"מ)</label>
      <input type="number" id="f-waist" placeholder="לדוגמה: 68">
    </div>

    <div class="filter-group">
      <label>אגן (ס"מ)</label>
      <input type="number" id="f-hips" placeholder="לדוגמה: 92">
    </div>

    <div class="filter-group">
      <label>נעליים (מספר)</label>
      <input type="number" id="f-shoes" placeholder="לדוגמה: 38" step="0.5">
    </div>

    <div class="divider"></div>

    <div class="filter-group">
      <label>מידת חולצה</label>
      <select id="f-shirt">
        <option value="">הכל</option>
        <option>XS</option><option>S</option><option>M</option>
        <option>L</option><option>XL</option><option>XXL</option>
      </select>
    </div>

    <div class="filter-group">
      <label>צבע שיער</label>
      <select id="f-hair">
        <option value="">הכל</option>
        <option>Black</option><option>Brown</option><option>Blonde</option>
        <option>Red</option><option>Auburn</option><option>Other</option>
      </select>
    </div>

    <div class="filter-group">
      <label>קעקועים בולטים</label>
      <select id="f-tattoos">
        <option value="">הכל</option>
        <option value="yes">יש</option>
        <option value="no">אין</option>
      </select>
    </div>

    <button class="btn-search" onclick="applyFilters()">🔍 חפש</button>
    <button class="btn-reset" onclick="resetFilters()">איפוס סינון</button>
  </div>

  <div class="results">
    <div class="legend" id="legend" style="display:none">
      <span class="legend-dot"></span> התאמה מדויקת
      <span class="legend-dot close"></span> קרוב לטווח
    </div>
    <div class="results-header" id="results-header">טוען נתונים...</div>
    <div class="grid" id="grid">
      <div class="state-msg">⏳ טוען...</div>
    </div>
  </div>
</div>

<script>
let allModels = [];

function getVal(model, ...substrings) {
  for (const sub of substrings) {
    for (const k of Object.keys(model)) {
      if (k.includes(sub)) return model[k] || '';
    }
  }
  return '';
}

function numVal(model, ...substrings) {
  const v = getVal(model, ...substrings);
  const n = parseFloat(v);
  return isNaN(n) ? null : n;
}

// Returns: 'exact' | 'close' | 'out' | 'skip' (no data entered)
function matchStatus(modelVal, target, tolerance) {
  if (target === null) return 'skip';
  if (modelVal === null) return 'out'; // model has no data for this field → exclude
  const diff = Math.abs(modelVal - target);
  if (diff <= 0.001) return 'exact';
  if (diff <= tolerance) return 'close';
  return 'out';
}

async function loadData() {
  try {
    const res = await fetch('/api/models');
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    allModels = data;
    document.getElementById('count-header').textContent = allModels.length + ' דוגמניות במאגר';
    applyFilters();
  } catch(e) {
    document.getElementById('grid').innerHTML = '<div class="state-msg error">שגיאה בטעינת הנתונים: ' + e.message + '</div>';
  }
}

function applyFilters() {
  const name      = document.getElementById('f-name').value.trim().toLowerCase();
  const toleranceRaw = document.getElementById('f-tolerance').value;
  const tolerance = toleranceRaw === '' ? 3 : (isNaN(parseFloat(toleranceRaw)) ? 3 : parseFloat(toleranceRaw));
  const heightT   = parseFloat(document.getElementById('f-height').value)  || null;
  const bustT     = parseFloat(document.getElementById('f-bust').value)    || null;
  const waistT    = parseFloat(document.getElementById('f-waist').value)   || null;
  const hipsT     = parseFloat(document.getElementById('f-hips').value)    || null;
  const shoesT    = parseFloat(document.getElementById('f-shoes').value)   || null;
  const shirt     = document.getElementById('f-shirt').value;
  const hair      = document.getElementById('f-hair').value.toLowerCase();
  const tattoos   = document.getElementById('f-tattoos').value.toLowerCase();

  const hasNumericFilter = heightT || bustT || waistT || hipsT || shoesT;

  const results = [];

  for (const m of allModels) {
    // Name filter
    if (name && !getVal(m, 'שם', 'Name', 'name').toLowerCase().includes(name)) continue;

    // Shirt
    if (shirt) {
      const s = getVal(m, 'חולצה', 'Shirt').toUpperCase();
      if (s !== shirt.toUpperCase()) continue;
    }

    // Hair
    if (hair) {
      const h = getVal(m, 'שיער', 'Hair').toLowerCase();
      if (!h.includes(hair)) continue;
    }

    // Tattoos
    if (tattoos) {
      const t = getVal(m, 'קעקוע', 'Tattoo').toLowerCase();
      if (!t.includes(tattoos)) continue;
    }

    // Numeric fields – calculate match status for each
    const heightStatus = matchStatus(numVal(m, 'גובה'), heightT, tolerance);
    const bustStatus   = matchStatus(numVal(m, 'חזה'),  bustT,   tolerance);
    const waistStatus  = matchStatus(numVal(m, 'מותן'), waistT,  tolerance);
    const hipsStatus   = matchStatus(numVal(m, 'אגן'),  hipsT,   tolerance);
    const shoesStatus  = matchStatus(numVal(m, 'נעליים'), shoesT, tolerance);

    const fieldStatuses = { heightStatus, bustStatus, waistStatus, hipsStatus, shoesStatus };

    // If any active filter has 'out' status → exclude
    let excluded = false;
    for (const [key, status] of Object.entries(fieldStatuses)) {
      if (status === 'out') { excluded = true; break; }
    }
    if (excluded) continue;

    // Determine card-level status: 'close' if any field is close, else 'exact'
    const isClose = Object.values(fieldStatuses).some(s => s === 'close');

    results.push({ model: m, isClose, fieldStatuses });
  }

  // Sort: exact matches first, then close matches
  results.sort((a, b) => {
    if (a.isClose === b.isClose) return 0;
    return a.isClose ? 1 : -1;
  });

  // Show legend if numeric filter active
  document.getElementById('legend').style.display = hasNumericFilter ? 'flex' : 'none';

  renderResults(results);
}

function renderResults(results) {
  const grid   = document.getElementById('grid');
  const header = document.getElementById('results-header');

  if (results.length === 0) {
    header.textContent = 'לא נמצאו תוצאות';
    grid.innerHTML = '<div class="state-msg">אין דוגמניות התואמות את החיפוש 🔍</div>';
    return;
  }

  const exactCount = results.filter(r => !r.isClose).length;
  const closeCount = results.filter(r => r.isClose).length;
  let headerText = results.length + ' דוגמניות נמצאו';
  if (closeCount > 0) headerText += ` (${exactCount} מדויקות, ${closeCount} קרובות)`;
  header.textContent = headerText;

  grid.innerHTML = results.map(({ model: m, isClose, fieldStatuses }) => {
    const name      = getVal(m, 'שם', 'Name')          || '—';
    const height    = getVal(m, 'גובה')                 || '—';
    const bust      = getVal(m, 'חזה')                  || '—';
    const waist     = getVal(m, 'מותן')                 || '—';
    const hips      = getVal(m, 'אגן')                  || '—';
    const bra       = getVal(m, 'חזייה')                || '—';
    const shirt     = getVal(m, 'חולצה')                || '—';
    const pants     = getVal(m, 'מכנסיים')              || '—';
    const shoes     = getVal(m, 'נעליים')               || '—';
    const eyes      = getVal(m, 'עיניים')               || '—';
    const hair      = getVal(m, 'שיער')                 || '—';
    const piercings = getVal(m, 'חורים', 'עגילים')     || '—';
    const tattoos   = getVal(m, 'קעקוע');
    const instagram = getVal(m, 'אינסטגרם', 'Instagram');
    const tiktok    = getVal(m, 'טיקטוק', 'TikTok');

    const tattooLow = tattoos.toLowerCase();
    const tattoosBadge = tattooLow.includes('yes') || tattooLow === 'כן'
      ? '<span class="badge badge-yes">קעקועים</span>'
      : tattooLow.includes('no') || tattooLow === 'לא'
      ? '<span class="badge badge-no">ללא קעקועים</span>'
      : '';

    const links = [];
    if (instagram) links.push(`<a href="${instagram}" target="_blank">📷 אינסטגרם</a>`);
    if (tiktok)    links.push(`<a href="${tiktok}"    target="_blank">🎵 טיקטוק</a>`);

    // Field-level close highlighting
    const hCls  = fieldStatuses.heightStatus === 'close' ? ' field-close' : '';
    const bCls  = fieldStatuses.bustStatus   === 'close' ? ' field-close' : '';
    const wCls  = fieldStatuses.waistStatus  === 'close' ? ' field-close' : '';
    const hpCls = fieldStatuses.hipsStatus   === 'close' ? ' field-close' : '';
    const shCls = fieldStatuses.shoesStatus  === 'close' ? ' field-close' : '';

    return `
<div class="card${isClose ? ' close-match' : ''}">
  <div class="card-name">
    <span>${name}</span>
    ${isClose ? '<span class="badge-close">~ קרוב</span>' : ''}
  </div>
  <div class="card-grid">
    <div class="card-field${hCls}"><div class="lbl">גובה</div><div class="val">${height}</div></div>
    <div class="card-field${bCls}"><div class="lbl">חזה</div><div class="val">${bust}</div></div>
    <div class="card-field${wCls}"><div class="lbl">מותן</div><div class="val">${waist}</div></div>
    <div class="card-field${hpCls}"><div class="lbl">אגן</div><div class="val">${hips}</div></div>
    <div class="card-field"><div class="lbl">חזייה</div><div class="val">${bra}</div></div>
    <div class="card-field"><div class="lbl">חולצה</div><div class="val">${shirt}</div></div>
    <div class="card-field"><div class="lbl">מכנסיים</div><div class="val">${pants}</div></div>
    <div class="card-field${shCls}"><div class="lbl">נעליים</div><div class="val">${shoes}</div></div>
    <div class="card-field"><div class="lbl">עיניים</div><div class="val">${eyes}</div></div>
    <div class="card-field"><div class="lbl">שיער</div><div class="val">${hair}</div></div>
    <div class="card-field"><div class="lbl">עגילים</div><div class="val">${piercings}</div></div>
  </div>
  ${tattoosBadge || links.length ? `
  <div class="card-bottom">
    ${tattoosBadge}
    ${links.length ? '<div class="card-links">' + links.join('') + '</div>' : ''}
  </div>` : ''}
</div>`;
  }).join('');
}

function resetFilters() {
  document.querySelectorAll('input[type=text], input[type=number], select')
    .forEach(el => { if (el.id !== 'f-tolerance') el.value = ''; });
  document.getElementById('f-tolerance').value = '3';
  applyFilters();
}

document.addEventListener('keydown', e => { if (e.key === 'Enter') applyFilters(); });

loadData();
</script>
</body>
</html>"""


@app.route("/")
def index():
    return HTML


if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8081))
    IS_LOCAL = not os.environ.get("RAILWAY_ENVIRONMENT")
    if IS_LOCAL:
        threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    app.run(debug=False, port=PORT, host="0.0.0.0")
זה 
