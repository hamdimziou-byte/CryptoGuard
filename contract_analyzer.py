"""
CryptoGuard - Smart Contract Analyzer
تحليل العقود الذكية باستخدام Gemini REST API
"""

import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Endpoint الرسمي
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"


SYSTEM_PROMPT = """أنت خبير في تحليل العقود الذكية (Smart Contracts).

مهمتك: تحليل صورة عقد ذكي واكتشاف:
1. 🚨 علامات الخطر (Rug Pull, Honeypot, Backdoor)
2. ⚠️ المخاطر الأمنية
3. 📊 صلاحيات المطوّر
4. 💰 وظائف التحويل (Transfer, Mint, Burn)

قدّم التحليل بهذا الشكل:

🚨 **المخاطر المكتشفة**:
- [قائمة]

⚠️ **علامات الخطر الحمراء**:
- [قائمة]

✅ **نقاط إيجابية**:
- [قائمة]

💡 **التوصية النهائية**:
- [نصيحة]

⚠️ **تنبيه**: تحليل تقني فقط وليس نصيحة استثمارية!

جاوب بنفس لغة السؤال.
"""


def analyze_contract_image(image_bytes, mime_type="image/png", lang="fr"):
    """تحليل صورة عقد ذكي عبر Gemini REST API"""

    if not GEMINI_API_KEY:
        return {"success": False, "error": "GEMINI_API_KEY manquant dans .env"}

    try:
        prompts = {
            "fr": "Analyse cette image d'un smart contract Solidity. Cherche les risques et scams.",
            "en": "Analyze this Solidity smart contract image. Look for risks and scams.",
            "ar": "حلّل هذي الصورة لعقد ذكي Solidity. ابحث على المخاطر."
        }
        user_prompt = prompts.get(lang, prompts["fr"])

        # Encode image
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Payload
        payload = {
            "contents": [{
                "parts": [
                    {"text": SYSTEM_PROMPT + "\n\n" + user_prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1500
            }
        }

        # Headers - المفتاح في الـheader
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": GEMINI_API_KEY
        }

        # Request
        response = requests.post(GEMINI_URL, json=payload, headers=headers, timeout=60)

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:300]}"
            }

        data = response.json()

        # Extract text
        try:
            analysis = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return {"success": False, "error": f"Réponse invalide: {str(data)[:300]}"}

        return {"success": True, "analysis": analysis}

    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("Test Contract Analyzer (Gemini REST API)")
    print("=" * 50)

    test_image = "test_contract.png"
    if os.path.exists(test_image):
        with open(test_image, "rb") as f:
            result = analyze_contract_image(f.read(), "image/png", "fr")

        if result["success"]:
            print("✅ Analyse:")
            print(result["analysis"])
        else:
            print(f"❌ Erreur: {result['error']}")
    else:
        print(f"⚠️ Image '{test_image}' introuvable")