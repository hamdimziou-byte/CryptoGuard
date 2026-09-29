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
SYSTEM_PROMPT = """Tu es CryptoGuard AI, un assistant expert en cryptomonnaies.

Tes regles:
1. Reponds en francais (ou en arabe si l'utilisateur ecrit en arabe)
2. Sois CONCIS (max 200 mots)
3. Base tes reponses sur les donnees fournies
4. Si tu parles d'investissement, rappelle TOUJOURS les risques
5. Ne donne JAMAIS de conseils financiers precis
6. Utilise des emojis pour etre plus clair
7. Si tu ne sais pas, dis-le

Format de reponse:
- Court
- Precis
- Base sur les donnees
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