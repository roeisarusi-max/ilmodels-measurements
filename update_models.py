#!/usr/bin/env python3
"""
Scrapes ALL models from ilmodel.com (all categories) into models_data.json.
Pure requests + BeautifulSoup - no browser needed.
"""

import json
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

BASE = "https://www.ilmodel.com"
MIN_EXPECTED = 20  # sanity floor: below this the scrape is assumed broken
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

# Field key -> label aliases (longest first so "Eye Color" beats "Eye")
FIELD_ALIASES = [
    ("Height", ["height"]),
    ("Bust", ["bust", "chest"]),
    ("Waist", ["waist"]),
    ("Hips", ["hips", "hip"]),
    ("Bra", ["bra"]),
    ("Shirt", ["shirt"]),
    ("Pants", ["pants"]),
    ("Shoe", ["shoes", "shoe"]),
    ("EyeColor", ["eye color", "eyes", "eye"]),
    ("HairColor", ["hair color", "hair"]),
    ("Tattoos", ["tattoos", "tattoo"]),
    ("EarPiercings", ["ear piercings", "ear piercing", "piercings", "piercing"]),
]

FIELD_KEYS = [k for k, _ in FIELD_ALIASES]


def get(url, tries=3):
    for i in range(tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code == 200:
                return r
        except Exception:
            pass
        time.sleep(1 + i)
    return None


CATEGORIES = {
    "WOMEN": f"{BASE}/models",
    "MEN": f"{BASE}/men",
    "CURVE": f"{BASE}/plus-size",
    "DEVELOPMENT": f"{BASE}/development",
    "CLASSIC WOMEN": f"{BASE}/classic-women",
}


def find_categories():
    """Known category pages, plus any extra ones discovered in the site nav."""
    cats = dict(CATEGORIES)
    r = get(f"{BASE}/models")
    if r:
        soup = BeautifulSoup(r.content, "html.parser")
        for a in soup.select("nav a[href], .header-nav a[href]"):
            name = a.get_text(strip=True).upper()
            href = a.get("href", "")
            if not name or not href.startswith("/"):
                continue
            if name in {"BECOME A MODEL", "CONTACT", "MENU", ""}:
                continue
            cats.setdefault(name, BASE + href)
    return cats


def find_models_in_category(cat_url):
    """Return list of (name, url) from a category page."""
    r = get(cat_url)
    out = []
    if not r:
        return out
    soup = BeautifulSoup(r.content, "html.parser")
    for a in soup.select("#projectThumbs a.project[href]"):
        href = a.get("href", "")
        title_el = a.select_one(".project-title")
        name = title_el.get_text(strip=True) if title_el else ""
        if href and name:
            out.append((name, BASE + href if href.startswith("/") else href))
    # fallback: data-url attributes
    if not out:
        for div in soup.select(".project[data-url]"):
            u = div.get("data-url", "")
            if u:
                out.append((u.strip("/").upper().replace("-", " "), BASE + u))
    return out


def normalize_height(value):
    """'1.74' or '1,74' -> '174'. '171' stays '171'."""
    v = value.replace(",", ".").strip()
    m = re.match(r"^(\d)\.(\d{2})$", v)
    if m:
        return m.group(1) + m.group(2)
    m = re.match(r"^(\d{3})", v)
    return m.group(1) if m else v


def parse_measurements(text):
    """Handles both site formats:
      'Height 171 | Bust 84 | ... | Ear Piercings 1+2'
      'Height: 1.74|BUST 83| WAIST 63| HIPS 90| Shoes: 37| Hair: BLOND| Eyes: BLUE'
    """
    data = {key: "" for key in FIELD_KEYS}

    line = None
    for raw in text.split("\n"):
        s = raw.strip()
        if "|" in s and re.search(r"\bheight\b", s, re.I) and len(s) < 400:
            line = s
            break
    if not line:
        return data, False

    for chunk in line.split("|"):
        chunk = chunk.strip().lstrip("-–—").strip()
        if not chunk:
            continue
        low = chunk.lower()
        for key, aliases in FIELD_ALIASES:
            matched = next((a for a in aliases if low.startswith(a)), None)
            if not matched:
                continue
            value = chunk[len(matched):].strip()
            value = value.lstrip(":").strip()
            if key == "Height":
                value = normalize_height(value)
            data[key] = value
            break

    return data, bool(data["Height"])


def scrape_model(name, url, category):
    r = get(url)
    if not r:
        return None
    soup = BeautifulSoup(r.content, "html.parser")
    text = soup.get_text("\n")

    # Real title from the page heading
    title = name
    for line in [l.strip() for l in text.split("\n") if l.strip()]:
        if line.upper() == name.upper():
            title = line
            break

    data, ok = parse_measurements(text)
    model = {"Name": title, "URL": url, "Category": category}
    model.update(data)
    return model if ok else model


def main():
    print("=" * 70)
    print(f"SCRAPING ilmodel.com - {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 70)

    cats = find_categories()
    print(f"\nCategories ({len(cats)}): {', '.join(cats)}")

    seen = {}
    for cat, cat_url in cats.items():
        models = find_models_in_category(cat_url)
        print(f"  {cat:16s} -> {len(models)} models")
        for name, url in models:
            if url not in seen:
                seen[url] = (name, cat)
        time.sleep(0.3)

    print(f"\nTotal unique models: {len(seen)}\n")

    all_models = []
    for i, (url, (name, cat)) in enumerate(seen.items(), 1):
        m = scrape_model(name, url, cat)
        if m:
            has = "OK " if m.get("Height") else "-- "
            print(f"[{i}/{len(seen)}] {has}{m['Name']}")
            all_models.append(m)
        else:
            print(f"[{i}/{len(seen)}] FAIL {name}")
        time.sleep(0.25)

    with_data = sum(1 for m in all_models if m.get("Height"))

    # Safety: never overwrite good data with a broken/partial scrape
    if len(all_models) < MIN_EXPECTED:
        print(f"\nABORT: only {len(all_models)} models found (min {MIN_EXPECTED}). "
              f"Keeping existing models_data.json.")
        return all_models

    with open("models_data.json", "w", encoding="utf-8") as f:
        json.dump(all_models, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"SAVED {len(all_models)} models ({with_data} with measurements)")
    print("=" * 70)
    return all_models


if __name__ == "__main__":
    main()
