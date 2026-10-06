"""
CryptoGuard - AI Self-Learning
يحلّل تفاعلات المستخدمين ويولّد توصيات مخصّصة
"""

import os
import json
import time
from datetime import datetime, timedelta
from collections import Counter

LEARNED_FILE = "learned_data.json"


def get_user_interactions(user_id, db, Interaction):
    """جلب تفاعلات المستخدم من آخر 30 يوم"""
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    interactions = Interaction.query.filter(
        Interaction.user_id == user_id,
        Interaction.timestamp >= thirty_days_ago
    ).all()
    return interactions


def analyze_patterns(interactions):
    """تحليل الأنماط من التفاعلات"""
    if not interactions:
        return None

    # 1. العملات الأكثر مشاهدة
    viewed = Counter()
    watchlist_added = Counter()
    chart_viewed = Counter()
    actions_count = Counter()

    for i in interactions:
        actions_count[i.action] += 1
        if i.action == "view":
            viewed[i.crypto_id] += 1
        elif i.action == "watchlist":
            watchlist_added[i.crypto_id] += 1
        elif i.action == "chart":
            chart_viewed[i.crypto_id] += 1

    # 2. النمط العام
    total = len(interactions)

    # 3. العملات المفضّلة (weighted score)
    scores = {}
    for cid, count in viewed.items():
        scores[cid] = scores.get(cid, 0) + count * 1
    for cid, count in watchlist_added.items():
        scores[cid] = scores.get(cid, 0) + count * 3  # watchlist أثقل
    for cid, count in chart_viewed.items():
        scores[cid] = scores.get(cid, 0) + count * 2  # chart أثقل

    # ترتيب
    favorites = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]

    # 4. هل المستخدم نشيط؟
    user_type = "casual"
    if total > 50:
        user_type = "power_user"
    elif total > 20:
        user_type = "active"
    elif total > 5:
        user_type = "casual"
    else:
        user_type = "new"

    return {
        "total_interactions": total,
        "user_type": user_type,
        "favorites": [{"crypto_id": cid, "score": s} for cid, s in favorites],
        "top_viewed": viewed.most_common(5),
        "top_watchlist": watchlist_added.most_common(5),
        "actions_breakdown": dict(actions_count),
    }


def generate_ai_recommendations(user_id, db, Interaction, chat_fn):
    """يستعمل AI باش يوصّي بعملات بناءً على السلوك"""
    interactions = get_user_interactions(user_id, db, Interaction)
    analysis = analyze_patterns(interactions)

    if not analysis:
        return {
            "personalized": False,
            "message": "Pas assez de données pour personnaliser",
            "recommendations": []
        }

    # نبنيو prompt لـAI
    favs_str = ", ".join([f["crypto_id"] for f in analysis["favorites"]]) or "aucune"
    actions_str = ", ".join([f"{k}: {v}" for k, v in analysis["actions_breakdown"].items()])

    prompt = f"""Tu es un assistant crypto. Analyse le comportement de cet utilisateur:

- Type: {analysis['user_type']}
- Total interactions: {analysis['total_interactions']}
- Crypto préférées: {favs_str}
- Actions: {actions_str}

Recommande 3 cryptomonnaies qui pourraient l'intéresser, basées sur ses préférences.
Réponds UNIQUEMENT en JSON:
{{
  "recommendations": [
    {{"crypto_id": "bitcoin", "symbol": "BTC", "reason": "courte raison"}},
    {{"crypto_id": "ethereum", "symbol": "ETH", "reason": "raison"}},
    {{"crypto_id": "solana", "symbol": "SOL", "reason": "raison"}}
  ],
  "user_insight": "1 phrase sur le comportement de l'utilisateur"
}}"""

    try:
        response = chat_fn(prompt)
        import re
        m = re.search(r'\{.*\}', response, re.DOTALL)
        if m:
            data = json.loads(m.group())
            data["personalized"] = True
            data["analysis"] = analysis
            return data
    except Exception as e:
        print(f"AI error: {e}")

    return {
        "personalized": False,
        "message": "Erreur AI",
        "recommendations": [],
        "analysis": analysis
    }


def save_learned_data(user_id, data):
    """حفظ البيانات المتعلّمة"""
    all_data = {}
    if os.path.exists(LEARNED_FILE):
        try:
            with open(LEARNED_FILE, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            all_data = {}

    all_data[str(user_id)] = {
        "timestamp": time.time(),
        "data": data
    }

    try:
        with open(LEARNED_FILE, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def load_learned_data(user_id):
    """تحميل البيانات المتعلّمة"""
    if not os.path.exists(LEARNED_FILE):
        return None
    try:
        with open(LEARNED_FILE, "r", encoding="utf-8") as f:
            all_data = json.load(f)
        entry = all_data.get(str(user_id))
        if entry and (time.time() - entry["timestamp"]) < 86400:  # 24h
            return entry["data"]
    except (json.JSONDecodeError, IOError):
        pass
    return None