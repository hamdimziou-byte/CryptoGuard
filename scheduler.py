"""
CryptoGuard - Auto Scheduler
يعاود يحلّل سلوك المستخدمين تلقائيًا
"""

import os
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler


def retrain_models(app, db, User, Interaction, chat):
    """يعاود يدرّب الموديلات لكل المستخدمين"""
    from ai_learner import generate_ai_recommendations, save_learned_data

    with app.app_context():
        print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Retraining models...")
        users = User.query.all()
        count = 0
        for user in users:
            try:
                result = generate_ai_recommendations(user.id, db, Interaction, chat)
                if result.get("personalized"):
                    save_learned_data(user.id, result)
                    count += 1
            except Exception as e:
                print(f"  ⚠️ User {user.id}: {e}")
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Retrained {count}/{len(users)} users")


def clean_old_interactions(app, db, Interaction):
    """يمسح التفاعلات القديمة (> 90 يوم)"""
    from datetime import timedelta
    with app.app_context():
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        deleted = Interaction.query.filter(Interaction.timestamp < ninety_days_ago).delete()
        db.session.commit()
        if deleted:
            print(f"🗑️  Cleaned {deleted} old interactions")


def start_scheduler(app, db, User, Interaction, chat):
    """يبدا الـScheduler"""
    scheduler = BackgroundScheduler()
    
    # كل ساعة ← retrain
    scheduler.add_job(
        func=lambda: retrain_models(app, db, User, Interaction, chat),
        trigger="interval",
        hours=1,
        id="retrain_models",
        replace_existing=True
    )
    
    # كل يوم ← clean
    scheduler.add_job(
        func=lambda: clean_old_interactions(app, db, Interaction),
        trigger="interval",
        hours=24,
        id="clean_old",
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ Scheduler démarré")
    return scheduler