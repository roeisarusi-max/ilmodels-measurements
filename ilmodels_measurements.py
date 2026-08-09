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

_cache = {"models": [], "updated": None}
_lock = threading.Lock()


def load_file():
    try:
        with open(MODELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not read {MODELS_FILE}: {e}")
        return []


def refresh_loop():
    """Re-scrape ilmodel.com once a day, keeping the last good data on failure."""
    while True:
        try:
            logger.info("Refreshing models from ilmodel.com...")
            update_models.main()
            models = load_file()
            if models:
                with _lock:
                    _cache["models"] = models
                    _cache["updated"] = datetime.now().isoformat(timespec="seconds")
                logger.info(f"Refreshed: {len(models)} models")
        except Exception as e:
            logger.error(f"Refresh failed, keeping previous data: {e}")
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
        return jsonify({"count": len(_cache["models"]), "updated": _cache["updated"]})


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
