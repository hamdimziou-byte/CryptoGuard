"""
CryptoGuard Web App - Flask Backend
Version: 2.0.0
"""

from flask import Flask, render_template, jsonify, request
from datetime import datetime
import main as cg

app = Flask(__name__)


@app.route("/")
def index():
    """الصفحة الرئيسية"""
    return render_template("index.html")


@app.route("/api/prices")
def api_prices():
    """API: جلب الأسعار"""
    limit = request.args.get("limit", 20, type=int)
    currency = request.args.get("currency", "usd")
    
    data = cg.get_top_cryptos(limit, currency)
    
    if not data:
        # Fallback
        data = cg.fetch_prices_robust(cg.CRYPTOS[:limit], currency)
    
    if not data:
        return jsonify({"error": "Impossible de récupérer les données"}), 500
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "currency": currency,
        "data": data
    })


@app.route("/api/search")
def api_search():
    """API: بحث عن عملة"""
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Query vide"}), 400
    
    results = cg.search_crypto(query)
    return jsonify({"query": query, "results": results or []})


@app.route("/api/exchange")
def api_exchange():
    """API: سعر الصرف"""
    target = request.args.get("to", "TND")
    rate = cg.get_exchange_rate(target)
    return jsonify({"from": "USD", "to": target, "rate": rate})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)