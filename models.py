"""
CryptoGuard - Database Models
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# ═══════════════════════════════════════════════════════
#  USER
# ═══════════════════════════════════════════════════════

class User(UserMixin, db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    watchlist = db.relationship("WatchlistItem", backref="user", lazy=True, cascade="all, delete-orphan")
    portfolio = db.relationship("PortfolioItem", backref="user", lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"


# ═══════════════════════════════════════════════════════
#  WATCHLIST
# ═══════════════════════════════════════════════════════

class WatchlistItem(db.Model):
    __tablename__ = "watchlist"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    crypto_id = db.Column(db.String(100), nullable=False)
    crypto_symbol = db.Column(db.String(20), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<WatchlistItem {self.crypto_symbol}>"


# ═══════════════════════════════════════════════════════
#  PORTFOLIO
# ═══════════════════════════════════════════════════════

class PortfolioItem(db.Model):
    __tablename__ = "portfolio"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    crypto_id = db.Column(db.String(100), nullable=False)
    crypto_symbol = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    buy_price = db.Column(db.Float, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PortfolioItem {self.crypto_symbol} x{self.amount}>"