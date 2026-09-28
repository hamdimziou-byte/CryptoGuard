"""
CryptoGuard - Authentication Routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        
        # Validation
        if not username or not email or not password:
            flash("Tous les champs sont obligatoires", "error")
            return redirect(url_for("auth.register"))
        
        if len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères", "error")
            return redirect(url_for("auth.register"))
        
        if password != confirm:
            flash("Les mots de passe ne correspondent pas", "error")
            return redirect(url_for("auth.register"))
        
        # Check existing
        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est déjà pris", "error")
            return redirect(url_for("auth.register"))
        
        if User.query.filter_by(email=email).first():
            flash("Cet email est déjà utilisé", "error")
            return redirect(url_for("auth.register"))
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash("Compte créé avec succès! Connectez-vous.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash("Nom d'utilisateur ou mot de passe incorrect", "error")
            return redirect(url_for("auth.login"))
        
        login_user(user)
        flash(f"Bienvenue {user.username}!", "success")
        
        next_page = request.args.get("next")
        return redirect(next_page or url_for("index"))
    
    return render_template("login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous êtes déconnecté", "success")
    return redirect(url_for("index"))