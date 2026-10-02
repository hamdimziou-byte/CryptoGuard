"""
CryptoGuard - AI Chat
Chat powered by Groq (Llama 3.3 70B)
"""

import os
from groq import Groq
from dotenv import load_dotenv

# تحميل .env
load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# نموذج Llama 3.3 70B (قوي + سريع)
MODEL = "openai/gpt-oss-120b"

# System prompt
SYSTEM_PROMPT = """أنت CryptoGuard AI، مساعد خبير في العملات الرقمية.

⚠️ القاعدة الأهم:
**جاوب دايماً بنفس اللغة اللي كتب بيها المستخدم**

- إذا كتب بالدارجة التونسية 🇹🇳 → جاوب بالدارجة التونسية
- إذا كتب بالعربية الفصحى → جاوب بالعربية الفصحى
- إذا كتب بالفرنسية 🇫🇷 → جاوب بالفرنسية
- إذا كتب بالإنجليزية 🇬🇧 → جاوب بالإنجليزية
- إذا كتب بأي لغة أخرى → جاوب بنفس اللغة

أمثلة على الدارجة التونسية (كي تكتب بيهم):
- "شنوّة" = ما هو
- "برشة" = كثير
- "خلي نحكيلك" = دعني أخبرك
- "تنجم" = يمكنك
- "علاش" = لماذا
- "كيما" = مثل
- "توا" = الآن
- "باهي" = جيد
- "ماشي" = ليس
- "ياخي" = هل

قواعد أخرى:
1. كون CONCIS (200 كلمة كحد أقصى)
2. اعتمد على البيانات اللي نعطيهالك
3. إذا حكيت على استثمار، **ذكّر دايماً بالمخاطر**
4. **ما تعطيش** نصايح مالية دقيقة
5. استعمل emojis باش تكون واضح
6. إذا ما تعرفش، قول "ما نعرفش"
7. استعمل كلمات تقنية بالإنجليزية كي ما فماش ترجمة (Bitcoin, Blockchain, Wallet...)
"""

def chat(user_message, crypto_context=None):
    """
    Chat avec AI
    
    Args:
        user_message (str): Question de l'utilisateur
        crypto_context (dict): Donnees des cryptos (optionnel)
    
    Returns:
        str: Reponse AI
    """
    if not client:
        return "Erreur: GROQ_API_KEY manquant dans .env"
    
    # Construire le contexte
    context = ""
    if crypto_context:
        context = "\n\nDonnees actuelles du marche:\n"
        for coin in crypto_context[:10]:
            context += "- " + coin.get('symbol', '').upper() + " (" + coin.get('name', '') + "): "
            context += "$" + f"{coin.get('current_price', 0):,.2f} "
            change = coin.get('price_change_percentage_24h', 0) or 0
            context += "(" + f"{change:+.2f}" + "% 24h)\n"
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT + context},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Erreur AI: " + str(e)


# Test
if __name__ == "__main__":
    print("Test AI Chat:\n")
    print("Q: Qu'est-ce que Bitcoin?")
    print("A:", chat("Qu'est-ce que Bitcoin?"))
    print("\n" + "=" * 60)
    print("Q: Analyse BTC")
    btc_data = [{"symbol": "btc", "name": "Bitcoin", "current_price": 83655, "price_change_percentage_24h": -1.20}]
    print("A:", chat("Analyse BTC", btc_data))