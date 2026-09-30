"""
CryptoGuard - Email Alerts
إرسال تنبيهات بالبريد الإلكتروني
"""

import os
import resend
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# ⚠️ Resend Free: تقدر تبعث فقط من onboarding@resend.dev
FROM_EMAIL = "CryptoGuard <onboarding@resend.dev>"


def send_alert_email(to_email, username, crypto_symbol, current_price, condition, target_price):
    """
    إرسال إيميل تنبيه
    """
    if not RESEND_API_KEY:
        return {"success": False, "error": "RESEND_API_KEY manquant"}
    
    condition_text = "est monté au-dessus de" if condition == "above" else "est descendu en-dessous de"
    emoji = "🚀" if condition == "above" else "📉"
    
    subject = f"{emoji} CryptoGuard Alerte: {crypto_symbol} {condition_text} ${target_price:,.2f}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #1e1e2e; color: #cdd6f4; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #313244; border-radius: 15px; padding: 30px; }}
            .header {{ text-align: center; padding-bottom: 20px; border-bottom: 2px solid #45475a; }}
            .header h1 {{ color: #89b4fa; margin: 0; }}
            .content {{ padding: 30px 0; }}
            .alert-box {{ background: #1e1e2e; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #f9e2af; }}
            .price {{ font-size: 2em; color: #a6e3a1; font-weight: bold; }}
            .label {{ color: #a6adc8; font-size: 0.9em; text-transform: uppercase; letter-spacing: 1px; }}
            .footer {{ text-align: center; color: #6c7086; font-size: 0.85em; padding-top: 20px; border-top: 1px solid #45475a; }}
            .btn {{ display: inline-block; background: #89b4fa; color: #1e1e2e; padding: 12px 25px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ CryptoGuard</h1>
                <p style="color: #a6adc8; margin: 5px 0;">Alerte crypto déclenchée</p>
            </div>
            
            <div class="content">
                <p>Bonjour <strong>{username}</strong>,</p>
                
                <p>Votre alerte a été déclenchée :</p>
                
                <div class="alert-box">
                    <div class="label">Cryptomonnaie</div>
                    <div style="font-size: 1.5em; margin: 5px 0;">{emoji} <strong>{crypto_symbol}</strong></div>
                    
                    <div class="label" style="margin-top: 15px;">Prix actuel</div>
                    <div class="price">${current_price:,.2f}</div>
                    
                    <div class="label" style="margin-top: 15px;">Condition</div>
                    <div style="font-size: 1.1em;">{crypto_symbol} {condition_text} <strong>${target_price:,.2f}</strong></div>
                </div>
                
                <center>
                    <a href="http://localhost:5000" class="btn">Voir sur CryptoGuard</a>
                </center>
            </div>
            
            <div class="footer">
                <p>⚠️ Ceci n'est PAS un conseil financier.</p>
                <p>Les cryptomonnaies sont très volatiles. Investissez prudemment.</p>
                <p style="margin-top: 15px;">© {datetime.now().year} CryptoGuard</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        email = resend.Emails.send(params)
        return {"success": True, "id": email.get("id")}
    except Exception as e:
        return {"success": False, "error": str(e)}


# اختبار
if __name__ == "__main__":
    print("Test Email Alert...")
    result = send_alert_email(
        to_email="hamdimziou377@gmail.com",
        username="Hamdi",
        crypto_symbol="BTC",
        current_price=83000,
        condition="above",
        target_price=80000
    )
    print("Result:", result)