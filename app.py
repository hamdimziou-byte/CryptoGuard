"""
CryptoGuard Web App - Flask Backend with Authentication
Version: 2.1.0
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager, current_user, login_required
from datetime import datetime
from models import db, User, WatchlistItem
from auth import auth
import main as cg
from scam_detector import enrich_with_risk
import os


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
database_url = os.environ.get("DATABASE_URL", "sqlite:///cryptoguard.db")

# Render يعطي postgres:// أما SQLAlchemy يحتاج postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Init extensions
db.init_app(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Connectez-vous pour accéder à cette page."


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Register blueprints
app.register_blueprint(auth)
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# ═══════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/prices")
def api_prices():
    limit = request.args.get("limit", 20, type=int)
    currency = request.args.get("currency", "usd")
    
    data = cg.get_top_cryptos(limit, currency)
    if not data:
        data = cg.fetch_prices_robust(cg.CRYPTOS[:limit], currency)
    
    if not data:
        return jsonify({"error": "Impossible de récupérer les données"}), 500
        # زيد Risk Score لكل عملة
    data = enrich_with_risk(data)
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "currency": currency,
        "data": data
    })


@app.route("/api/search")
def api_search():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Query vide"}), 400
    results = cg.search_crypto(query)
    return jsonify({"query": query, "results": results or []})


@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)
@app.route("/watchlist")
@login_required
def watchlist():
    """صفحة قائمة المراقبة"""
    items = WatchlistItem.query.filter_by(user_id=current_user.id).all()
    
    # جلب الأسعار للعملات في الـwatchlist
    crypto_ids = [item.crypto_id for item in items]
    prices = {}
    if crypto_ids:
        data = cg.fetch_prices_robust(crypto_ids, "usd")
        if data:
            prices = {coin["id"]: coin for coin in data}
    
    return render_template("watchlist.html", items=items, prices=prices)


@app.route("/watchlist/add/<crypto_id>", methods=["POST"])
@login_required
def watchlist_add(crypto_id):
    """إضافة عملة للـwatchlist"""
    symbol = request.form.get("symbol", crypto_id[:3]).upper()
    
    # تحقق إنو ما موجودة
    existing = WatchlistItem.query.filter_by(
        user_id=current_user.id,
        crypto_id=crypto_id
    ).first()
    
    if not existing:
        item = WatchlistItem(
            user_id=current_user.id,
            crypto_id=crypto_id,
            crypto_symbol=symbol
        )
        db.session.add(item)
        db.session.commit()
        return jsonify({"status": "added", "crypto_id": crypto_id})
    
    return jsonify({"status": "exists", "crypto_id": crypto_id})


@app.route("/watchlist/remove/<crypto_id>", methods=["POST"])
@login_required
def watchlist_remove(crypto_id):
    """حيّد عملة من الـwatchlist"""
    item = WatchlistItem.query.filter_by(
        user_id=current_user.id,
        crypto_id=crypto_id
    ).first()
    
    if item:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"status": "removed", "crypto_id": crypto_id})
    
    return jsonify({"status": "not_found", "crypto_id": crypto_id}), 404


@app.route("/api/watchlist")
@login_required
def api_watchlist():
    """API: قائمة الـwatchlist متاع المستخدم"""
    items = WatchlistItem.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        "crypto_ids": [item.crypto_id for item in items]
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)