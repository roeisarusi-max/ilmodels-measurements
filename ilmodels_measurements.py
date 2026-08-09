#!/usr/bin/env python3
"""
IL Models server.
Serves models_data.json via /api/models and refreshes it from ilmodel.com once a day.
"""

import json
import logging
import os
import threading
import time
from datetime import datetime

from flask import Flask, jsonify, send_file

import update_models

app = Flask(__name__, static_folder=".", static_url_path="")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

MODELS_FILE = "models_data.json"
REFRESH_SECONDS = 24 * 60 * 60  # once a day

_cache = {"models": [], "updated": None, "added": [], "removed": [], "last_error": None}
_lock = threading.Lock()


def load_file():
    try:
        with open(MODELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not read {MODELS_FILE}: {e}")
        return []


def _refresh_once():
    """Rebuild the whole roster from the live site.

    Because the list is rebuilt from scratch, a model removed from
    ilmodel.com disappears here and a newly added one shows up
    automatically. Previous data is kept if the scrape fails.
    """
    try:
        logger.info("Refreshing models from ilmodel.com...")

        with _lock:
            before = {m["URL"]: m.get("Name", "") for m in _cache["models"]}

        models = update_models.main()
        if not models or len(models) < update_models.MIN_EXPECTED:
            raise RuntimeError(f"scrape returned {len(models) if models else 0} models")

        after = {m["URL"]: m.get("Name", "") for m in models}
        added = sorted(after[u] for u in after.keys() - before.keys())
        removed = sorted(before[u] for u in before.keys() - after.keys())

        with _lock:
            _cache["models"] = models
            _cache["updated"] = datetime.now().isoformat(timespec="seconds")
            _cache["added"] = added
            _cache["removed"] = removed
            _cache["last_error"] = None

        logger.info(f"Refreshed: {len(models)} models "
                    f"(+{len(added)} added, -{len(removed)} removed)")
        if added:
            logger.info(f"  added:   {', '.join(added)}")
        if removed:
            logger.info(f"  removed: {', '.join(removed)}")

    except Exception as e:
        logger.error(f"Refresh failed, keeping previous data: {e}")
        with _lock:
            _cache["last_error"] = str(e)


def refresh_loop():
    """Run a refresh at startup, then once every 24 hours."""
    while True:
        _refresh_once()
        time.sleep(REFRESH_SECONDS)


@app.route("/api/models")
def api_models():
    with _lock:
        models = list(_cache["models"])
    if not models:
        models = load_file()
    return jsonify(models)


@app.route("/api/status")
def api_status():
    with _lock:
        return jsonify({
            "count": len(_cache["models"]),
            "updated": _cache["updated"],
            "added": _cache["added"],
            "removed": _cache["removed"],
            "last_error": _cache["last_error"],
            "refresh_hours": REFRESH_SECONDS / 3600,
        })


@app.route("/api/refresh", methods=["POST", "GET"])
def api_refresh():
    """Trigger an immediate refresh without waiting for the daily cycle."""
    threading.Thread(target=_refresh_once, daemon=True).start()
    return jsonify({"status": "refresh started"})


@app.route("/")
def index():
    return send_file("index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))

    _cache["models"] = load_file()
    logger.info(f"Loaded {len(_cache['models'])} models from disk")

    threading.Thread(target=refresh_loop, daemon=True).start()

    logger.info(f"Listening on port {port}")
    app.run(debug=False, port=port, host="0.0.0.0", use_reloader=False)
